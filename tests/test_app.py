import asyncio
import base64
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import github, main


def api_request(path, *, method="POST", body=b"", content_type="application/json"):
    async def run_request():
        messages = []
        received = False

        async def receive():
            nonlocal received
            if received:
                return {"type": "http.disconnect"}
            received = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [
                (b"host", b"testserver"),
                (b"content-type", content_type.encode()),
            ],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        await main.app(scope, receive, send)
        start = next(message for message in messages if message["type"] == "http.response.start")
        response_body = b"".join(
            message.get("body", b"")
            for message in messages
            if message["type"] == "http.response.body"
        )
        return start["status"], response_body

    return asyncio.run(run_request())


def test_offline_demo_returns_grounded_report_without_external_services(monkeypatch):
    def no_external_service(*args, **kwargs):
        raise AssertionError("offline demo unexpectedly attempted an external request")

    monkeypatch.setattr(main.requests, "get", no_external_service)
    monkeypatch.setattr(main.requests, "post", no_external_service)
    report = main.analyze(main.AnalyzeRequest(mode="demo", use_ai=False))

    assert report["mode"] == "offline-demo"
    assert "synthetic bundled demo" in report["limitations"][0].lower()
    assert any(file["path"] == "src/cli.py" for file in report["relevant_files"])
    assert all(file["source_url"].startswith("/api/demo/evidence?path=") for file in report["relevant_files"])
    assert report["ai"]["provider"] == "deterministic"


def test_offline_demo_api_accepts_a_json_body_without_external_services(monkeypatch):
    def no_external_service(*args, **kwargs):
        raise AssertionError("offline demo unexpectedly attempted an external request")

    monkeypatch.setattr(main.requests, "get", no_external_service)
    monkeypatch.setattr(main.requests, "post", no_external_service)
    status, body = api_request(
        "/api/analyze",
        body=json.dumps({"mode": "demo", "use_ai": False}).encode(),
    )

    assert status == 200
    assert json.loads(body)["mode"] == "offline-demo"


def test_live_request_schema_accepts_each_supported_source():
    demo = main.AnalyzeRequest(mode="demo", use_ai=False)
    issue = main.AnalyzeRequest(
        mode="live",
        issue_url=" https://github.com/octo/project/issues/7 ",
        use_ai=False,
    )
    repository = main.AnalyzeRequest(
        mode="live",
        repo_url=" https://github.com/octo/project ",
        issue_title="  Improve widget  ",
        issue_body="  Add a test.  ",
        use_ai=False,
    )

    assert demo.mode == "demo"
    assert issue.issue_url == "https://github.com/octo/project/issues/7"
    assert issue.issue_title == ""
    assert repository.repo_url == "https://github.com/octo/project"
    assert repository.issue_title == "Improve widget"
    assert repository.issue_body == "Add a test."


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        ({"mode": "live"}, "provide issue_url or repo_url"),
        (
            {
                "mode": "live",
                "issue_url": "https://github.com/octo/project/issues/7",
                "repo_url": "https://github.com/octo/project",
            },
            "issue_url or repo_url, not both",
        ),
        (
            {"mode": "live", "repo_url": "https://github.com/octo/project"},
            "issue_title is required",
        ),
    ],
)
def test_missing_or_conflicting_live_fields_return_actionable_422(payload, expected_message):
    status, body = api_request("/api/analyze", body=json.dumps(payload).encode())
    response = json.loads(body)

    assert status == 422
    assert expected_message in " ".join(error["msg"] for error in response["detail"])


def test_empty_and_malformed_request_bodies_return_fastapi_validation_errors():
    empty_status, empty_body = api_request("/api/analyze")
    invalid_status, invalid_body = api_request("/api/analyze", body=b'{"mode":')

    assert empty_status == 422
    assert json.loads(empty_body)["detail"][0]["type"] == "missing"
    assert invalid_status == 422
    assert json.loads(invalid_body)["detail"][0]["type"] == "json_invalid"


def test_wrong_field_type_is_rejected_by_request_schema():
    with pytest.raises(ValidationError):
        main.AnalyzeRequest(mode="demo", use_ai="not-a-boolean")


def test_issue_url_and_repository_url_workflows_through_api(monkeypatch):
    main._cache.clear()

    class FakeResponse:
        status_code = 200
        headers = {}

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def fake_get(url, **kwargs):
        if url.endswith("/repos/octo/project"):
            return FakeResponse({
                "full_name": "octo/project",
                "description": "Test repository",
                "default_branch": "main",
                "html_url": "https://github.com/octo/project",
            })
        if url.endswith("/issues/7"):
            return FakeResponse({
                "title": "Fix widget output",
                "body": "The widget output should be consistent.",
                "html_url": "https://github.com/octo/project/issues/7",
            })
        if url.endswith("/readme"):
            return FakeResponse({
                "content": base64.b64encode(b"# Project README").decode(),
                "path": "README.md",
                "encoding": "base64",
            })
        if "/git/trees/" in url:
            return FakeResponse({"tree": [
                {"path": "src/widget.py", "type": "blob"},
                {"path": "tests/test_widget.py", "type": "blob"},
            ]})
        raise AssertionError(f"Unexpected GitHub request: {url}")

    monkeypatch.setattr(github.requests, "get", fake_get)
    issue_status, issue_body = api_request(
        "/api/analyze",
        body=json.dumps({
            "mode": "live",
            "issue_url": "https://github.com/octo/project/issues/7",
            "use_ai": False,
        }).encode(),
    )
    repo_status, repo_body = api_request(
        "/api/analyze",
        body=json.dumps({
            "mode": "live",
            "repo_url": "https://github.com/octo/project",
            "issue_title": "Fix widget output",
            "issue_body": "The widget output should be consistent.",
            "use_ai": False,
        }).encode(),
    )

    issue_report = json.loads(issue_body)
    repo_report = json.loads(repo_body)
    assert issue_status == repo_status == 200
    assert issue_report["issue"]["source_url"].endswith("/issues/7")
    assert issue_report["issue"]["title"] == "Fix widget output"
    assert repo_report["issue"]["source_label"] == "User-provided issue details"
    assert repo_report["issue"]["title"] == "Fix widget output"
    assert all("source_url" in item for item in repo_report["relevant_files"])
    main._cache.clear()


@pytest.mark.parametrize(
    ("status_code", "headers"),
    [(403, {"X-RateLimit-Remaining": "0"}), (429, {})],
)
def test_github_rate_limits_return_clear_api_error(monkeypatch, status_code, headers):
    class FakeResponse:
        def __init__(self):
            self.status_code = status_code
            self.headers = headers

    monkeypatch.setattr(github.requests, "get", lambda *args, **kwargs: FakeResponse())
    status, body = api_request(
        "/api/analyze",
        body=json.dumps({
            "mode": "live",
            "repo_url": "https://github.com/octo/project",
            "issue_title": "Improve widget",
            "use_ai": False,
        }).encode(),
    )

    assert status == 502
    assert "rate limit" in json.loads(body)["detail"].lower()


def test_github_network_failure_returns_clear_api_error(monkeypatch):
    def connection_failed(*args, **kwargs):
        raise github.requests.ConnectionError("connection refused")

    monkeypatch.setattr(github.requests, "get", connection_failed)
    status, body = api_request(
        "/api/analyze",
        body=json.dumps({
            "mode": "live",
            "repo_url": "https://github.com/octo/project",
            "issue_title": "Improve widget",
            "use_ai": False,
        }).encode(),
    )

    assert status == 502
    assert "connect to github" in json.loads(body)["detail"].lower()


def test_demo_evidence_endpoint_serves_only_bundled_paths():
    response = main.demo_evidence("src/cli.py")
    assert 'def greet(name="world")' in response.body.decode()
    with pytest.raises(HTTPException) as error:
        main.demo_evidence("missing.py")
    assert error.value.status_code == 404


def test_invalid_live_source_is_reported():
    with pytest.raises(HTTPException) as error:
        main.analyze(main.AnalyzeRequest(
            mode="live",
            issue_url="https://example.com/owner/repo/issues/1",
            use_ai=False,
        ))
    assert error.value.status_code == 422
    assert "github.com" in error.value.detail


def test_github_timeout_is_returned_as_actionable_error(monkeypatch):
    def timed_out(*args, **kwargs):
        raise github.requests.Timeout("network stalled")

    monkeypatch.setattr(github.requests, "get", timed_out)
    with pytest.raises(HTTPException) as error:
        main.analyze(main.AnalyzeRequest(
            mode="live",
            repo_url="https://github.com/octo/project",
            issue_title="Improve widget",
            use_ai=False,
        ))
    assert error.value.status_code == 502
    assert "timed out" in error.value.detail.lower()


def test_live_repo_analysis_uses_real_paths_and_then_cache(monkeypatch):
    main._cache.clear()
    calls = []

    class FakeResponse:
        def __init__(self, status_code, payload, headers=None):
            self.status_code = status_code
            self._payload = payload
            self.headers = headers or {}

        def json(self):
            return self._payload

    def fake_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/repos/octo/project"):
            return FakeResponse(200, {
                "full_name": "octo/project",
                "description": "Demo for tests",
                "default_branch": "main",
                "html_url": "https://github.com/octo/project",
            })
        if url.endswith("/readme"):
            return FakeResponse(200, {
                "content": base64.b64encode(b"# Project README").decode(),
                "path": "docs/README project.md",
                "encoding": "base64",
            })
        if "/git/trees/" in url:
            return FakeResponse(200, {"tree": [
                {"path": "src/handler.py", "type": "blob"},
                {"path": "tests/test_handler.py", "type": "blob"},
                {"path": "src/other.py", "type": "blob"},
            ]})
        raise AssertionError(f"Unexpected GitHub request: {url}")

    monkeypatch.setattr(github.requests, "get", fake_get)
    payload = {
        "mode": "live",
        "repo_url": "https://github.com/octo/project",
        "issue_title": "Update handler response",
        "issue_body": "The handler response should include a status.",
        "use_ai": False,
    }
    first_report = main.analyze(main.AnalyzeRequest(**payload))
    assert first_report["mode"] == "live"
    assert "src/handler.py" in [item["path"] for item in first_report["relevant_files"]]
    assert first_report["readme_excerpt"] == "# Project README"
    assert first_report["readme_path"] == "docs/README project.md"
    assert first_report["readme_source_url"].endswith("docs/README%20project.md")
    assert first_report["suggested_tests"][0]["source_paths"] == ["tests/test_handler.py"]
    call_count = len(calls)

    second_report = main.analyze(main.AnalyzeRequest(**payload))
    assert second_report["mode"] == "cached"
    assert len(calls) == call_count
    main._cache.clear()


def test_ollama_does_not_download_a_missing_model(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"models": [{"name": "another-model"}]}

    def unexpected_generate(*args, **kwargs):
        raise AssertionError("Ollama generation would pull the missing model")

    monkeypatch.setattr(main.requests, "get", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(main.requests, "post", unexpected_generate)
    provider, status, summary = main._summarize_with_ollama("Issue title", "Issue body")

    assert provider == "deterministic"
    assert "no model was downloaded" in status
    assert "Issue title" in summary


def test_issue_url_fetches_issue_and_handles_ollama_failure(monkeypatch):
    main._cache.clear()

    class FakeResponse:
        status_code = 200
        headers = {}

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def fake_get(url, **kwargs):
        if url == main.OLLAMA_TAGS_URL:
            return FakeResponse({"models": [{"name": main.OLLAMA_MODEL}]})
        if url.endswith("/repos/octo/project"):
            return FakeResponse({
                "full_name": "octo/project",
                "description": "",
                "default_branch": "main",
                "html_url": "https://github.com/octo/project",
            })
        if url.endswith("/issues/7"):
            return FakeResponse({
                "title": "Fix widget",
                "body": "The widget output is wrong.",
                "html_url": "https://github.com/octo/project/issues/7",
            })
        if url.endswith("/readme"):
            return FakeResponse(None)
        if "/git/trees/" in url:
            return FakeResponse({"tree": []})
        raise AssertionError(f"Unexpected GitHub request: {url}")

    def failed_ollama(*args, **kwargs):
        raise main.requests.ConnectionError("Ollama is not running")

    monkeypatch.setattr(github.requests, "get", fake_get)
    monkeypatch.setattr(main.requests, "post", failed_ollama)
    report = main.analyze(main.AnalyzeRequest(
        mode="live",
        issue_url="https://github.com/octo/project/issues/7",
        use_ai=True,
    ))
    assert report["issue"]["title"] == "Fix widget"
    assert report["issue"]["source_url"] == "https://github.com/octo/project/issues/7"
    assert report["ai"]["provider"] == "deterministic"
    assert "Ollama unavailable" in report["ai"]["status"]
    assert report["warnings"]
    main._cache.clear()
