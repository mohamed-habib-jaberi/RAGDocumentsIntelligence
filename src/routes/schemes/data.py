"""Expose the HTTP endpoints implemented by the data router."""

from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    """Validate the input fields accepted by the Process API operation."""
    file_id: str
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0
