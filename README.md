# 17 — Celery Workflows and Monitoring for RAG Document Intelligence

RAG Document Intelligence is a Retrieval-Augmented Generation (RAG) system for document-grounded question answering. This stage adds Celery workflows for processing and indexing, scheduled maintenance, execution tracking, and Flower monitoring.

## 1. Target Architecture

```text
HTTP Client
    │
    ▼
FastAPI (project API)
    ├── LLM: answer generation
    ├── Embeddings: text vector representation
    ├── PostgreSQL: projects, files, chunks, and task executions
    └── Qdrant or PGVector: semantic search
```

## 2. Prerequisites

- Python 3.11 or later;
- Conda or [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install), recommended for dependency isolation.

## 3. Create and Activate the Python Environment

Run from: **any directory**.

```bash
conda create -n rag python=3.11 -y
conda activate rag
```

Optionally, make the terminal prompt easier to read:

Run from: **any directory**, after activating `rag`.

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## Team Command Interface

The repository `Makefile` is the recommended interface for local development.
Every `make` command below must be run from the **repository root**
(`RAGDocumentsIntelligence/`). The Makefile enters `src/` or `docker/`
automatically. By default it runs Python through the Conda environment named
`rag`, independently of whether the current shell displays `(base)`, `(.venv)`,
or both. It resolves that environment to its absolute interpreter path and
removes inherited Python and macOS launcher variables. Packages and the
standard library from a pyenv installation therefore cannot leak into Conda.

To select another Conda environment or a virtualenv interpreter explicitly:

```bash
make CONDA_ENV=my-environment api
make PYTHON=.venv/bin/python api
```

```bash
make check-python
make help
make env-local
make env-docker
make install
make infra
make migrate
```

Run each long-running application in a separate terminal, always from the
repository root:

```bash
make api
make worker
make beat
make flower
```

`make check-python` must report the `rag` interpreter and `lzma: OK`. If your
terminal is already inside `src/`, the forwarding Makefile accepts the same
command: `make check-python`.

For an entirely containerized environment, use:

```bash
make docker-up
make docker-logs
```

Stop it with `make docker-down`. Use `make docker-reset` only when all Docker
volumes and their development data should be deleted.

If your terminal is already inside `src/`, the included forwarding Makefile
accepts the same commands, so `make api`, `make worker`, and `make flower` work
without returning to the repository root.

## 4. Enter the Application Directory and Install Dependencies

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
conda run --no-capture-output -n rag python -m pip install -r requirements.txt
conda run --no-capture-output -n rag python -m pip check
```

Versions are pinned so every developer uses compatible dependencies. FastAPI defines routes, Uvicorn runs the application, and `python-multipart` supports file uploads.
Using `conda run -n rag` prevents pyenv or a global Python installation from
receiving the project dependencies by mistake.

## 5. Configure the Environment

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
cp .env.example .env
```

`src/.env` is your personal local configuration and is ignored by Git. Store
secrets, passwords, and the current Ollama/ngrok URL there. `src/.env.example`
is the versioned template: it documents every required variable with safe
placeholder values and must never contain a real secret.

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
```

## 6. Run Locally with Docker Dependencies

This mode runs FastAPI, Celery, Celery Beat, and Flower from the `rag` Conda
environment. Docker runs only PostgreSQL/PGVector, RabbitMQ, and Redis. Open a
separate terminal for each long-running command.

The `make` commands above are preferred for team development. The expanded
commands below document exactly what each target executes.

### Terminal 1 — Start the infrastructure

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
conda activate rag
cd docker
docker compose up -d rabbitmq redis pgvector
docker compose ps rabbitmq redis pgvector
```

If Compose reports an obsolete container from another branch, recreate this
subset and remove only orphaned containers:

Run from: **`RAGDocumentsIntelligence/docker/`**.

```bash
docker compose up -d --remove-orphans rabbitmq redis pgvector
```

Follow the infrastructure logs when troubleshooting:

Run from: **`RAGDocumentsIntelligence/docker/`**.

```bash
docker compose logs -f rabbitmq redis pgvector
```

The local values in `src/.env` must use the published host ports:

```env
POSTGRES_HOST="localhost"
POSTGRES_PORT=5400
CELERY_BROKER_URL="amqp://rag_user:change-me@localhost:5672/rag_vhost"
CELERY_RESULT_BACKEND="redis://:change-me@localhost:6379/0"
```

### Apply PostgreSQL migrations

Run migrations once after creating the database, and again whenever a new
Alembic migration is added:

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src/models/db_schemes/minirag
cp -n alembic.ini.example alembic.ini
conda run --no-capture-output -n rag python -m alembic upgrade head
cd ../../../
```

### Terminal 2 — Start FastAPI

Port `8001` keeps the local server separate from the Docker FastAPI port:

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
conda run --no-capture-output -n rag python -m uvicorn main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8001
```

Open `http://localhost:8001/docs` or verify the API with:

Run from: **any directory**.

```bash
curl http://localhost:8001/api/v1/
```

### Terminal 3 — Start the Celery worker

The worker must consume every queue declared by this branch. The duplicate
`file_processing,file_processing` shown in an earlier command is incorrect.

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
conda run --no-capture-output -n rag python -m celery \
  -A celery_app.celery_app worker \
  --loglevel=INFO \
  --queues=default,file_processing,data_indexing,mail_service_queue \
  --pool=solo \
  --concurrency=1
```

`--pool=solo` is recommended for local macOS development. Production workers
can use their normal prefork pool and the configured concurrency.

### Terminal 4 — Start scheduled tasks

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
conda run --no-capture-output -n rag python -m celery \
  -A celery_app.celery_app beat \
  --loglevel=INFO
```

### Terminal 5 — Start Flower monitoring

Flower is already installed by `requirements.txt`; no additional
`pip install flower` command is required.

For authenticated access, add the following setting to `src/.env` before
starting Flower (replace the example value):

```env
CELERY_FLOWER_PASSWORD="change-me"
```

If the setting is omitted, Flower starts without basic authentication for
local development.

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
conda run --no-capture-output -n rag python -m celery \
  -A celery_app.celery_app flower \
  --conf=flowerconfig.py \
  --port=5555
```

Using `conda run -n rag` is important even when the prompt displays an active
environment: it prevents a higher-priority pyenv shim from loading a Python
build that does not provide `_lzma`. Open Flower at `http://localhost:5555`.

## 7. Load Configuration and Organize Routes

`main.py` loads `.env`, initializes the shared asynchronous PostgreSQL session
factory, and registers FastAPI routers. The base route is versioned under
`/api/v1`, allowing future API versions without breaking existing clients.

`GET /api/v1/` returns the application name and version defined in `.env`, confirming both API availability and configuration loading.

## 8. Verify the FastAPI Application

For the local mode from section 6, use `http://localhost:8001`. For the full
Docker mode, use `http://localhost:5001` directly or `http://localhost` through
Nginx.

Run from: **any directory**.

```bash
curl http://localhost:8001/api/v1/
curl http://localhost:8001/api/v1/send_reports
```

## 9. Upload a Document

`POST /api/v1/data/upload/{project_id}` accepts TXT and PDF files declared in `.env`. It validates MIME type and size, sanitizes the client filename, creates a project folder, and writes the file asynchronously under `src/assets/files/`.

Run from: **the directory containing `document.pdf`**.

```bash
curl -F "file=@document.pdf" http://localhost:8001/api/v1/data/upload/1
```

Uploaded documents are not versioned: `src/assets/.gitignore` protects runtime data.

## 10. Process an Uploaded Document

After upload, call `POST /api/v1/data/process/{project_id}` with the identifier returned by the upload endpoint. The controller reads a TXT or PDF file, preserves source metadata, and creates overlapping chunks for later vector indexing.

```json
{
  "file_id": "uploaded-file-id.pdf",
  "chunk_size": 500,
  "overlap_size": 50
}
```

`chunk_size` defines the maximum fragment size; `overlap_size` repeats a portion of the previous chunk to preserve context.

## 11. Track File Assets

Every successful upload creates an `assets` record containing the project ID,
server-side filename, file type, size, and upload timestamp. A compound index
prevents duplicate filenames within one project.

Processing can now target one `file_id` or omit it to process every asset belonging to the project. Each stored chunk references both its project and source asset.

## 12. Configure an LLM Provider

The provider layer separates application logic from vendor SDKs. Configure OpenAI, Cohere, or an OpenAI-compatible endpoint through `.env`, then select the generation and embedding models. The same interface exposes `generate_text` and `embed_text` to future RAG services.

## 13. Configure the Vector Store

Qdrant stores document embeddings for semantic retrieval. Configure the local path, provider, and distance method in `.env`. The provider abstraction can create collections, batch-insert vectors, and search nearest vectors without coupling application services to the Qdrant SDK.

## 14. Persist Projects and Chunks

The first upload creates a row in PostgreSQL's `projects` table. Processing
inserts rows into `chunks`, including their text, metadata, order, and owning
project and asset IDs. With `do_reset: true`, existing project chunks are
removed before the new insertion.

## 15. Test with Postman

Import `assets/rag-document-intelligence.postman_collection.json`. Set `api` to
`http://localhost:8001` for local mode, `http://localhost:5001` for direct
Docker access, or `http://localhost` for Nginx. Then run the requests in order.

## 16. Index, Search, and Answer with RAG

Stage 10 adds the `/api/v1/nlp` router. It indexes persisted chunks in Qdrant, retrieves semantically related chunks, and uses locale-specific templates to build a prompt for the configured generation provider.

The available operations are:

- `POST /api/v1/nlp/index/push/{project_id}`: create or reset a project vector collection and index its chunks;
- `GET /api/v1/nlp/index/info/{project_id}`: inspect the vector collection;
- `POST /api/v1/nlp/index/search/{project_id}`: retrieve matching chunks;
- `POST /api/v1/nlp/index/answer/{project_id}`: retrieve context and generate an answer.

The template language is selected through `PRIMARY_LANG` and falls back to `DEFAULT_LANG`. Configure the LLM and vector database variables in `src/.env` before starting the API.

## 17. Template and Route Corrections

The answer templates now interpolate the submitted question before the answer section. Both the indexing and collection-information routes also receive the application template parser, so every `NLPController` is constructed with the dependencies expected by the controller contract.

## 18. PostgreSQL Persistence and Migrations

Configure `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and `POSTGRES_MAIN_DATABASE` in `src/.env`. The FastAPI startup hook creates an asynchronous SQLAlchemy session factory; project, asset, and chunk repositories use it for persistence.

Start the PostgreSQL container from `docker/`, then initialize the schema:

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd docker
docker compose up -d pgvector
cd ../src/models/db_schemes/minirag
cp -n alembic.ini.example alembic.ini
# Set sqlalchemy.url in alembic.ini, then run:
conda run --no-capture-output -n rag python -m alembic upgrade head
```

The Alembic directory is kept with this tutorial step so schema changes can be generated and applied predictably.

## 19. Run with Ollama or Cloud LLMs

Set `LLM_MODE="OLLAMA"` in `src/.env` to use the OpenAI-compatible Ollama API.
For a local Mac server, use `OLLAMA_API_URL="http://localhost:11434/v1"`. For
Colab, replace it with the ngrok HTTPS URL followed by `/v1`.

Set `LLM_MODE="CLOUD"` and provide `CLOUD_OPENAI_API_KEY` to use OpenAI or a
compatible cloud endpoint. The profile selection maps the chosen values onto
the existing provider factory, so routes and controllers do not need to change.

See [the Ollama local and Colab guide](docs/OLLAMA_LOCAL_AND_COLAB.md) for the
model downloads, Colab startup cells, ngrok setup, and safety guidance.

## 20. Store Vectors with PGVector

Set `VECTOR_DB_BACKEND="PGVECTOR"` to keep embeddings in PostgreSQL. On startup,
the application enables the `vector` extension and creates a collection table
whose vector dimension matches the active embedding model. The index is created
once the number of records reaches `VECTOR_DB_PGVEC_INDEX_THRESHOLD`.

`QDRANT` remains selectable through the same setting. Embedding calls are now
batched and vector-store operations are asynchronous for both providers.

## 21. Containerized Deployment and Monitoring

The Docker stack runs the FastAPI application behind Nginx, provisions PGVector
and Qdrant, and exposes Prometheus metrics for Grafana dashboards. Copy the
files under `docker/env/` from their `.env.example.*` templates before starting
the stack.

The application container accepts the same `LLM_MODE` profile switch. Use a
cloud key, a host Ollama URL (`http://host.docker.internal:11434/v1` on macOS),
or a Colab/ngrok URL. See [docker/README.md](docker/README.md) for deployment
steps and [the Ollama guide](docs/OLLAMA_LOCAL_AND_COLAB.md) for the profile
configuration.

### Prepare Docker environment files

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd docker/env
cp -n .env.example.app .env.app
cp -n .env.example.postgres .env.postgres
cp -n .env.example.postgres-exporter .env.postgres-exporter
cp -n .env.example.rabbitmq .env.rabbitmq
cp -n .env.example.redis .env.redis
cp -n .env.example.grafana .env.grafana

cd ../minirag
cp -n alembic.example.ini alembic.ini
```

Review the copied files and keep the PostgreSQL, RabbitMQ, and Redis passwords
consistent between their service files and `.env.app`.

### Start the complete Docker stack

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd docker
docker compose up -d --build
docker compose ps
```

The main URLs are:

- Nginx API: `http://localhost/api/v1/`
- Direct FastAPI API: `http://localhost:5001/api/v1/`
- FastAPI documentation: `http://localhost:5001/docs`
- Flower: `http://localhost:5555`
- RabbitMQ management: `http://localhost:15672`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Qdrant dashboard: `http://localhost:6333/dashboard`

### Inspect logs

Run from: **`RAGDocumentsIntelligence/docker/`**.

```bash
docker compose logs -f fastapi
docker compose logs -f celery-worker celery-beat flower
docker compose logs -f rabbitmq redis pgvector
```

### Stop the stack

Run from: **`RAGDocumentsIntelligence/docker/`**.

```bash
docker compose down
```

To also delete all persisted development data, use the following destructive
command only when a complete reset is intended:

Run from: **`RAGDocumentsIntelligence/docker/`**.

```bash
docker compose down -v --remove-orphans
```

## 22. Background Document Processing with Celery

The process endpoint now queues work instead of processing documents in the HTTP
request. RabbitMQ carries tasks and Redis stores task results. Copy
`docker/env/.env.example.rabbitmq` and `.env.example.redis` to their local
`.env.*` equivalents, then keep their credentials aligned with the Celery URLs
in `docker/env/.env.app`.

Start the worker separately after the broker and database services are ready:

Run from: **repository root** (`RAGDocumentsIntelligence/`).

```bash
cd src
conda run --no-capture-output -n rag python -m celery \
  -A celery_app.celery_app worker \
  --loglevel=INFO \
  --queues=default,file_processing,data_indexing,mail_service_queue \
  --pool=solo \
  --concurrency=1
```

The task worker uses the same `LLM_MODE` configuration as the API, so it can
process embeddings with Ollama, Colab/ngrok, or the cloud profile.

On macOS, `--pool=solo` avoids multiprocessing issues. Confirm that the active
Conda interpreter provides the standard `lzma` module before starting Celery:

Run from: **`RAGDocumentsIntelligence/src/`** with the `rag` environment active.

```bash
conda run --no-capture-output -n rag python \
  -c "import sys, lzma; print(sys.executable)"
```

The `GET /api/v1/send_reports` endpoint submits the report simulation to
`mail_service_queue` and immediately returns its Celery `task_id`; the worker
continues the work without blocking FastAPI.

### Troubleshoot a `FAILURE` state in Flower

- `relation "celery_task_executions" does not exist`: run `alembic upgrade
  head` from `src/models/db_schemes/minirag/` before submitting a new task.
- `no_file_found_with_this_id`: use the same numeric `project_id` used during
  upload and copy the returned `file_id` exactly into the processing request.
- Do not combine FastAPI running in Docker with a Celery worker running on the
  host. Uploaded files live in a Docker volume that the local worker cannot
  read. Run both application processes locally, or run both with Compose.
- A failed task is historical and remains red in Flower. Submit a new request
  after fixing the cause and verify the state of the new `task_id`.

## 23. Celery Workflows, Beat, and Flower

The Docker stack now starts separate Celery worker and Beat services, plus the
Flower dashboard on port `5555`. Workflow tasks coordinate document processing
and vector indexing; execution records are stored through new Alembic
migrations, and scheduled maintenance removes old task records.

After copying `docker/env/.env.example.app`, set a strong
`CELERY_FLOWER_PASSWORD`. The Celery workers inherit the same Ollama/Cloud
profile selection as the API container.

## Project Principles

- **Configuration outside code**: secrets and machine-specific values stay in `.env`.
- **Pinned versions**: the environment is reproducible.
- **Incremental delivery**: each numbered branch adds one focused responsibility.
