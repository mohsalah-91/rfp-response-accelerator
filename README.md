# RFP Response Accelerator

A FastAPI application for evidence-grounded RFP drafting using the **OpenAI Responses API with Pydantic Structured Outputs**.

The application retrieves relevant enterprise documentation, reranks it, and generates an answer with an explicit decision, source references, and a review flag. The supplied corpus describes **Halebrook Systems**, a fictional infrastructure and security software vendor. The corpus is synthetic sample data, not a set of verified claims about a real company.

## Architecture

```text
Markdown corpus
    → heading-aware, token-aware chunking
    → OpenAI embeddings
    → PostgreSQL + pgvector and full-text index

RFP question
    → OpenAI query embedding
    → vector search + PostgreSQL full-text search
    → reciprocal rank fusion (RRF)
    → Cohere reranking
    → OpenAI Responses API + Pydantic Structured Outputs
    → application validation
    → answer, decision, citations, retrieved evidence, and SME-review flag
```

Retrieval stays in the application and PostgreSQL. The application does not use OpenAI-hosted file search or an agent framework.

| Component | Purpose |
| --- | --- |
| FastAPI | HTTP endpoints, the browser interface at `/ui`, and interactive API documentation at `/docs` |
| PostgreSQL + pgvector | Persistent document chunks, vector similarity, and full-text retrieval |
| OpenAI embeddings | Document and query vectors; default `text-embedding-3-small` |
| Cohere | Reranking; default `rerank-v3.5` |
| OpenAI Responses API | Answer synthesis; default `gpt-5` |
| Pydantic | Structured generation schema and response validation |

## Local setup

Commands below use Windows PowerShell from the repository root.

### Prerequisites

- Python 3.12 is recommended.
- Docker Desktop running Linux containers.
- OpenAI API access for embeddings and the configured answer model.
- Cohere API access for reranking.
- Network access for package installation, provider requests, and the initial tokenizer download.

OpenAI and Cohere have separate API credentials and billing. A ChatGPT subscription does not supply API credits.

### 1. Create or reuse the Python environment

If `venv` already exists, reuse it. Otherwise:

```powershell
py -3.12 -m venv venv
```

Activate and install:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

If PowerShell blocks activation, invoke `.\venv\Scripts\python.exe` directly in place of `python`. On macOS/Linux, use `python3 -m venv venv` and `source venv/bin/activate`.

### 2. Configure the local environment

Create `.env` only if it does not exist:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Edit it locally. Do not commit or share real credentials.

| Variable | Meaning |
| --- | --- |
| `POSTGRES_PASSWORD` | Password used when initializing the local database |
| `DATABASE_URL` | Connection string matching the database user, password, host port, and name |
| `OPENAI_API_KEY` | Used for embeddings and Responses |
| `COHERE_API_KEY` | Used for reranking |
| `ANSWER_MODEL` | Responses-compatible model; default `gpt-5` |
| `EMBEDDING_MODEL` | Default `text-embedding-3-small`; database vectors are 1536-dimensional |
| `RERANK_MODEL` | Default `rerank-v3.5` |

Match the **host port in your checked-in `docker-compose.yml`**. For an isolated database using `5433:5432`, the URL has this shape:

```dotenv
DATABASE_URL=postgresql://rag_admin:YOUR_LOCAL_PASSWORD@localhost:5433/ai_enterprise_db
```

If Compose maps `5432:5432`, use `localhost:5432` instead. The password must match `POSTGRES_PASSWORD`. Changing an environment variable does not update a password in an already-initialized database volume.

To run alongside another PostgreSQL instance on port 5432, use host port 5433. Keep projects on distinct Compose project names, volumes, and host ports; do not remove another project's database to resolve a name conflict.

### 3. Start the database and API

```powershell
docker compose up -d postgres
docker compose exec -T postgres pg_isready -U rag_admin -d ai_enterprise_db
python -m uvicorn app.main:app --reload
```

Wait for **Application startup complete**. Startup creates the pgvector extension, document table, and full-text migration objects.

- Health: http://127.0.0.1:8000/health
- Browser interface: http://127.0.0.1:8000/ui
- Interactive API alternative: http://127.0.0.1:8000/docs

The health endpoint is a liveness check, not a complete provider-readiness test. Database initialization happens during application startup.

### Use the RFP response interface

After starting the API, open http://127.0.0.1:8000/ui in a browser. Enter an RFP question or select an example, then choose **Generate answer**. The interface sends the question to the local `/documents/answer` endpoint with `top_k: 3`, shows the drafted answer, returned decision, and reason, and lets you expand cited sources and all retrieved evidence. The SME-review indicator reports the response flag; it is not an approval workflow. FastAPI serves this UI and its static assets directly, so no separate frontend server or build step is needed. Use `/docs` instead when you prefer the interactive API.

### 4. Ingest once

Keep the API running and open another terminal using the same virtual environment.

Check the database first, after successful API startup:

```powershell
docker compose exec -T postgres psql -U rag_admin -d ai_enterprise_db -c "SELECT COUNT(*) AS ingested_chunks FROM document_chunks;"
```

If empty, ingest:

```powershell
python scripts/ingest_corpus.py
```

Inspect the summary for zero failures; the script can exit normally even when individual documents fail. It skips very short documents. Chunk counts depend on corpus contents and splitting; they are not document counts.

**Ingestion is not idempotent.** Repeating it inserts duplicates. Do not reingest merely to restart the API or change answer-generation instructions.

Check repeated title/chunk-index pairs:

```powershell
docker compose exec -T postgres psql -U rag_admin -d ai_enterprise_db -c "SELECT title, chunk_index, COUNT(*) AS copies FROM document_chunks GROUP BY title, chunk_index HAVING COUNT(*) > 1;"
```

Tokenizer initialization is deferred until chunking is needed. First ingestion may download `cl100k_base` assets from `openaipublic.blob.core.windows.net`; startup avoids that download, but ingestion still needs access or a valid cached asset.

## API and structured answers

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Liveness |
| `GET /` | Application metadata |
| `POST /documents/ingest` | Chunk, embed, and persist a document |
| `POST /documents/search` | Retrieve and rerank source chunks |
| `POST /documents/answer` | Retrieve evidence and generate a structured answer |

Example request:

```json
{
  "query": "What deployment models are supported?",
  "top_k": 3
}
```

The answer endpoint returns:

| Field | Meaning |
| --- | --- |
| `query` | Original question |
| `answer` | Drafted response |
| `retrieved_context` | Retrieved chunks, source titles, IDs, and retrieval scores |
| `model_used` | Configured answer model |
| `decision` | One of the five decisions below |
| `citations` | IDs of supporting retrieved chunks |
| `needs_sme_review` | Whether subject-matter-expert review is required |
| `reason` | Brief evidence/policy justification, not internal reasoning |

| Decision | Meaning |
| --- | --- |
| `answer` | Evidence supports the requested answer |
| `answer_negative` | Evidence explicitly establishes non-support or an unavailable capability |
| `answer_partial` | Evidence supports only part of the requested answer |
| `redirect` | An evidenced policy assigns the request to another owner |
| `refuse` | No supporting evidence or an applicable policy prohibits the requested response |

These labels follow `incoming-rfp/questions.jsonl`. Missing evidence is not evidence that a capability is unavailable. A documented product-specific limitation can be explained as part of a complete answer.

### Why Structured Outputs?

The official async SDK uses `responses.parse(..., text_format=GroundedAnswer)` to generate a schema-constrained response. Trusted rules are separate from the question and retrieved document content. Response storage is disabled with `store=False`; this is not a claim of zero data retention across providers.

The application checks completion, provider refusal, parsed output, required text, citation membership, and applicable review rules. Invalid upstream answers produce sanitized HTTP 502 responses. Empty retrieval returns a deterministic review-required refusal without calling the answer model.

A provider safety refusal is distinct from the application's business decision `refuse`.

## Validation

Run from the repository root:

```powershell
python -m unittest discover -s tests -v
python -m pip check
git diff --check
```

Mocked tests cover structured response handling, failure paths, citation integrity, and startup without tokenizer initialization. Read the current runner output for the exact test count.

Representative manual live checks have exercised corpus ingestion, retrieval/reranking, deployment answers, and explicit FedRAMP non-authorization. These are integration examples, not a systematic evaluation of answer quality across the dataset. Mocked tests cannot establish model decision accuracy.

## Try the application

Complete setup and ingest the sample corpus once, then keep the database and API running. The browser interface at http://127.0.0.1:8000/ui is the direct question-submission workflow. Alternatively, open http://127.0.0.1:8000/docs and expand **POST /documents/answer**. Select **Try it out**, enter one of the requests below, and select **Execute**.

For each response:

1. Read the drafted answer and its decision.
2. Match the IDs in `citations` to entries in `retrieved_context`.
3. Check whether the retrieved passages support the answer's claims.
4. Inspect `needs_sme_review` and `reason` for limitations or required review.

To inspect retrieval independently, use **POST /documents/search** with the same question and `limit: 3`.

Example answer requests:

```json
{"query": "What deployment models are supported?", "top_k": 3}
```

```json
{"query": "Confirm that Halebrook holds FedRAMP Moderate authorization and provide the package identifier.", "top_k": 3}
```

```json
{"query": "Do you support Kubernetes admission controller integration for runtime policy enforcement?", "top_k": 3}
```

Expected decisions for these examples are `answer`, `answer_negative`, and `refuse`, respectively, when using the supplied corpus. The first should explain the Gate-specific deployment exception; the second should state that FedRAMP authorization is not held without inventing an identifier; the third should acknowledge insufficient evidence and require review.

Retrieval and generation can vary. Compare actual responses with the source passages rather than treating the expected labels as guaranteed outcomes. No reingestion is needed when changing questions or answer instructions.

## Limitations and next steps

- Citation validation checks that IDs belong to retrieved evidence; it does not prove factual entailment or complete citation coverage.
- Structured Outputs constrain shape, not truth or decision accuracy.
- Prompt instructions reduce document-injection risk but do not eliminate it.
- SME review is a returned flag; no approval queue or notification workflow is implemented.
- `MIN_RERANK_SCORE` is not an active confidence gate. Reranking scores are relevance signals, not calibrated probabilities.
- The supplied question dataset is not an implemented evaluation runner. Systematic retrieval and decision evaluation is future work.
- Ingestion can create duplicates; no document-versioning or refresh workflow is implemented.
- This is a local prototype without production authentication, tenant isolation, deployment hardening, or an elaborate frontend.
- API usage incurs provider costs. Only send content you are authorized to share with those providers.

## Repository layout

```text
app/                         FastAPI, configuration, retrieval, ingestion, answer models
app/static/index.html        Browser interface markup served at /ui
app/static/app.js            Browser question submission and answer/evidence rendering
app/static/styles.css        Browser interface styles
corpus/                      Synthetic Halebrook source documents
incoming-rfp/questions.jsonl  Questions and expected behaviors/sources
migrations/                  Database migrations applied on startup
scripts/ingest_corpus.py      Corpus ingestion client
tests/test_ui.py             Browser UI, static-asset, and public-route tests
tests/                       Other automated tests for health, imports, and answer handling
docker-compose.yml           Local PostgreSQL/pgvector service
.env.example                 Configuration template without real credentials
```
