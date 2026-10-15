# RepoGuide AI

A small, evidence-grounded guide for first-time contributors. It fetches public GitHub repository information when requested, matches issue terms against real repository paths, and turns the results into a readiness report. It works without GitHub credentials, an AI API key, or a database.

## Run on Windows Command Prompt

From Command Prompt, activate the existing virtual environment and verify its app packages:

```cmd
cd /d "C:\Users\Hp\Desktop\RepoGuide-AI"
call .venv\Scripts\activate.bat
python -c "import fastapi, requests, uvicorn"
```

If that import check reports a missing package, install the project's requirements into the activated environment:

```cmd
python -m pip install -r requirements.txt
```

Start the server, then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser:

```cmd
python -m uvicorn app.main:app --reload
```

Run the automated tests in a second Command Prompt window, activating `.venv` there as well:

```cmd
cd /d "C:\Users\Hp\Desktop\RepoGuide-AI"
call .venv\Scripts\activate.bat
python -m pytest -q
```

## Modes and evidence

- **Offline demo** uses a bundled, explicitly fictional example. It needs no internet or Ollama; its cited file content is served locally from the fixture.
- **Live GitHub** accepts a public issue URL, or a repository URL with a title and issue details. The app fetches repository metadata, README, issue details (for issue URLs), and the recursive file tree from GitHub's public API. GitHub's unauthenticated rate limit applies.
- **Cached snapshot** is shown when the same live request can use the process-local 15-minute cache, including as a stale fallback after a refresh error. Cache entries disappear when the server restarts.

The report keeps issue text separate from repository evidence, links relevant paths to their source, lists missing issue details, proposes next steps and test ideas, and explicitly notes limitations. Suggested tests are not run by RepoGuide. File relevance is keyword overlap, not code understanding; no code is downloaded or executed.

## Optional local AI

If enabled in the form, the app checks the local Ollama model list and, only when `qwen2.5:1.5b` is already installed, asks it to summarize the issue. Only the issue title and description are sent to the local service. Evidence matching and all other report sections remain deterministic. An installed model gets up to 60 seconds for a cold CPU start; if Ollama is stopped, times out, or returns unusable output, the report uses a deterministic summary and says so. A missing model is never downloaded.

## API

- `GET /api/health`
- `POST /api/analyze` with `{"mode":"demo","use_ai":false}`, or `{"mode":"live","issue_url":"https://github.com/owner/repo/issues/123","use_ai":false}`
- Demo evidence is available under `GET /api/demo/evidence?path=...`.

These single-line examples work in Windows Command Prompt. The quotes and `-d` are required; without `-d`, curl sends no JSON body and FastAPI returns a 422 missing-body error:

```cmd
curl.exe -i -X POST "http://127.0.0.1:8000/api/analyze" -H "Content-Type: application/json" -d "{\"mode\":\"demo\",\"use_ai\":false}"
curl.exe -i -X POST "http://127.0.0.1:8000/api/analyze" -H "Content-Type: application/json" -d "{\"mode\":\"live\",\"issue_url\":\"https://github.com/psf/requests/issues/7634\",\"use_ai\":false}"
curl.exe -i -X POST "http://127.0.0.1:8000/api/analyze" -H "Content-Type: application/json" -d "{\"mode\":\"live\",\"repo_url\":\"https://github.com/psf/requests\",\"issue_title\":\"Improve timeout guidance\",\"issue_body\":\"Clarify timeout behavior and add a test.\",\"use_ai\":false}"
```

The issue-URL workflow needs only `issue_url`; the repository workflow requires `repo_url` and `issue_title`, while `issue_body` may be blank. Do not send both URL fields. `use_ai` is optional and defaults to `true`.
