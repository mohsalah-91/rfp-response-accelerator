(() => {
  "use strict";

  const form = document.querySelector("#answer-form");
  const question = document.querySelector("#question");
  const submitButton = document.querySelector("#submit-button");
  const requestStatus = document.querySelector("#request-status");
  const results = document.querySelector("#results");
  const errorPanel = document.querySelector("#error-panel");
  const errorMessage = document.querySelector("#error-message");
  const answerText = document.querySelector("#answer-text");
  const decisionBadge = document.querySelector("#decision-badge");
  const reasonText = document.querySelector("#reason-text");
  const modelText = document.querySelector("#model-text");
  const reviewAlert = document.querySelector("#review-alert");
  const citationList = document.querySelector("#citation-list");
  const retrievedList = document.querySelector("#retrieved-list");
  const citationSummary = document.querySelector("#citation-summary");
  let requestInProgress = false;

  function clearElement(element) {
    element.replaceChildren();
  }

  function clearResults() {
    results.hidden = true;
    errorPanel.hidden = true;
    reviewAlert.hidden = true;
    answerText.textContent = "";
    decisionBadge.textContent = "";
    decisionBadge.removeAttribute("data-decision");
    reasonText.textContent = "";
    modelText.textContent = "";
    citationSummary.textContent = "";
    clearElement(citationList);
    clearElement(retrievedList);
  }

  function sourceCard(chunk, cited) {
    const card = document.createElement("details");
    card.className = "source-card";
    const summary = document.createElement("summary");
    const id = document.createElement("span");
    id.className = "source-id";
    id.textContent = `Chunk ${chunk.id}`;
    const title = document.createElement("span");
    title.className = "source-title";
    title.textContent = chunk.title;
    summary.append(id, title);
    if (cited) {
      const tag = document.createElement("span");
      tag.className = "source-tag";
      tag.textContent = "Cited";
      summary.append(tag);
    }
    const content = document.createElement("pre");
    content.className = "source-content";
    content.textContent = chunk.content;
    card.append(summary, content);
    return card;
  }

  function emptyState(message) {
    const item = document.createElement("p");
    item.className = "empty-state";
    item.textContent = message;
    return item;
  }

  function displayAnswer(data) {
    const retrieved = Array.isArray(data.retrieved_context) ? data.retrieved_context : [];
    const citationIds = Array.isArray(data.citations) ? data.citations : [];
    const citedIds = new Set(citationIds);
    const chunksById = new Map(retrieved.map((chunk) => [chunk.id, chunk]));

    answerText.textContent = data.answer || "";
    decisionBadge.textContent = data.decision || "No decision";
    decisionBadge.dataset.decision = data.decision || "";
    reasonText.textContent = data.reason || "No reason was returned.";
    modelText.textContent = data.model_used || "Not provided";
    reviewAlert.hidden = !data.needs_sme_review;

    const citedChunks = citationIds.map((id) => chunksById.get(id)).filter(Boolean);
    citationSummary.textContent = `${citedChunks.length} cited source${citedChunks.length === 1 ? "" : "s"}`;
    clearElement(citationList);
    if (citedChunks.length) {
      citedChunks.forEach((chunk) => citationList.append(sourceCard(chunk, true)));
    } else {
      citationList.append(emptyState("No citations were returned for this response."));
    }

    clearElement(retrievedList);
    if (retrieved.length) {
      retrieved.forEach((chunk) => retrievedList.append(sourceCard(chunk, citedIds.has(chunk.id))));
    } else {
      retrievedList.append(emptyState("No evidence was retrieved."));
    }
    results.hidden = false;
  }

  function setLoading(isLoading) {
    requestInProgress = isLoading;
    submitButton.disabled = isLoading;
    question.disabled = isLoading;
    document.querySelectorAll(".example-button").forEach((button) => {
      button.disabled = isLoading;
    });
    submitButton.textContent = isLoading ? "Generating answer…" : "Generate answer";
    requestStatus.textContent = isLoading ? "Retrieving evidence and generating an answer…" : "";
  }

  document.querySelectorAll(".example-button").forEach((button) => {
    button.addEventListener("click", () => {
      question.value = button.dataset.question || "";
      question.focus();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (requestInProgress) return;

    const query = question.value.trim();
    if (query.length < 3) {
      question.setCustomValidity("Enter a question with at least 3 characters.");
      question.reportValidity();
      question.setCustomValidity("");
      return;
    }

    clearResults();
    setLoading(true);
    try {
      const response = await fetch("/documents/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 3 })
      });
      let data;
      try {
        data = await response.json();
      } catch {
        data = null;
      }
      if (!response.ok) {
        throw new Error(data && typeof data.detail === "string" ? data.detail : "The service could not generate an answer. Please try again later.");
      }
      displayAnswer(data || {});
    } catch (error) {
      errorMessage.textContent = error instanceof Error ? error.message : "The service could not generate an answer. Please try again later.";
      errorPanel.hidden = false;
    } finally {
      setLoading(false);
    }
  });
})();
