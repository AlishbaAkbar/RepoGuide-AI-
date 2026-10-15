import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.analysis import analyze_issue, deterministic_summary
from app.github import GitHubFetchError, fetch_repository_data, parse_input


ROOT = Path(__file__).resolve().parent
DEMO_PATH = ROOT / "data" / "demo.json"
STATIC_PATH = ROOT / "static"
CACHE_TTL_SECONDS = 15 * 60
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_MODEL = "qwen2.5:1.5b"

app = FastAPI(title="RepoGuide AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = threading.Lock()


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["demo", "live"] = "demo"
    issue_url: str | None = None
    repo_url: str | None = None
    issue_title: str = ""
    issue_body: str = ""
    use_ai: bool = True

    @field_validator("issue_url", "repo_url", mode="before")
    @classmethod
    def normalize_optional_url(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("issue_title", "issue_body", mode="before")
    @classmethod
    def normalize_issue_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_source(self):
        if self.mode == "live":
            if self.issue_url and self.repo_url:
                raise ValueError("Provide issue_url or repo_url, not both.")
            if not self.issue_url and not self.repo_url:
                raise ValueError("For live analysis, provide issue_url or repo_url.")
            if self.repo_url and not self.issue_title.strip():
                raise ValueError("issue_title is required when repo_url is provided.")
        return self


def _load_demo() -> dict:
    return json.loads(DEMO_PATH.read_text(encoding="utf-8"))


def _cache_key(owner: str, repo: str, issue_number: int | None, title: str, body: str) -> str:
    identity = f"{owner.lower()}/{repo.lower()}#{issue_number or 'manual'}"
    if issue_number is None:
        identity += ":" + hashlib.sha256(f"{title}\n{body}".encode()).hexdigest()
    return identity


def _cached(key: str, *, allow_stale: bool = False):
    with _cache_lock:
        entry = _cache.get(key)
    if entry is None:
        return None
    created, data = entry
    if not allow_stale and time.monotonic() - created > CACHE_TTL_SECONDS:
        return None
    return data


def _save_cache(key: str, data: dict) -> None:
    with _cache_lock:
        _cache[key] = (time.monotonic(), data)


def _summarize_with_ollama(title: str, body: str) -> tuple[str, str, str]:
    fallback = deterministic_summary(title, body)
    prompt = (
        "Summarize this GitHub issue in at most two sentences. Use only the issue text. "
        "Do not invent repository files, tests, requirements, or facts. "
        "Return only the summary.\n\n"
        f"Title: {title}\nDescription: {body[:4000]}"
    )
    try:
        installed_response = requests.get(OLLAMA_TAGS_URL, timeout=(2, 4))
        installed_response.raise_for_status()
        installed_models = installed_response.json().get("models", [])
        if not any(
            model.get("name") == OLLAMA_MODEL or model.get("model") == OLLAMA_MODEL
            for model in installed_models
            if isinstance(model, dict)
        ):
            return (
                "deterministic",
                f"{OLLAMA_MODEL} is not installed; deterministic summary used (no model was downloaded).",
                fallback,
            )
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 120},
            },
            timeout=(2, 60),
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        if not text:
            return "deterministic", "Ollama returned an empty summary; deterministic summary used.", fallback
        return "ollama-qwen2.5:1.5b", "summary generated locally by Ollama.", text
    except (requests.RequestException, requests.JSONDecodeError, AttributeError, TypeError) as exc:
        reason = str(exc).splitlines()[0][:160] or "local inference failed"
        return "deterministic", f"Local Ollama unavailable; deterministic summary used ({reason}).", fallback


def _apply_ai(report: dict, use_ai: bool) -> dict:
    if not use_ai:
        return report
    provider, status, summary = _summarize_with_ollama(
        report["issue"]["title"],
        report["issue"]["body"],
    )
    report["ai"] = {"provider": provider, "status": status, "summary": summary}
    return report


@app.get("/")
def index():
    return FileResponse(STATIC_PATH / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_optional": True}


@app.get("/api/demo/evidence")
def demo_evidence(path: str):
    files = _load_demo().get("files", {})
    content = files.get(path)
    if content is None:
        raise HTTPException(status_code=404, detail="No bundled demo evidence exists for that path.")
    return PlainTextResponse(content)


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    if request.mode == "demo":
        demo = _load_demo()
        report = analyze_issue(
            title=demo["issue"]["title"],
            body=demo["issue"]["body"],
            repository=demo["repository"],
            readme=demo["readme"],
            file_paths=demo["file_paths"],
            issue_url=None,
            repo_url=demo["repository"]["html_url"],
            source_mode="offline-demo",
        )
        report["issue"]["source_label"] = "Bundled synthetic demo issue"
        report["repository_source_url"] = None
        report["readme_source_url"] = "/api/demo/evidence?path=README.md"
        report["readme_path"] = "README.md"
        report["file_tree_count"] = len(demo["file_paths"])
        return _apply_ai(report, request.use_ai)

    try:
        owner, repo, issue_number = parse_input(request.issue_url, request.repo_url)
    except GitHubFetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    key = _cache_key(owner, repo, issue_number, request.issue_title, request.issue_body)
    cached = _cached(key)
    if cached is not None:
        data = cached
        mode = "cached"
        warnings = ["Using a recent in-memory snapshot; GitHub was not contacted for this request."]
    else:
        try:
            data = fetch_repository_data(
                owner,
                repo,
                issue_number,
                request.issue_title,
                request.issue_body,
            )
            _save_cache(key, data)
            mode = "live"
            warnings = data["warnings"]
        except GitHubFetchError as exc:
            stale_data = _cached(key, allow_stale=True)
            if stale_data is None:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            data = stale_data
            mode = "cached"
            warnings = [f"GitHub refresh failed; showing the saved snapshot. {exc}"]

    repo_source = data["repository"]["html_url"]
    issue_source = data["issue_url"] or request.issue_url
    report = analyze_issue(
        title=data["issue_title"],
        body=data["issue_body"],
        repository=data["repository"],
        readme=data["readme"],
        file_paths=data["file_paths"],
        issue_url=issue_source,
        repo_url=repo_source,
        source_mode=mode,
        warnings=warnings,
    )
    report["issue"]["source_label"] = (
        "GitHub issue" if issue_source else "User-provided issue details"
    )
    report["readme_source_url"] = (
        f"{repo_source}/blob/{quote(data['repository']['default_branch'], safe='/')}/"
        f"{quote(data['readme_path'], safe='/')}"
        if data["readme"] and data.get("readme_path") else None
    )
    report["readme_path"] = data.get("readme_path")
    report["file_tree_count"] = len(data["file_paths"])
    return _apply_ai(report, request.use_ai)
