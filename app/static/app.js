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
  const decisionRail = document.querySelector("#decision-rail");
  const reasonText = document.querySelector("#reason-text");
  const modelText = document.querySelector("#model-text");
  const reviewAlert = document.querySelector("#review-alert");
  const retrievedList = document.querySelector("#retrieved-list");
  const citationSummary = document.querySelector("#citation-summary");
  const timingsSummary = document.querySelector("#timings-summary");
  const singleTab = document.querySelector("#single-tab");
  const batchTab = document.querySelector("#batch-tab");
  const singleMode = document.querySelector("#single-mode");
  const batchMode = document.querySelector("#batch-mode");
  const batchQuestions = document.querySelector("#batch-questions");
  const processBatch = document.querySelector("#process-batch");
  const downloadBatch = document.querySelector("#download-batch");
  const batchStatus = document.querySelector("#batch-status");
  const batchResults = document.querySelector("#batch-results");
  const batchSummary = document.querySelector("#batch-summary");
  const batchResultsBody = document.querySelector("#batch-results-body");
  const reviewFilter = document.querySelector("#review-filter");
  let requestInProgress = false;
  let batchInProgress = false;
  let batchResponses = [];

  function clearElement(element) { element.replaceChildren(); }

  function setMode(mode) {
    const isSingle = mode === "single";
    singleMode.hidden = !isSingle;
    batchMode.hidden = isSingle;
    singleTab.setAttribute("aria-selected", String(isSingle));
    batchTab.setAttribute("aria-selected", String(!isSingle));
    singleTab.tabIndex = isSingle ? 0 : -1;
    batchTab.tabIndex = isSingle ? -1 : 0;
  }

  function clearResults() {
    results.hidden = true;
    errorPanel.hidden = true;
    reviewAlert.hidden = true;
    answerText.textContent = "";
    decisionRail.querySelectorAll(".decision-rail-item").forEach((item) => item.classList.remove("is-active"));
    reasonText.textContent = "";
    modelText.textContent = "";
    citationSummary.textContent = "";
    timingsSummary.textContent = "";
    clearElement(retrievedList);
  }

  function sortedChunks(data) {
    const retrieved = Array.isArray(data.retrieved_context) ? data.retrieved_context : [];
    const citedIds = new Set(Array.isArray(data.citations) ? data.citations : []);
    return [...retrieved].sort((first, second) => Number(citedIds.has(second.id)) - Number(citedIds.has(first.id)));
  }

  function sourceCard(chunk, cited) {
    const card = document.createElement("details");
    card.className = "source-card";
    card.id = `chunk-${chunk.id}`;
    if (cited) card.classList.add("source-card-cited");
    const summary = document.createElement("summary");
    const id = document.createElement("span");
    id.className = "source-id";
    id.textContent = `Chunk ${chunk.id}`;
    const title = document.createElement("span");
    title.className = "source-title";
    title.textContent = chunk.title || "Untitled source";
    summary.append(id, title);
    if (cited) {
      const tag = document.createElement("span");
      tag.className = "source-tag";
      tag.textContent = "Cited";
      summary.append(tag);
    }
    const score = Number(chunk.rerank_score);
    const scoreRow = document.createElement("div");
    scoreRow.className = "source-score";
    const scoreLabel = document.createElement("span");
    scoreLabel.textContent = "Rerank score";
    const scoreTrack = document.createElement("span");
    scoreTrack.className = "score-track";
    scoreTrack.setAttribute("role", "progressbar");
    scoreTrack.setAttribute("aria-label", "Cohere rerank score on a fixed zero to one scale");
    const scoreBar = document.createElement("span");
    scoreBar.className = "score-bar";
    const scoreValue = Number.isFinite(score) ? Math.max(0, Math.min(1, score)) : 0;
    scoreBar.style.width = `${scoreValue * 100}%`;
    scoreTrack.setAttribute("aria-valuemin", "0");
    scoreTrack.setAttribute("aria-valuemax", "1");
    scoreTrack.setAttribute("aria-valuenow", String(scoreValue));
    scoreTrack.append(scoreBar);
    const scoreText = document.createElement("span");
    scoreText.textContent = Number.isFinite(score) ? scoreValue.toFixed(3) : "Not available";
    scoreRow.append(scoreLabel, scoreTrack, scoreText);
    const content = document.createElement("pre");
    content.className = "source-content";
    content.textContent = chunk.content || "No content was returned.";
    card.append(summary, scoreRow, content);
    return card;
  }

  function highlightCitation(chunkId) {
    const card = document.querySelector(`#chunk-${chunkId}`);
    if (!card) return;
    card.open = true;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    card.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "center" });
    card.classList.remove("citation-flash", "citation-highlight");
    if (reducedMotion) {
      card.classList.add("citation-highlight");
      return;
    }
    card.classList.add("citation-flash");
    window.setTimeout(() => card.classList.remove("citation-flash"), 1000);
  }

  function citationChip(chunkId) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "citation-chip";
    chip.textContent = `Chunk ${chunkId}`;
    chip.setAttribute("aria-label", `Show cited chunk ${chunkId}`);
    chip.addEventListener("click", () => highlightCitation(chunkId));
    return chip;
  }

  function renderTimings(timings) {
    clearElement(timingsSummary);
    if (!timings || typeof timings !== "object") return;
    const values = [
      ["Retrieve", timings.retrieve],
      ["Rerank", timings.rerank],
      ["Synthesize", timings.synthesize],
      ["Total", timings.total],
    ];
    if (Number(timings.rerank_wait) > 0) values.splice(2, 0, ["Rerank wait", timings.rerank_wait]);
    values.forEach(([label, value]) => {
      const item = document.createElement("span");
      item.textContent = `${label}: ${Number.isFinite(Number(value)) ? Number(value) : 0} ms`;
      timingsSummary.append(item);
    });
  }

  function emptyState(message) {
    const item = document.createElement("p");
    item.className = "empty-state";
    item.textContent = message;
    return item;
  }

  function displayAnswer(data) {
    const citedIds = new Set(Array.isArray(data.citations) ? data.citations : []);
    const retrieved = sortedChunks(data);
    answerText.textContent = data.answer || "";
    decisionRail.querySelectorAll(".decision-rail-item").forEach((item) => {
      item.classList.toggle("is-active", item.dataset.decision === data.decision);
    });
    reasonText.textContent = `Reason: ${data.reason || "No reason was returned."}`;
    modelText.textContent = `Model: ${data.model_used || "Not provided"}`;
    clearElement(citationSummary);
    const citedChunks = retrieved.filter((chunk) => citedIds.has(chunk.id));
    if (citedChunks.length) citedChunks.forEach((chunk) => citationSummary.append(citationChip(chunk.id)));
    else citationSummary.textContent = "No citations";
    renderTimings(data.timings_ms);
    reviewAlert.hidden = !data.needs_sme_review;
    clearElement(retrievedList);
    if (retrieved.length) retrieved.forEach((chunk) => retrievedList.append(sourceCard(chunk, citedIds.has(chunk.id))));
    else retrievedList.append(emptyState("No evidence was retrieved."));
    results.hidden = false;
  }

  function setLoading(isLoading) {
    requestInProgress = isLoading;
    submitButton.disabled = isLoading;
    question.disabled = isLoading;
    document.querySelectorAll(".example-button").forEach((button) => { button.disabled = isLoading; });
    submitButton.textContent = isLoading ? "Generating answer…" : "Generate answer";
    requestStatus.textContent = isLoading ? "Retrieving evidence and generating an answer…" : "";
  }

  async function requestAnswer(query) {
    const response = await fetch("/documents/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 3 })
    });
    let data = null;
    try { data = await response.json(); } catch { /* A safe generic message follows. */ }
    if (!response.ok) throw new Error(data && typeof data.detail === "string" ? data.detail : "The service could not generate an answer. Please try again later.");
    return data || {};
  }

  function truncate(value, maximum = 180) {
    const text = value || "";
    return text.length > maximum ? `${text.slice(0, maximum - 1)}…` : text;
  }

  function batchDetail(data) {
    const detail = document.createElement("div");
    detail.className = "batch-detail";
    const answer = document.createElement("p");
    answer.className = "batch-full-answer";
    answer.textContent = data.answer || "No answer was returned.";
    const reason = document.createElement("p");
    reason.textContent = `Reason: ${data.reason || "No reason was returned."}`;
    const heading = document.createElement("p");
    heading.className = "batch-evidence-heading";
    heading.textContent = "Cited chunks";
    const sources = document.createElement("div");
    sources.className = "source-list";
    const citedIds = new Set(Array.isArray(data.citations) ? data.citations : []);
    const cited = sortedChunks(data).filter((chunk) => citedIds.has(chunk.id));
    if (cited.length) cited.forEach((chunk) => sources.append(sourceCard(chunk, true)));
    else sources.append(emptyState("No cited chunks were returned."));
    detail.append(answer, reason, heading, sources);
    return detail;
  }

  function appendBatchRow(record) {
    const row = document.createElement("tr");
    row.className = record.error ? "batch-row-error" : "batch-row";
    const questionCell = document.createElement("th");
    questionCell.scope = "row";
    questionCell.textContent = record.question;
    const decisionCell = document.createElement("td");
    const answerCell = document.createElement("td");
    const citationCell = document.createElement("td");
    const reviewCell = document.createElement("td");
    const detailCell = document.createElement("td");
    row.append(questionCell, decisionCell, answerCell, citationCell, reviewCell, detailCell);
    if (record.error) {
      decisionCell.textContent = "Error";
      answerCell.textContent = record.error;
      citationCell.textContent = "—";
      reviewCell.textContent = "—";
      detailCell.textContent = "—";
      batchResultsBody.append(row);
      return { row, detailRow: null };
    }
    const data = record.data;
    const badge = document.createElement("span");
    badge.className = "decision-badge";
    badge.dataset.decision = data.decision || "";
    badge.textContent = data.decision || "No decision";
    decisionCell.append(badge);
    answerCell.textContent = truncate(data.answer);
    citationCell.textContent = String(Array.isArray(data.citations) ? data.citations.length : 0);
    reviewCell.textContent = data.needs_sme_review ? "Yes" : "No";
    const expand = document.createElement("button");
    expand.className = "details-button";
    expand.type = "button";
    expand.textContent = "Details";
    expand.setAttribute("aria-expanded", "false");
    const detailRow = document.createElement("tr");
    detailRow.className = "batch-detail-row";
    detailRow.hidden = true;
    const detailContent = document.createElement("td");
    detailContent.colSpan = 6;
    detailContent.append(batchDetail(data));
    detailRow.append(detailContent);
    expand.addEventListener("click", () => {
      const expanded = expand.getAttribute("aria-expanded") === "true";
      expand.setAttribute("aria-expanded", String(!expanded));
      expand.textContent = expanded ? "Details" : "Hide details";
      detailRow.hidden = expanded;
    });
    detailCell.append(expand);
    batchResultsBody.append(row, detailRow);
    return { row, detailRow };
  }

  function updateBatchSummary() {
    const decisions = {};
    let reviewCount = 0;
    batchResponses.forEach((record) => {
      if (record.error) return;
      const decision = record.data.decision || "No decision";
      decisions[decision] = (decisions[decision] || 0) + 1;
      if (record.data.needs_sme_review) reviewCount += 1;
    });
    const decisionText = Object.entries(decisions).map(([decision, count]) => `${decision}: ${count}`).join(" · ");
    batchSummary.textContent = `Processed ${batchResponses.length}. ${decisionText || "No completed answers yet."} SME review: ${reviewCount}.`;
    downloadBatch.disabled = !batchResponses.some((record) => !record.error);
    applyReviewFilter();
  }

  function applyReviewFilter() {
    const showOnlyReview = reviewFilter.checked;
    batchResponses.forEach((record) => {
      const hidden = showOnlyReview && (!record.data || !record.data.needs_sme_review);
      record.row.hidden = hidden;
      if (record.detailRow) record.detailRow.hidden = true;
    });
  }

  async function processBatchQuestions() {
    if (batchInProgress) return;
    const questions = batchQuestions.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (!questions.length) {
      batchStatus.textContent = "Enter at least one question to process.";
      batchQuestions.focus();
      return;
    }
    batchInProgress = true;
    processBatch.disabled = true;
    batchQuestions.disabled = true;
    downloadBatch.disabled = true;
    batchResponses = [];
    clearElement(batchResultsBody);
    batchResults.hidden = false;
    batchStatus.textContent = `Processing 0 of ${questions.length} questions…`;
    updateBatchSummary();
    let nextIndex = 0;
    async function worker() {
      while (nextIndex < questions.length) {
        const questionText = questions[nextIndex];
        nextIndex += 1;
        let record;
        try { record = { question: questionText, data: await requestAnswer(questionText) }; }
        catch (error) { record = { question: questionText, error: error instanceof Error ? error.message : "The request failed." }; }
        Object.assign(record, appendBatchRow(record));
        batchResponses.push(record);
        batchStatus.textContent = `Processing ${batchResponses.length} of ${questions.length} questions…`;
        updateBatchSummary();
      }
    }
    try { await Promise.all(Array.from({ length: Math.min(3, questions.length) }, worker)); }
    finally {
      batchInProgress = false;
      processBatch.disabled = false;
      batchQuestions.disabled = false;
      batchStatus.textContent = `Finished processing ${batchResponses.length} questions.`;
    }
  }

  function citedChunkTitles(data) {
    const citationIds = new Set(Array.isArray(data.citations) ? data.citations : []);
    return (Array.isArray(data.retrieved_context) ? data.retrieved_context : []).filter((chunk) => citationIds.has(chunk.id)).map((chunk) => chunk.title || `Chunk ${chunk.id}`);
  }

  function downloadResponseDocument() {
    const lines = ["# RFP response document", ""];
    batchResponses.filter((record) => !record.error).forEach((record) => {
      const data = record.data;
      lines.push(`## ${record.question}`, "", `**Decision:** ${data.decision || "No decision"}`, "", data.answer || "No answer was returned.", "", `**Cited chunks:** ${citedChunkTitles(data).join(", ") || "None"}`, "", `**SME review:** ${data.needs_sme_review ? "Yes" : "No"}`, "");
    });
    const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "rfp-response-document.md";
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function loadRfpQuestions() {
    try {
      const response = await fetch("/documents/rfp-questions");
      const data = await response.json();
      if (!response.ok || !Array.isArray(data)) throw new Error("Unable to load the RFP question set.");
      batchQuestions.value = data.map((item) => item.question).filter((item) => typeof item === "string").join("\n");
      batchStatus.textContent = `${data.length} RFP questions loaded. You can edit them before processing.`;
    } catch (error) {
      batchQuestions.placeholder = "Enter one RFP question per line.";
      batchStatus.textContent = error instanceof Error ? error.message : "Unable to load the RFP question set.";
    }
  }

  singleTab.addEventListener("click", () => setMode("single"));
  batchTab.addEventListener("click", () => setMode("batch"));
  reviewFilter.addEventListener("change", applyReviewFilter);
  processBatch.addEventListener("click", processBatchQuestions);
  downloadBatch.addEventListener("click", downloadResponseDocument);
  document.querySelectorAll(".example-button").forEach((button) => button.addEventListener("click", () => { question.value = button.dataset.question || ""; question.focus(); }));
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
    try { displayAnswer(await requestAnswer(query)); }
    catch (error) {
      errorMessage.textContent = error instanceof Error ? error.message : "The service could not generate an answer. Please try again later.";
      errorPanel.hidden = false;
    } finally { setLoading(false); }
  });
  loadRfpQuestions();
})();
