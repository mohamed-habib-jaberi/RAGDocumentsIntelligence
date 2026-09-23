# 04 — Document Upload Foundation for RAG Document Intelligence

This stage establishes the application structure and the first document-ingestion workflow for RAG Document Intelligence.

## 1. Architecture

```text
HTTP Client → FastAPI → Upload validation → Project storage → Future processing and indexing
```

## 2. Setup

Python 3.8+ and [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install) are recommended.

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
cd src
pip install -r requirements.txt
cp .env.example .env
```

`.env` is local and Git-ignored. Configure the application and upload limits there:

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
FILE_ALLOWED_TYPES='["text/plain", "application/pdf"]'
FILE_MAX_SIZE=10
FILE_DEFAULT_CHUNK_SIZE=524288
```

## 3. Application Structure

The executable application is now contained in `src/`. Controllers own filesystem rules, routes expose HTTP endpoints, models define response contracts, and `assets/files/` stores runtime uploads.

## 4. Start the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/api/v1/
```

## 5. Upload a Document

```bash
curl -F "file=@document.pdf" http://127.0.0.1:8000/api/v1/data/upload/demo-project
```

`POST /api/v1/data/upload/{project_id}` accepts configured TXT and PDF MIME types, validates the file size during streaming, sanitizes client filenames, prevents path traversal, and writes files asynchronously to `src/assets/files/`.

Runtime documents are excluded through `src/assets/.gitignore`.

## 6. Test with Postman

Import `src/assets/rag-document-intelligence.postman_collection.json`, set `api` to `http://127.0.0.1:8000`, and run `API configuration endpoint` followed by `Upload document`.

## Project Principles

- Keep secrets outside source code.
- Pin dependencies for reproducible environments.
- Add one focused capability per numbered branch.
