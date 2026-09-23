"""Request validation for document-processing endpoints."""

from pydantic import BaseModel, Field, model_validator


class ProcessRequest(BaseModel):
    """Parameters that control how one uploaded file is chunked."""

    file_id: str | None = Field(default=None, min_length=1)
    chunk_size: int = Field(default=500, ge=1, le=10_000)
    overlap_size: int = Field(default=50, ge=0)
    do_reset: bool = False

    @model_validator(mode="after")
    def validate_overlap(self) -> "ProcessRequest":
        """An overlap equal to a chunk size would prevent splitter progress."""
        if self.overlap_size >= self.chunk_size:
            raise ValueError("overlap_size must be smaller than chunk_size")
        return self
