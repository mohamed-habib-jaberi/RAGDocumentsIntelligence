# 03 — Configured API and Modular Routes for RAG Document Intelligence

This stage introduces a configured FastAPI application with versioned, modular routes.

## 1. Setup

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
pip install -r requirements.txt
cp .env.example .env
```

Python 3.8+ and [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install) are recommended. The local `.env` file keeps secrets out of Git.

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
```

## 2. Configuration and Routing

`main.py` loads `.env` through `python-dotenv` before registering routers. Version-one routes live below `/api/v1`, which makes future API versions possible without breaking existing clients.

`GET /api/v1/` returns the configured application name and version as a lightweight health check.

## 3. Start and Test the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/api/v1/
```

Import `assets/rag-document-intelligence.postman_collection.json`, set `api` to `http://127.0.0.1:8000`, then run `API configuration endpoint`.

## Project Principles

- Keep environment-specific settings outside source code.
- Pin dependencies for reproducible setups.
- Deliver one focused capability per numbered branch.
