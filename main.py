from fastapi import FastAPI

# FastAPI is the HTTP entry point of RAG Document Intelligence. Future steps
# will add document ingestion, semantic search and answer-generation routes.
app = FastAPI(
    title="RAG Document Intelligence",
    version="0.1.0",
)


@app.get("/welcome", tags=["health"])
def welcome() -> dict[str, str]:
    """Return a minimal health response to validate that the API is running."""
    return {
        "message": "RAG Document Intelligence API is running."
    }
