const form = document.querySelector("#analyze-form");
const mode = document.querySelector("#mode");
const liveFields = document.querySelector("#live-fields");
const issueUrlInput = document.querySelector("#issue-url");
const repoUrlInput = document.querySelector("#repo-url");
const titleInput = document.querySelector("#issue-title");
const bodyInput = document.querySelector("#issue-body");
const useAiInput = document.querySelector("#use-ai");
const submitButton = document.querySelector("#submit-button");
const errorBox = document.querySelector("#error");
const loading = document.querySelector("#loading");
const reportRoot = document.querySelector("#report");

mode.addEventListener("change", () => {
  liveFields.hidden = mode.value !== "live";
});

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function link(text, href, className) {
  if (!href) return element("span", text, className);
  const node = element("a", text, className);
  node.href = href;
  if (href.startsWith("http")) {
    node.target = "_blank";
    node.rel = "noopener noreferrer";
  }
  return node;
}

function card(title, items, renderItem) {
  const section = element("section", undefined, "report-card");
  const heading = element("h3", title);
  heading.append(element("span", String(items.length), "count"));
  section.append(heading);
  if (!items.length) {
    section.append(element("p", "Nothing was flagged by the available evidence.", "empty"));
    return section;
  }
  const list = element("ul");
  items.forEach((item) => {
    const row = element("li");
    renderItem(row, item);
    list.append(row);
  });
  section.append(list);
  return section;
}

function renderReport(data) {
  reportRoot.replaceChildren();
  const header = element("section", undefined, "panel");
  const headerRow = element("div", undefined, "report-head");
  const titleWrap = document.createElement("div");
  titleWrap.append(element("p", "READINESS REPORT", "eyebrow"));
  titleWrap.append(element("h2", data.issue.title || "Untitled issue"));
  titleWrap.append(link(data.repository.full_name, data.repository_source_url, "repo-name"));
  headerRow.append(titleWrap);
  const modeLabel = data.mode === "offline-demo" ? "OFFLINE DEMO" : data.mode === "cached" ? "CACHED SNAPSHOT" : "LIVE GITHUB";
  const badgeClass = data.mode === "offline-demo" ? "demo" : data.mode === "cached" ? "cached" : "live";
  headerRow.append(element("span", modeLabel, `badge ${badgeClass}`));
  header.append(headerRow);
  header.append(element("p", data.ai.summary, "summary"));
  const aiLabel = data.ai.provider === "ollama-qwen2.5:1.5b" ? "Local Qwen summary" : "Deterministic summary";
  const aiRow = element("p", undefined, "fine-print");
  aiRow.append(element("span", aiLabel, "badge ai"));
  aiRow.append(document.createTextNode(` ${data.ai.status}`));
  header.append(aiRow);
  const issueSource = element("p", undefined, "fine-print");
  issueSource.append(document.createTextNode("Issue source: "));
  if (data.issue.source_url) {
    issueSource.append(link(data.issue.source_label, data.issue.source_url));
  } else {
    issueSource.append(document.createTextNode(data.issue.source_label));
  }
  header.append(issueSource);
  if (data.warnings.length) {
    const warningList = element("ul");
    data.warnings.forEach((warning) => warningList.append(element("li", warning)));
    header.append(warningList);
  }
  reportRoot.append(header);

  const grid = element("div", undefined, "report-grid");
  grid.append(card("Relevant repository files", data.relevant_files, (row, file) => {
    const wrapper = element("div", undefined, "file-item");
    wrapper.append(link(file.path, file.source_url));
    wrapper.append(element("small", file.reason));
    row.append(wrapper);
  }));
  grid.append(card("Missing requirements", data.missing_requirements, (row, text) => row.append(document.createTextNode(text))));
  grid.append(card("Implementation steps", data.implementation_steps, (row, text) => row.append(document.createTextNode(text))));
  grid.append(card("Suggested tests — not run", data.suggested_tests, (row, test) => {
    row.append(document.createTextNode(test.suggestion));
    if (test.source_paths.length) {
      row.append(document.createTextNode(" Existing test files: "));
      test.source_paths.forEach((path, index) => {
        if (index) row.append(document.createTextNode(", "));
        row.append(link(path, test.source_urls[index]));
      });
    }
  }));
  grid.append(card("Questions to clarify", data.unanswered_questions, (row, text) => row.append(document.createTextNode(text))));
  grid.append(card("Limitations", data.limitations, (row, text) => row.append(document.createTextNode(text))));
  reportRoot.append(grid);

  const evidence = element("section", undefined, "report-card");
  evidence.append(element("h3", "Repository evidence"));
  evidence.append(element("p", `${data.file_tree_count} file paths were available to the matching heuristic. No source files were fetched or executed.`, "fine-print"));
  if (data.readme_excerpt) {
    const readmeHeading = element("p", undefined, "fine-print");
    readmeHeading.append(document.createTextNode("README · "));
    readmeHeading.append(link(data.mode === "offline-demo" ? "bundled demo source" : "GitHub source", data.readme_source_url));
    evidence.append(readmeHeading);
    evidence.append(element("pre", data.readme_excerpt, "evidence"));
  } else {
    evidence.append(element("p", "README content was unavailable.", "empty"));
  }
  reportRoot.append(evidence);
  reportRoot.scrollIntoView({ behavior: "smooth", block: "start" });
}

const fieldLabels = {
  mode: "Analysis mode",
  issue_url: "GitHub issue URL",
  repo_url: "GitHub repository URL",
  issue_title: "Issue title",
  issue_body: "Issue details",
  use_ai: "Local AI option",
};

function validationMessage(error) {
  if (error.type === "json_invalid") {
    return "The request body was not valid JSON. Please submit the form again.";
  }
  const location = Array.isArray(error.loc) ? error.loc : [];
  if (location.length === 1 && location[0] === "body" && error.type === "missing") {
    return "The request had no JSON body. Please submit the form again.";
  }
  const field = location.find((part) => typeof part === "string" && fieldLabels[part]);
  const rawMessage = typeof error.msg === "string" ? error.msg : "is invalid";
  const message = rawMessage.replace(/^Value error,\s*/i, "");
  if (field) return `${fieldLabels[field]}: ${message}`;
  if (message.includes("issue_url or repo_url")) {
    return "Live mode requires exactly one source: provide an issue URL or a repository URL, not both.";
  }
  if (message.includes("issue_title is required")) {
    return "Issue title is required when you provide a repository URL.";
  }
  if (message.includes("provide issue_url or repo_url")) {
    return "Enter a GitHub issue URL, or a repository URL with an issue title.";
  }
  return message;
}

function apiErrorMessage(status, data) {
  const detail = data && data.detail;
  if (typeof detail === "string" && status !== 500) return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map(validationMessage).filter(Boolean);
    if (messages.length) return [...new Set(messages)].join(" ");
  }
  if (status >= 500) {
    return `RepoGuide encountered a server error (HTTP ${status}). Please retry.`;
  }
  return `The server rejected the request (HTTP ${status}). Please check the fields and retry.`;
}

function validatePayload(payload) {
  if (payload.mode !== "live") return null;
  const hasIssueUrl = Boolean(payload.issue_url);
  const hasRepoUrl = Boolean(payload.repo_url);
  if (hasIssueUrl && hasRepoUrl) {
    return {
      field: issueUrlInput,
      message: "Choose either a GitHub issue URL or a repository URL, not both.",
    };
  }
  if (!hasIssueUrl && !hasRepoUrl) {
    return {
      field: issueUrlInput,
      message: "Enter a GitHub issue URL, or a repository URL with an issue title.",
    };
  }
  if (hasRepoUrl && !payload.issue_title) {
    return {
      field: titleInput,
      message: "Issue title is required when you provide a repository URL.",
    };
  }
  return null;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  reportRoot.replaceChildren();
  const payload = { mode: mode.value, use_ai: useAiInput.checked };
  if (mode.value === "live") {
    const issueUrl = issueUrlInput.value.trim();
    const repoUrl = repoUrlInput.value.trim();
    if (issueUrl) payload.issue_url = issueUrl;
    if (repoUrl) payload.repo_url = repoUrl;
    if (repoUrl) {
      payload.issue_title = titleInput.value.trim();
      payload.issue_body = bodyInput.value.trim();
    }
  }
  const validationError = validatePayload(payload);
  if (validationError) {
    errorBox.textContent = validationError.message;
    errorBox.hidden = false;
    validationError.field.focus();
    return;
  }

  loading.hidden = false;
  submitButton.disabled = true;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const responseText = await response.text();
    let data = null;
    if (responseText) {
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.warn("[RepoGuide] API returned a non-JSON response.", {
          status: response.status,
          contentType: response.headers.get("content-type"),
          error: parseError,
        });
      }
    }
    if (!response.ok) {
      console.error("[RepoGuide] Analysis request rejected.", {
        status: response.status,
        validation: data && Array.isArray(data.detail)
          ? data.detail.map(({ loc, type, msg }) => ({ loc, type, msg }))
          : undefined,
      });
      throw new Error(apiErrorMessage(response.status, data));
    }
    if (!data || typeof data !== "object" || !data.issue || !data.repository || !data.ai) {
      throw new Error("The server returned an unexpected response. Please retry.");
    }
    renderReport(data);
  } catch (error) {
    console.error("[RepoGuide] Could not complete analysis.", error);
    if (error && error.name === "AbortError") {
      errorBox.textContent = "The request took too long. Check your connection and try again.";
    } else if (error instanceof TypeError) {
      errorBox.textContent = "Could not reach RepoGuide. Check that the local server is running, then retry.";
    } else {
      errorBox.textContent = error instanceof Error
        ? error.message
        : "Something went wrong. Please retry.";
    }
    errorBox.hidden = false;
  } finally {
    clearTimeout(timeout);
    loading.hidden = true;
    submitButton.disabled = false;
  }
});
