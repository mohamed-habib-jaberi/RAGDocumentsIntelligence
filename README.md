# 13b — Ollama Local and Colab LLM Profiles for RAG Document Intelligence

RAG Document Intelligence is a Retrieval-Augmented Generation (RAG) system for document-grounded question answering. This stage adds a switchable Ollama profile for local macOS and Google Colab/ngrok deployments, while retaining the existing cloud-provider profile.

## 1. Target Architecture

```text
HTTP Client
    │
    ▼
FastAPI (project API)
    ├── LLM: answer generation
    ├── Embeddings: text vector representation
    ├── MongoDB: projects, files, and chunks
    └── Vector database: semantic search
```

## 2. Prerequisites

- Python 3.11 or later;
- Conda or [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install), recommended for dependency isolation.

## 3. Create and Activate the Python Environment

```bash
conda create -n rag python=3.11 -y
conda activate rag
```

Optionally, make the terminal prompt easier to read:

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## 4. Enter the Application Directory and Install Dependencies

```bash
cd src
pip install -r requirements.txt
```

Versions are pinned so every developer uses compatible dependencies. FastAPI defines routes, Uvicorn runs the application, and `python-multipart` supports file uploads.

## 5. Configure the Environment

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

## 6. Start MongoDB with Docker

```bash
cd ../docker
docker compose up -d
cd ../src
```

MongoDB is exposed locally on port `27007`. Data is stored in `docker/mongodb/`, a Git-ignored directory.

```env
MONGODB_URL="mongodb://localhost:27007"
MONGODB_DATABASE="rag_document_intelligence"
```

## 7. Load Configuration and Organize Routes

`main.py` loads `.env`, initializes the shared asynchronous PostgreSQL session
factory, and registers FastAPI routers. The base route is versioned under
`/api/v1`, allowing future API versions without breaking existing clients.

`GET /api/v1/` returns the application name and version defined in `.env`, confirming both API availability and configuration loading.

## 8. Start the FastAPI Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify the base endpoint:

```bash
curl http://127.0.0.1:8000/api/v1/
```

## 9. Upload a Document

`POST /api/v1/data/upload/{project_id}` accepts TXT and PDF files declared in `.env`. It validates MIME type and size, sanitizes the client filename, creates a project folder, and writes the file asynchronously under `src/assets/files/`.

```bash
curl -F "file=@document.pdf" http://127.0.0.1:8000/api/v1/data/upload/demo-project
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

Every successful upload now creates an `assets` collection record with the project ObjectId, server-side filename, file type, size, and upload timestamp. A compound index prevents two assets with the same filename in one project.

Processing can now target one `file_id` or omit it to process every asset belonging to the project. Each stored chunk references both its project and source asset.

## 12. Configure an LLM Provider

The provider layer separates application logic from vendor SDKs. Configure OpenAI, Cohere, or an OpenAI-compatible endpoint through `.env`, then select the generation and embedding models. The same interface exposes `generate_text` and `embed_text` to future RAG services.

## 13. Configure the Vector Store

Qdrant stores document embeddings for semantic retrieval. Configure the local path, provider, and distance method in `.env`. The provider abstraction can create collections, batch-insert vectors, and search nearest vectors without coupling application services to the Qdrant SDK.

## 14. Persist Projects and Chunks

The first upload creates a project in MongoDB's `projects` collection. Processing inserts chunk batches into `chunks`, including their text, metadata, order, and owning project ObjectId. With `do_reset: true`, existing project chunks are removed before the new insertion.

## 15. Test with Postman

Import `assets/rag-document-intelligence.postman_collection.json`, set `api` to `http://127.0.0.1:8000`, then run requests in order: `API configuration endpoint`, `Upload document`, and `Process document`.

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

```bash
docker compose up -d pgvector
cd ../src/models/db_schemes/minirag
cp alembic.ini.example alembic.ini
# Set sqlalchemy.url in alembic.ini, then run:
alembic upgrade head
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

## Project Principles

- **Configuration outside code**: secrets and machine-specific values stay in `.env`.
- **Pinned versions**: the environment is reproducible.
- **Incremental delivery**: each numbered branch adds one focused responsibility.
