"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const script = fs.readFileSync(path.join(__dirname, "..", "app", "static", "app.js"), "utf8");
const labelsStart = script.indexOf("  const batchDecisionLabels");
const start = script.indexOf("  function normalizeQuestionText");
const end = script.indexOf("  function batchDetail", start);
assert.ok(labelsStart >= 0 && start > labelsStart && end > start, "Batch input helpers must be present in app.js.");
const labelHelpers = script.slice(labelsStart, start);
const parserHelpers = script.slice(start, end);

const decisionLabel = Function(`${labelHelpers}\nreturn batchDecisionLabel;`)();
assert.equal(decisionLabel("answer"), "Answered");
assert.equal(decisionLabel("answer_negative"), "Documented no");
assert.equal(decisionLabel("answer_partial"), "Partial answer");
assert.equal(decisionLabel("redirect"), "Route by policy");
assert.equal(decisionLabel("refuse"), "Insufficient evidence");

function parse(value, catalog) {
  return Function(
    "batchQuestions",
    "batchQuestionCatalog",
    `${parserHelpers}\nreturn parseBatchQuestions();`,
  )({ value }, catalog);
}

const ssoQuestion = "Which single sign-on standards do you support, and is automated user provisioning available?";
const catalog = [{ id: "q02", question: ssoQuestion }];
const mixed = parse(
  `  WHICH single sign-on standards do you support, and is automated user provisioning available?\nq11: Confirm FedRAMP status.\n3) What infrastructure is needed for 30,000 assets?`,
  catalog,
);

assert.deepEqual(
  mixed.map(({ id, position, rowKey, question }) => ({ id, position, rowKey, question })),
  [
    { id: "q02", position: 1, rowKey: "batch-1", question: "WHICH single sign-on standards do you support, and is automated user provisioning available?" },
    { id: "q11", position: 2, rowKey: "batch-2", question: "Confirm FedRAMP status." },
    { id: "R03", position: 3, rowKey: "batch-3", question: "What infrastructure is needed for 30,000 assets?" },
  ],
);

const duplicates = parse(`${ssoQuestion}\n2. ${ssoQuestion}`, catalog);
assert.deepEqual(duplicates.map((item) => item.id), ["q02", "q02"]);
assert.notEqual(duplicates[0].rowKey, duplicates[1].rowKey);

assert.match(script, /batchResponses = questions\.map/);
assert.match(script, /batchResponses\[questionEntry\.position - 1\]/);
assert.match(script, /\[\.\.\.batchResponses\]\.sort\(\(first, second\) => first\.position - second\.position\)/);
assert.match(script, /answer_negative: "Documented no"/);
assert.match(script, /redirect: "Route by policy"/);
assert.match(script, /refuse: "Insufficient evidence"/);
assert.match(script, /cells\.decisionCell\.textContent = "Processing error"/);
assert.match(script, /item\.classList\.toggle\("is-active", item\.dataset\.decision === data\.decision\)/);
assert.match(script, /item\.querySelector\("\.decision-rail-label"\)\.textContent = label/);

console.log("batch input parsing and ordered-result wiring passed");
