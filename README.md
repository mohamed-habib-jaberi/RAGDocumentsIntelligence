# RAG Document Intelligence

RAG Document Intelligence is a document-grounded Retrieval-Augmented Generation
(RAG) platform. It ingests TXT and PDF files, processes them into chunks,
indexes their embeddings, retrieves relevant context, and generates answers
with either Ollama or a cloud OpenAI-compatible provider.

This `main` branch is the complete, cumulative application. Each numbered
branch is a tutorial checkpoint that introduces one capability.

For a detailed French walkthrough of the components and complete RAG pipeline,
see [Architecture détaillée](docs/ARCHITECTURE_FR.md).

## Architecture

```text
Client
  │
  ▼
FastAPI API ──► Celery workflows ──► RabbitMQ / Redis
  │                    │
  │                    ├── PostgreSQL + PGVector
  │                    └── Qdrant (optional vector backend)
  │
  └── LLM profile: Ollama local / Ollama Colab-ngrok / Cloud
```

## Capabilities

- FastAPI endpoints for uploading, processing, indexing, searching, and
  answering questions about documents.
- PostgreSQL persistence, Alembic migrations, and PGVector or Qdrant for
  semantic retrieval.
- Switchable LLM profiles: local Ollama, Ollama served from Google Colab through
  ngrok, or a cloud OpenAI-compatible service.
- Celery workers, RabbitMQ, Redis, scheduled maintenance, and Flower task
  monitoring.
- Docker deployment with Nginx, Prometheus, and Grafana.

## Quick Start: Local Development

### 1. Install dependencies

Use Python 3.10 or later, then create an isolated environment:

```bash
conda create -n rag-document-intelligence python=3.10
conda activate rag-document-intelligence
cd src
pip install -r requirements.txt
```

### 2. Create local configuration

```bash
cp .env.example .env
```

`src/.env` is personal and ignored by Git. Store API keys, passwords, and an
ngrok URL only there. `src/.env.example` is the safe, versioned template.

### 3. Choose the LLM profile

For Ollama on the Mac:

```env
LLM_MODE="OLLAMA"
OLLAMA_API_URL="http://localhost:11434/v1"
```

For Colab, keep `LLM_MODE="OLLAMA"` and replace the URL with the HTTPS ngrok
address followed by `/v1`. For a cloud provider:

```env
LLM_MODE="CLOUD"
CLOUD_OPENAI_API_KEY="your-key-kept-only-in-.env"
```

See [the Ollama local and Colab guide](docs/OLLAMA_LOCAL_AND_COLAB.md) for
model downloads, notebook usage, and ngrok setup.

### 4. Start infrastructure

For PostgreSQL/PGVector, RabbitMQ, Redis, and the other services, create the
Docker environment files from their templates:

```bash
cd ../docker/env
cp .env.example.app .env.app
cp .env.example.postgres .env.postgres
cp .env.example.rabbitmq .env.rabbitmq
cp .env.example.redis .env.redis
cp .env.example.grafana .env.grafana
cp .env.example.postgres-exporter .env.postgres-exporter
```

Edit these local files so the RabbitMQ, Redis, Celery, and LLM values agree,
then start the stack:

```bash
cd ..
docker compose up --build -d
```

The Docker guide contains deployment, monitoring, and troubleshooting details:
[docker/README.md](docker/README.md).

### 5. Run database migrations

For a local development run, copy the Alembic template then apply migrations:

```bash
cd src/models/db_schemes/minirag
cp alembic.ini.example alembic.ini
# Set sqlalchemy.url in alembic.ini
alembic upgrade head
```

### 6. Start the API and workers

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In separate terminals, start the task worker, scheduler, and Flower dashboard:

```bash
cd src
python -m celery -A celery_app worker --queues=default,file_processing,data_indexing --loglevel=info
python -m celery -A celery_app beat --loglevel=info
python -m celery -A celery_app flower --conf=flowerconfig.py
```

Useful local endpoints:

- API: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Flower: `http://localhost:5555`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Configuration Principles

- Never commit real values in `.env`, `docker/env/.env.*`, or `alembic.ini`.
- Copy each `.env.example` file to its local counterpart before running a
  service.
- Change `LLM_MODE` rather than application code when switching Ollama and
  cloud LLM environments.
- Select `VECTOR_DB_BACKEND="PGVECTOR"` or `"QDRANT"` according to the desired
  vector backend.

## Tutorial Branch Roadmap

| Branch | Capability |
| --- | --- |
| `01-architecture` | Project architecture and configuration foundation |
| `02-fastapi-foundation` | First FastAPI endpoint |
| `03-configured-api-routes` | Versioned modular routes |
| `04-document-upload-foundation` | Document upload workflow |
| `05-document-processing` | TXT/PDF chunk processing |
| `06-mongodb-persistence` | Initial persistence tutorial checkpoint |
| `07-asset-tracking` | Uploaded-file asset tracking |
| `08-llm-provider-abstraction` | OpenAI and Cohere provider abstraction |
| `09-qdrant-vector-store` | Qdrant vector storage |
| `10-llm-answer-generation` | Retrieval and LLM answer generation |
| `11-rag-answer-generation-checkpoint` | RAG flow review checkpoint |
| `12-rag-template-and-route-fixes` | RAG prompt and route fixes |
| `13-postgresql-sqlalchemy-migration` | PostgreSQL, SQLAlchemy, and Alembic |
| `13b-ollama-local-and-colab` | Ollama local/Colab-ngrok and cloud switching |
| `14-pgvector-vector-store` | PGVector backend and asynchronous vector operations |
| `15-containerized-deployment-and-observability` | Docker deployment, Nginx, Prometheus, and Grafana |
| `16-background-document-processing` | Celery, RabbitMQ, and Redis processing queue |
| `17-celery-workflows-and-monitoring` | Celery workflows, Beat, Flower, and task tracking |

## Project Principles

- Configuration stays outside source code.
- Dependencies are pinned for reproducible environments.
- Each tutorial branch adds one focused capability; `main` combines them all.
