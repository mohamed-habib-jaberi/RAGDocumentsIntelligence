"""Expose the HTTP endpoints implemented by the nlp router."""

from pydantic import BaseModel
from typing import Optional

class PushRequest(BaseModel):
    """Validate the input fields accepted by the Push API operation."""
    do_reset: Optional[int] = 0

class SearchRequest(BaseModel):
    """Validate the input fields accepted by the Search API operation."""
    text: str
    limit: Optional[int] = 5
