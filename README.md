# 01 — Architecture and Initialization of RAG Document Intelligence

RAG Document Intelligence is a Retrieval-Augmented Generation (RAG) system for document-grounded question answering. This first stage establishes a reproducible environment and configuration contracts; no server or RAG pipeline runs yet.

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

- Python 3.8 or later;
- Conda or [Miniconda](https://docs.anaconda.com/free/miniconda/#quick-command-line-install), recommended for dependency isolation.

## 3. Create and Activate the Python Environment

```bash
conda create -n rag-document-intelligence python=3.8
conda activate rag-document-intelligence
```

Optionally, make the terminal prompt easier to read:

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Versions are pinned so all developers use compatible dependencies.

## 5. Configure the Environment

```bash
cp .env.example .env
```

`.env` is local and ignored by Git. It stores secrets, while `.env.example` documents required variables safely.

```env
APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"
OPENAI_API_KEY=""
```

## Project Principles

- Keep machine-specific settings and secrets in `.env`.
- Pin versions to make environments reproducible.
- Add one focused responsibility per numbered branch.
