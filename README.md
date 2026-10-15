ReRepoGuide AI
Open source, one step at a time.
RepoGuide AI helps developers turn an unfamiliar GitHub issue into a clear, evidence-grounded plan for making their first open-source contribution.
The Problem
Contributing to open source can be intimidating for beginners. An issue may describe a bug or feature, but it often leaves contributors wondering:
Which files should I read first?
What parts of the codebase are relevant?
What information is missing from the issue?
What steps should I take before changing code?
How can I verify that my solution works?
RepoGuide AI aims to bridge the gap between finding an issue and knowing how to approach it.
Our Solution
RepoGuide AI analyzes an issue and, when repository data is available, turns it into an actionable contribution guide. It aims to help contributors understand the task, identify relevant source files, ask better questions, and plan implementation and testing.
The goal is not to replace developer judgment. It is to make the first step clearer and more approachable.
Key Features
Issue-to-plan workflow: Turn an issue description into a structured contribution plan.
GitHub integration: Retrieve public repository information in live mode, subject to GitHub access and rate limits.
Evidence-aware guidance: Distinguish findings grounded in retrieved repository information from suggestions that still need verification.
Clarifying questions: Highlight missing requirements and uncertainties that may need to be resolved before implementation.
Implementation guidance: Organize the task into practical next steps and suggested tests.
Offline demo: Explore the bundled example without requiring a live GitHub request.
Optional local AI: Use a compatible local Qwen model through Ollama when configured and available.
Feature availability depends on the selected mode and the current implementation. Verify each feature before treating it as production-ready.
How It Works
Select the offline demo or live GitHub mode.
Provide a GitHub issue URL, or a repository URL together with the issue title and description.
Submit the issue for analysis.
Review the generated contribution plan, supporting evidence, missing information, and suggested tests.
Verify source links and proposed changes before contributing.
Technology Stack
Python: Analysis and application logic
FastAPI: Backend API
HTML, CSS and JavaScript: User interface
GitHub public data: Repository and issue context
Ollama and Qwen: Optional local language-model assistance
Deterministic fallback logic: Support for workflows that do not require local model inference
Getting Started
Prerequisites
Git
Python compatible with the project's dependencies
A web browser
Optional: Ollama and a supported local model for AI-assisted analysis
Live mode requires network access. The offline demo is intended to work without a live GitHub request.
Installation
Clone the repository:
git clone YOUR_GITHUB_REPOSITORY_URL
cd RepoGuide-AI
Create a virtual environment on Windows:
python -m venv .venv
.venv\Scripts\activate
Install the project's dependencies using the dependency file included in the repository:
python -m pip install -r requirements.txt
Run the Application
Start the FastAPI application using the actual application module configured in this project. For example, if the entry point is main.py and it exports app:
uvicorn main:app --reload
Open:
http://127.0.0.1:8000
If your entry point has a different filename or is inside a package, adjust the command accordingly.
Try the Demo
Open the application in your browser.
Select Offline demo to explore the bundled example.
Switch to Live GitHub to test repository-backed analysis.
Review the output and verify the cited source files independently.
If local AI is enabled, make sure Ollama is running and the configured model is available. The application should communicate clearly when a requested mode or dependency is unavailable.
Evidence and Reliability
RepoGuide AI is designed to make its guidance easier to verify.
Repository paths and links should come from retrieved repository data, not invented examples.
Recommendations should be distinguished from confirmed facts.
Missing information should be surfaced rather than silently assumed.
Suggested tests are not the same as tests that have actually been executed.
AI-generated guidance should be reviewed before code is changed or submitted.
These principles reduce the risk of misleading contributors, but they do not guarantee that every recommendation is correct.
Current Status
Stage: Hackathon prototype.
The project is being developed to demonstrate an accessible, evidence-aware workflow for first-time open-source contributions. Live GitHub analysis, optional local inference, and fallback behavior should be validated separately before claiming full end-to-end reliability.
Known Limitations
Repository analysis depends on the information that can be retrieved.
Public GitHub access may be affected by network failures or API rate limits.
A small local language model may produce incomplete or incorrect recommendations.
Offline examples demonstrate the workflow but do not prove live integration works.
Suggested implementation steps and tests require developer review.
Roadmap
Improve relevance and traceability of source-file evidence.
Strengthen validation and recovery for incomplete or failed API requests.
Evaluate whether the recommended files and steps are genuinely useful.
Add automated tests for offline, live, and failure scenarios.
Make it easier for contributors to report issues and improve the project.
Contributing
Contributions, bug reports, and suggestions are welcome.
Open an issue describing the problem or proposed improvement.
Explain how to reproduce a bug where applicable.
Propose a focused change.
Test the change and document the results.
Submit a pull request with a clear description.
Please do not commit API keys, access tokens, passwords, or local environment files.
License
A license has not yet been specified in this draft. Add a LICENSE file and identify the chosen license before inviting others to reuse or redistribute the project.
Project Goal
RepoGuide AI aims to make open-source participation less intimidating by helping developers move from “I found an issue” to “I understand how to approach it.”
poGuide AI
Open source, one step at a time.
RepoGuide AI helps developers turn an unfamiliar GitHub issue into a clear, evidence-grounded plan for making their first open-source contribution.
The Problem
Contributing to open source can be intimidating for beginners. An issue may describe a bug or feature, but it often leaves contributors wondering:
Which files should I read first?
What parts of the codebase are relevant?
What information is missing from the issue?
What steps should I take before changing code?
How can I verify that my solution works?
RepoGuide AI aims to bridge the gap between finding an issue and knowing how to approach it.
Our Solution
RepoGuide AI analyzes an issue and, when repository data is available, turns it into an actionable contribution guide. It aims to help contributors understand the task, identify relevant source files, ask better questions, and plan implementation and testing.
The goal is not to replace developer judgment. It is to make the first step clearer and more approachable.
Key Features
Issue-to-plan workflow: Turn an issue description into a structured contribution plan.
GitHub integration: Retrieve public repository information in live mode, subject to GitHub access and rate limits.
Evidence-aware guidance: Distinguish findings grounded in retrieved repository information from suggestions that still need verification.
Clarifying questions: Highlight missing requirements and uncertainties that may need to be resolved before implementation.
Implementation guidance: Organize the task into practical next steps and suggested tests.
Offline demo: Explore the bundled example without requiring a live GitHub request.
Optional local AI: Use a compatible local Qwen model through Ollama when configured and available.
Feature availability depends on the selected mode and the current implementation. Verify each feature before treating it as production-ready.
How It Works
Select the offline demo or live GitHub mode.
Provide a GitHub issue URL, or a repository URL together with the issue title and description.
Submit the issue for analysis.
Review the generated contribution plan, supporting evidence, missing information, and suggested tests.
Verify source links and proposed changes before contributing.
Technology Stack
Python: Analysis and application logic
FastAPI: Backend API
HTML, CSS and JavaScript: User interface
GitHub public data: Repository and issue context
Ollama and Qwen: Optional local language-model assistance
Deterministic fallback logic: Support for workflows that do not require local model inference
Getting Started
Prerequisites
Git
Python compatible with the project's dependencies
A web browser
Optional: Ollama and a supported local model for AI-assisted analysis
Live mode requires network access. The offline demo is intended to work without a live GitHub request.
Installation
Clone the repository:
git clone YOUR_GITHUB_REPOSITORY_URL
cd RepoGuide-AI
Create a virtual environment on Windows:
python -m venv .venv
.venv\Scripts\activate
Install the project's dependencies using the dependency file included in the repository:
python -m pip install -r requirements.txt
Run the Application
Start the FastAPI application using the actual application module configured in this project. For example, if the entry point is main.py and it exports app:
uvicorn main:app --reload
Open:
http://127.0.0.1:8000
If your entry point has a different filename or is inside a package, adjust the command accordingly.
Try the Demo
Open the application in your browser.
Select Offline demo to explore the bundled example.
Switch to Live GitHub to test repository-backed analysis.
Review the output and verify the cited source files independently.
If local AI is enabled, make sure Ollama is running and the configured model is available. The application should communicate clearly when a requested mode or dependency is unavailable.
Evidence and Reliability
RepoGuide AI is designed to make its guidance easier to verify.
Repository paths and links should come from retrieved repository data, not invented examples.
Recommendations should be distinguished from confirmed facts.
Missing information should be surfaced rather than silently assumed.
Suggested tests are not the same as tests that have actually been executed.
AI-generated guidance should be reviewed before code is changed or submitted.
These principles reduce the risk of misleading contributors, but they do not guarantee that every recommendation is correct.
Current Status
Stage: Hackathon prototype.
The project is being developed to demonstrate an accessible, evidence-aware workflow for first-time open-source contributions. Live GitHub analysis, optional local inference, and fallback behavior should be validated separately before claiming full end-to-end reliability.
Known Limitations
Repository analysis depends on the information that can be retrieved.
Public GitHub access may be affected by network failures or API rate limits.
A small local language model may produce incomplete or incorrect recommendations.
Offline examples demonstrate the workflow but do not prove live integration works.
Suggested implementation steps and tests require developer review.
Roadmap
Improve relevance and traceability of source-file evidence.
Strengthen validation and recovery for incomplete or failed API requests.
Evaluate whether the recommended files and steps are genuinely useful.
Add automated tests for offline, live, and failure scenarios.
Make it easier for contributors to report issues and improve the project.
Contributing
Contributions, bug reports, and suggestions are welcome.
Open an issue describing the problem or proposed improvement.
Explain how to reproduce a bug where applicable.
Propose a focused change.
Test the change and document the results.
Submit a pull request with a clear description.
Please do not commit API keys, access tokens, passwords, or local environment files.
License
A license has not yet been specified in this draft. Add a LICENSE file and identify the chosen license before inviting others to reuse or redistribute the project.
Project Goal
RepoGuide AI aims to make open-source participation less intimidating by helping developers move from “I found an issue” to “I understand how to approach it.”


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
