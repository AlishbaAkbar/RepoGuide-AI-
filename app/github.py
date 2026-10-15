import base64
import re
from urllib.parse import urlparse

import requests


API_ROOT = "https://api.github.com"
REQUEST_TIMEOUT = (3.05, 10)
USER_AGENT = "RepoGuide-AI/1.0"


class GitHubFetchError(Exception):
    pass


def _parse_github_path(url: str, *, issue: bool) -> tuple[str, str, int | None]:
    try:
        parsed = urlparse(url.strip())
    except ValueError as exc:
        raise GitHubFetchError("Enter a valid public GitHub URL.") from exc
    if parsed.scheme not in ("http", "https") or parsed.netloc.lower() not in (
        "github.com", "www.github.com",
    ):
        raise GitHubFetchError("Only public github.com repository or issue URLs are supported.")
    parts = [part for part in parsed.path.split("/") if part]
    if issue:
        if len(parts) != 4 or parts[2] != "issues" or not parts[3].isdigit():
            raise GitHubFetchError("Issue URL must look like https://github.com/owner/repo/issues/123.")
        owner, repo, number = parts[0], parts[1], int(parts[3])
    else:
        if len(parts) != 2:
            raise GitHubFetchError("Repository URL must look like https://github.com/owner/repo.")
        owner, repo, number = parts[0], parts[1], None
    repo = re.sub(r"\.git$", "", repo)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", repo
    ):
        raise GitHubFetchError("The GitHub URL contains an invalid owner or repository name.")
    return owner, repo, number


def parse_input(issue_url: str | None, repo_url: str | None) -> tuple[str, str, int | None]:
    if issue_url:
        return _parse_github_path(issue_url, issue=True)
    if repo_url:
        return _parse_github_path(repo_url, issue=False)
    raise GitHubFetchError("Provide a GitHub issue URL or repository URL.")


def _get_json(url: str, *, missing_ok: bool = False):
    try:
        response = requests.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": USER_AGENT,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.Timeout as exc:
        raise GitHubFetchError("GitHub request timed out. Please retry.") from exc
    except requests.RequestException as exc:
        raise GitHubFetchError("Could not connect to GitHub. Check your connection and retry.") from exc
    if response.status_code == 404 and missing_ok:
        return None
    if response.status_code == 429 or (
        response.status_code == 403
        and response.headers.get("X-RateLimit-Remaining") == "0"
    ):
        raise GitHubFetchError("GitHub API rate limit reached. Wait and retry, or use offline demo.")
    if response.status_code == 404:
        raise GitHubFetchError("GitHub could not find that public repository or issue.")
    if response.status_code >= 400:
        raise GitHubFetchError(f"GitHub returned HTTP {response.status_code}. Please retry.")
    try:
        return response.json()
    except requests.JSONDecodeError as exc:
        raise GitHubFetchError("GitHub returned an unreadable response.") from exc


def fetch_repository_data(
    owner: str,
    repo: str,
    issue_number: int | None,
    supplied_title: str = "",
    supplied_body: str = "",
) -> dict:
    base = f"{API_ROOT}/repos/{owner}/{repo}"
    metadata = _get_json(base)
    warnings = []

    if issue_number is not None:
        issue = _get_json(f"{base}/issues/{issue_number}")
        title = issue.get("title") or ""
        body = issue.get("body") or ""
        issue_source_url = issue.get("html_url")
    else:
        title = supplied_title.strip()
        body = supplied_body.strip()
        issue_source_url = None

    try:
        readme_response = _get_json(f"{base}/readme", missing_ok=True)
        if readme_response is None:
            readme = ""
            readme_path = None
            warnings.append("The repository has no README available through the GitHub API.")
        else:
            encoded = readme_response.get("content", "")
            if readme_response.get("encoding") not in (None, "base64"):
                raise GitHubFetchError("GitHub returned README content in an unsupported encoding.")
            readme = base64.b64decode(encoded).decode("utf-8", errors="replace")
            readme_path = readme_response.get("path")
    except GitHubFetchError as exc:
        readme = ""
        readme_path = None
        warnings.append(f"README could not be retrieved: {exc}")

    try:
        tree_response = _get_json(
            f"{base}/git/trees/{metadata.get('default_branch') or 'HEAD'}?recursive=1",
            missing_ok=True,
        )
        if tree_response is None:
            file_paths = []
            warnings.append("The repository file tree is not available.")
        else:
            file_paths = [
                item["path"] for item in tree_response.get("tree", [])
                if item.get("type") == "blob" and isinstance(item.get("path"), str)
            ]
            if tree_response.get("truncated"):
                warnings.append("GitHub truncated the recursive tree; some files may be missing.")
    except GitHubFetchError as exc:
        file_paths = []
        warnings.append(f"File tree could not be retrieved: {exc}")

    repository = {
        "full_name": metadata.get("full_name") or f"{owner}/{repo}",
        "description": metadata.get("description") or "",
        "default_branch": metadata.get("default_branch") or "HEAD",
        "html_url": metadata.get("html_url") or f"https://github.com/{owner}/{repo}",
    }
    return {
        "repository": repository,
        "issue_title": title,
        "issue_body": body,
        "issue_url": issue_source_url,
        "readme": readme,
        "readme_path": readme_path,
        "file_paths": file_paths,
        "warnings": warnings,
    }
