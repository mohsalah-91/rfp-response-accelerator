# Repository Guidelines

## Project Structure & Module Organization

- `app/` — FastAPI application. `main.py` creates the app and health endpoint; `router.py` provides document ingest, search, and answer endpoints; `database.py` owns the async PostgreSQL pool and startup migrations; `config.py` loads settings; `ingest.py` chunks documents and generates embeddings; `answer_models.py` defines the Pydantic Structured Outputs model.
- `migrations/` — SQL migrations applied during FastAPI startup.
- `scripts/ingest_corpus.py` — client for ingesting the tracked sample corpus.
- `tests/` — standard-library `unittest` coverage for health, import/tokenizer behavior, and structured answer handling.
- `corpus/` — tracked synthetic Halebrook markdown source data. Do not alter corpus files unless the task explicitly requests it.
- `incoming-rfp/` — labeled sample questions, recorded live-request examples, and their documentation.
- `docker-compose.yml` — local PostgreSQL with pgvector. `.env.example` contains sanitized configuration examples.

## Architecture

The application stores chunks and 1536-dimension embeddings in PostgreSQL with pgvector. Search combines vector similarity and PostgreSQL full-text retrieval with reciprocal-rank fusion (RRF), then reranks candidates through Cohere. Keep this retrieval architecture unchanged unless the task explicitly scopes retrieval work.

Answer synthesis uses the asynchronous OpenAI Responses API with Pydantic Structured Outputs: `responses.parse(..., text_format=GroundedAnswer)`. The answer endpoint returns an answer, one of five decisions, citation chunk IDs, a short reason, and an SME-review flag. Citation validation confirms only that cited IDs belong to retrieved context; it does not establish factual entailment. SME review is a returned flag, not an approval, notification, queue, or persistence workflow.

Tokenizer initialization is lazy: importing the application must not initialize `tiktoken`; tokenizer setup occurs only when chunking is requested.

## Local Setup and Commands

Use the existing `venv` when it is present. From PowerShell at the repository root:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

If activation is unavailable, invoke the existing environment directly:

```powershell
.\venv\Scripts\python.exe -m pip check
```

Create `.env` from `.env.example` only when needed, then set local credentials without committing them. Start the local services and API with:

```powershell
docker compose up -d postgres
docker compose exec -T postgres pg_isready -U rag_admin -d ai_enterprise_db
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Compose resolves this repository as project `rfp-response-accelerator`, isolating its default network and `pgvector_data` volume. PostgreSQL is published on host port `5433` (container port `5432`); use the matching `DATABASE_URL` from `.env.example`.

Run checks with:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
.\venv\Scripts\python.exe -m pip check
git diff --check
```

## Ingestion and Data Safety

The corpus is synthetic sample data tracked in Git. Leave it unchanged unless explicitly asked. Ingestion is not idempotent: repeating an ingest inserts duplicate chunks. Do not ingest, reingest, delete data, or reset the database without task authorization.

## Coding and Testing

Match the surrounding code: four-space Python indentation, `snake_case` for functions, variables, and modules, and `PascalCase` for classes. Prefer explicit types at public interfaces and concise docstrings where retrieval, persistence, or validation behavior is non-obvious.

Use `unittest` and `httpx.ASGITransport` for endpoint tests. Mock provider, database, vector-store, and network behavior so unit tests run without credentials. Cover successful behavior, malformed or incomplete provider output, empty retrieval, invalid citations, and provider failures when relevant. Keep tokenizer import regression coverage passing.

Report mocked-test results separately from live provider checks. Mocked tests validate application behavior and request/response handling; they do not demonstrate live model decision accuracy. Do not make live provider calls unless explicitly authorized.

## Security and Change Scope

Never expose API keys, passwords, tokens, private data, provider exceptions containing request data, or `.env` contents. Never commit `.env`; use sanitized placeholders in `.env.example` only. Preserve unrelated local changes in a dirty worktree.

Keep changes targeted. Do not change Docker configuration, database contents, retrieval behavior, or corpus data unless the request authorizes it. Run relevant tests and `git diff --check` before handing off changes. Use focused, imperative commit subjects if a commit is requested.
