"""Read uploaded documents and split their content into overlapping chunks."""

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models import ProcessingExtension

from .BaseController import BaseController
from .ProjectController import ProjectController


class ProcessController(BaseController):
    """Prepare project documents for later embedding and vector indexing."""

    def __init__(self, project_id: str) -> None:
        super().__init__()
        self.project_path = ProjectController().get_project_path(project_id)

    def get_file_path(self, file_id: str) -> Path:
        """Resolve one stored filename while keeping access inside its project folder."""
        file_path = (self.project_path / Path(file_id).name).resolve()
        if self.project_path.resolve() not in file_path.parents or not file_path.is_file():
            raise FileNotFoundError("The requested file does not exist in this project")
        return file_path

    def get_file_loader(self, file_id: str) -> TextLoader | PyMuPDFLoader:
        """Choose a loader based on the server-side filename extension."""
        file_path = self.get_file_path(file_id)
        extension = file_path.suffix.lower()
        if extension == ProcessingExtension.TXT.value:
            return TextLoader(str(file_path), encoding="utf-8")
        if extension == ProcessingExtension.PDF.value:
            return PyMuPDFLoader(str(file_path))
        raise ValueError(f"Unsupported document extension: {extension or 'none'}")

    def get_file_content(self, file_id: str) -> list[Document]:
        """Load every page or text segment exposed by the selected loader."""
        return self.get_file_loader(file_id).load()

    @staticmethod
    def process_file_content(
        file_content: list[Document],
        chunk_size: int = 100,
        overlap_size: int = 20,
    ) -> list[Document]:
        """Split text into overlapping chunks while preserving source metadata."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
        )
        return splitter.split_documents(file_content)
