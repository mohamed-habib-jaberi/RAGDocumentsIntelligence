# 02 — FastAPI Foundation for RAG Document Intelligence

This stage introduces the first HTTP entry point for RAG Document Intelligence. Later stages add document ingestion, semantic search, and answer generation.

## 1. Prerequisites and Setup

Use Python 3.8+ and preferably [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install).

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
pip install -r requirements.txt
cp .env.example .env
```

`.env` is local and Git-ignored. It contains environment-specific values such as API keys.

## 2. FastAPI Application

Start the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify the first endpoint:

```bash
curl http://127.0.0.1:8000/welcome
```

`main.py` exposes the application entry point and the `/welcome` endpoint confirms that FastAPI is running.

## 3. Postman Collection

Import `assets/rag-document-intelligence.postman_collection.json`, set `api` to `http://127.0.0.1:8000`, and run `Welcome endpoint`.

## Project Principles

- Keep secrets outside source code.
- Pin dependencies for reproducible environments.
- Add one focused capability per numbered branch.
