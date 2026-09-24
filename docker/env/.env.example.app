APP_NAME="RAG Document Intelligence"
APP_VERSION="0.1"

FILE_ALLOWED_TYPES='["text/plain", "application/pdf"]'
FILE_MAX_SIZE=10
FILE_DEFAULT_CHUNK_SIZE=512000

POSTGRES_USERNAME="postgres"
POSTGRES_PASSWORD="postgres_password"
POSTGRES_HOST="pgvector"
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE="minirag"

# Select one LLM profile. CLOUD is the safe container default: set its key in
# docker/env/.env.app, which is ignored by Git.
LLM_MODE="CLOUD"

# For Ollama running on the Docker host (macOS), use host.docker.internal.
# For Colab, replace the URL with the ngrok HTTPS URL followed by /v1.
OLLAMA_API_URL="http://host.docker.internal:11434/v1"
OLLAMA_GENERATION_MODEL_ID="llama3.2"
OLLAMA_EMBEDDING_MODEL_ID="nomic-embed-text"
OLLAMA_EMBEDDING_MODEL_SIZE=768

# Required only when LLM_MODE="CLOUD". Never commit a real key.
CLOUD_OPENAI_API_KEY=""
CLOUD_OPENAI_API_URL=""
CLOUD_GENERATION_MODEL_ID="gpt-4.1-mini"
CLOUD_EMBEDDING_MODEL_ID="text-embedding-3-small"
CLOUD_EMBEDDING_MODEL_SIZE=1536
GENERATION_MODEL_ID_LITERAL='["gpt-4.1-mini", "llama3.2"]'

INPUT_DAFAULT_MAX_CHARACTERS=1024
GENERATION_DAFAULT_MAX_TOKENS=200
GENERATION_DAFAULT_TEMPERATURE=0.1

VECTOR_DB_BACKEND_LITERAL='["QDRANT", "PGVECTOR"]'
VECTOR_DB_BACKEND="PGVECTOR"
VECTOR_DB_PATH="qdrant_db"
VECTOR_DB_DISTANCE_METHOD="cosine"
VECTOR_DB_PGVEC_INDEX_THRESHOLD=100

PRIMARY_LANG="en"
DEFAULT_LANG="en"
