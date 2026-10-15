import re
from urllib.parse import quote


STOP_WORDS = {
    "about", "after", "again", "also", "and", "are", "because", "been",
    "before", "being", "below", "could", "does", "each", "from", "have",
    "into", "issue", "more", "most", "other", "please", "should", "that",
    "their", "there", "these", "they", "this", "those", "through", "when",
    "where", "which", "while", "with", "would", "your",
}


def _tokens(text: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 2 and word not in STOP_WORDS
    }


def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def _file_source_url(path: str, repository: dict, repo_url: str, source_mode: str) -> str:
    if source_mode == "offline-demo":
        return f"/api/demo/evidence?path={quote(path, safe='')}"
    branch = quote(repository.get("default_branch") or "HEAD", safe="/")
    return f"{repo_url.rstrip('/')}/blob/{branch}/{quote(path, safe='/')}"


def deterministic_summary(title: str, body: str) -> str:
    detail = re.sub(r"\s+", " ", body).strip()
    if len(detail) > 240:
        detail = detail[:237].rsplit(" ", 1)[0] + "..."
    if detail:
        return f"{title.strip() or 'Issue'}: {detail}"
    return title.strip() or "No issue title or description was provided."


def analyze_issue(
    *,
    title: str,
    body: str,
    repository: dict,
    readme: str,
    file_paths: list[str],
    issue_url: str | None,
    repo_url: str,
    source_mode: str,
    warnings: list[str] | None = None,
) -> dict:
    issue_text = f"{title}\n{body}"
    issue_tokens = _tokens(issue_text)
    candidates = []
    for path in file_paths:
        path_tokens = _tokens(path.replace("/", " ").replace("_", " ").replace("-", " "))
        overlap = issue_tokens & path_tokens
        if overlap:
            candidates.append({
                "path": path,
                "matched_terms": sorted(overlap),
                "score": len(overlap),
            })
    candidates.sort(key=lambda item: (-item["score"], item["path"]))

    if not candidates:
        relevant_files = []
    else:
        relevant_files = [
            {
                **item,
                "reason": "Path terms overlap with the issue text: "
                + ", ".join(item["matched_terms"]),
                "source_url": _file_source_url(item["path"], repository, repo_url, source_mode),
            }
            for item in candidates[:8]
        ]

    lowered = issue_text.lower()
    missing_requirements = []
    if not body.strip():
        missing_requirements.append("The issue has no description; add context and expected behavior.")
    if not _has_any(lowered, (
        "acceptance criteria", "expected behavior", "expected result",
        "definition of done",
    )):
        missing_requirements.append(
            "No explicit expected outcome or acceptance criteria were found."
        )
    if not _has_any(lowered, (
        "steps to reproduce", "how to reproduce", "reproduction steps",
        "reproducible",
    )):
        missing_requirements.append(
            "No reproduction steps were found; clarify them if this is a bug report."
        )
    if not _has_any(lowered, ("test", "tests", "testing")):
        missing_requirements.append(
            "The issue does not mention tests or how the change should be verified."
        )
    if not relevant_files:
        missing_requirements.append(
            "No file paths matched issue terms; narrow the affected area before editing."
        )

    implementation_steps = []
    if relevant_files:
        paths = ", ".join(item["path"] for item in relevant_files[:3])
        implementation_steps.append(
            f"Inspect {paths} and verify which matched files own the reported behavior."
        )
    else:
        implementation_steps.append(
            "Search the repository for the issue's key terms to identify the owning code."
        )
    implementation_steps.extend([
        "Confirm the expected behavior and edge cases with the issue author before coding.",
        "Make the smallest change consistent with the surrounding implementation.",
        "Run the repository's relevant checks and report their actual results.",
    ])

    test_paths = [
        path for path in file_paths
        if re.search(r"(^|/)(tests?|spec)(/|$)", path.lower())
        or re.search(r"(^|/)(test_|.*_test\.|.*\.spec\.)", path.lower())
    ][:8]
    if test_paths:
        suggested_tests = [
            {
                "suggestion": "Inspect existing tests and extend the closest matching coverage.",
                "source_paths": test_paths,
                "source_urls": [
                    _file_source_url(path, repository, repo_url, source_mode)
                    for path in test_paths
                ],
            },
            {
                "suggestion": "Add a case that reproduces the reported behavior and verify the expected outcome.",
                "source_paths": test_paths[:3],
                "source_urls": [
                    _file_source_url(path, repository, repo_url, source_mode)
                    for path in test_paths[:3]
                ],
            },
        ]
    else:
        suggested_tests = [{
            "suggestion": (
                "Determine the project's test framework and convention before adding "
                "a regression test; no test location was confirmed in the available tree."
            ),
            "source_paths": [],
            "source_urls": [],
        }]

    unanswered_questions = []
    if not _has_any(lowered, ("expected behavior", "expected result", "should ")):
        unanswered_questions.append("What should happen instead, including any acceptance criteria?")
    if not _has_any(lowered, (
        "steps to reproduce", "how to reproduce", "reproduction steps",
        "reproducible",
    )):
        unanswered_questions.append("What exact steps reproduce the problem?")
    if not _has_any(lowered, ("version", "operating system", "platform", "environment")):
        unanswered_questions.append("Which versions, platform, or environment are affected?")
    if not _has_any(lowered, ("test", "tests", "testing")):
        unanswered_questions.append("What test or manual check would confirm the fix?")

    limitations = [
        "Path matching is a transparent keyword heuristic, not a code-level dependency analysis.",
        "Suggested steps and tests are not proof that a change is correct or that tests were run.",
    ]
    if source_mode == "offline-demo":
        limitations.insert(0, "This is synthetic bundled demo data, not a live GitHub repository.")
    if not readme:
        limitations.append("No README content was available to provide repository-level context.")

    return {
        "mode": source_mode,
        "repository": repository,
        "issue": {
            "title": title,
            "body": body,
            "source_url": issue_url,
        },
        "repository_source_url": repo_url,
        "readme_excerpt": readme[:1800],
        "relevant_files": relevant_files,
        "missing_requirements": missing_requirements,
        "implementation_steps": implementation_steps,
        "suggested_tests": suggested_tests,
        "unanswered_questions": unanswered_questions,
        "limitations": limitations,
        "warnings": warnings or [],
        "ai": {
            "provider": "deterministic",
            "status": "not requested",
            "summary": deterministic_summary(title, body),
        },
    }
