# 05 — Document Processing for RAG Document Intelligence

RAG Document Intelligence is a document-grounded Retrieval-Augmented Generation (RAG) system. This stage turns uploaded TXT and PDF documents into metadata-preserving, overlapping chunks ready for vector indexing.

## 1. Architecture

```text
HTTP Client → FastAPI → Document upload → Processing → Chunks → Vector database → LLM
```

## 2. Prerequisites and Environment

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
cd src
pip install -r requirements.txt
cp .env.example .env
```

Python 3.8+ and [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install) are recommended. `.env` is local and Git-ignored; `.env.example` documents safe defaults.

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
```

## 3. Start the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/api/v1/
```

`main.py` loads configuration through `python-dotenv` and registers versioned routers under `/api/v1`.

## 4. Upload a Document

```bash
curl -F "file=@document.pdf" http://127.0.0.1:8000/api/v1/data/upload/demo-project
```

The upload endpoint validates MIME type and size, sanitizes the filename, and stores runtime files under `src/assets/files/`.

## 5. Process the Document

Call `POST /api/v1/data/process/{project_id}` with the returned `file_id`:

```json
{
  "file_id": "uploaded-file-id.pdf",
  "chunk_size": 500,
  "overlap_size": 50
}
```

The TXT/PDF loader preserves source metadata. `chunk_size` is the maximum fragment size; `overlap_size` repeats previous context to avoid losing meaning at chunk boundaries.

## 6. Test with Postman

Import `src/assets/rag-document-intelligence.postman_collection.json`, set `api` to `http://127.0.0.1:8000`, then run `API configuration endpoint`, `Upload document`, and `Process document` in order.

## Project Principles

- Keep secrets and local configuration in `.env`.
- Pin dependencies for reproducible environments.
- Deliver one focused responsibility per numbered branch.
