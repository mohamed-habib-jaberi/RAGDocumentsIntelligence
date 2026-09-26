"""Create the FastAPI application and coordinate its service lifecycle."""

from fastapi import FastAPI
app = FastAPI()

@app.get("/welcome")
def welcome():
    """Return API metadata and the currently active backend configuration."""
    return {
        "message": "Hello World!"
    }
