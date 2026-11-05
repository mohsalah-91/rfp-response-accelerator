# Incoming RFP: Vantage Regional Health, 2026

15 questions representing one section of a live RFP. Used as the demo input and
as the evaluation set.

Each entry carries the source document(s) that should be retrieved and the
behavior the system is expected to produce. That turns the demo input into a
labeled set: retrieval can be scored against `expected_source` without a human
reading the output.

## Expected behaviors

| Behavior | Meaning |
|---|---|
| `answer` | Approved content exists. Draft it with citations. |
| `answer_negative` | Approved content exists and the answer is "no" or "out of scope". Draft it. Do not soften it. |
| `answer_partial` | Approved content covers part of the question. Draft what is covered and flag the gap. |
| `redirect` | Policy forbids answering here. Point to the correct response section. |
| `refuse` | No approved content. Draft nothing. Route to an SME. |

## Why the traps matter

`q11` and `q12` ask the vendor to confirm certifications it does not hold. The
corpus contains the correct negative answer. A system that retrieves well will
say no; a system that pattern-matches on "compliance" will produce a confident
yes, which in an RFP is a contractual misrepresentation.

`q13` asks for pricing in a technical response. Policy forbids it. The correct
behavior is to redirect, not to answer.

`q14` and `q15` have no answer anywhere in the corpus. These test whether the
relevance floor fires.
