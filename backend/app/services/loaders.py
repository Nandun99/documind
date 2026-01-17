from pathlib import Path

from docx import Document as DocxDocument
from langchain_core.documents import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


class UnsupportedFileType(ValueError):
    pass


class EmptyDocumentError(ValueError):
    pass


def _read_pdf(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    return [(number, page.extract_text() or "") for number, page in enumerate(reader.pages, start=1)]


def _read_docx(path: Path) -> list[tuple[int, str]]:
    doc = DocxDocument(str(path))
    parts = [p.text for p in doc.paragraphs]
    return [(1, "\n".join(parts))]


def _read_text(path: Path) -> list[tuple[int, str]]:
    return [(1, path.read_text(encoding="utf-8", errors="replace"))]


def load_file(path: Path, filename: str) -> list[Document]:
    """Read a file into LangChain documents, one per page (PDF) or one for the whole file."""
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        pages = _read_pdf(path)
    elif extension == ".docx":
        pages = _read_docx(path)
    elif extension in (".txt", ".md"):
        pages = _read_text(path)
    else:
        raise UnsupportedFileType(f"Unsupported file type: {extension or 'unknown'}")

    documents = [
        Document(page_content=text.strip(), metadata={"source": filename, "page": number})
        for number, text in pages
        if text.strip()
    ]
    if not documents:
        raise EmptyDocumentError("No readable text found in the file")
    return documents
