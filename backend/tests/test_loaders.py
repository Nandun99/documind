import pytest

from app.services.chunking import split_documents
from app.services.loaders import EmptyDocumentError, UnsupportedFileType, load_file
from tests.helpers import make_pdf


def test_load_text_file(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("Hello world. This is a note.")
    docs = load_file(path, "notes.txt")
    assert len(docs) == 1
    assert docs[0].metadata == {"source": "notes.txt", "page": 1}


def test_load_pdf_keeps_page_numbers(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(make_pdf(["First page about revenue", "Second page about costs"]))
    docs = load_file(path, "report.pdf")
    assert [d.metadata["page"] for d in docs] == [1, 2]
    assert "costs" in docs[1].page_content



def test_unsupported_and_empty_files(tmp_path):
    path = tmp_path / "image.png"
    path.write_bytes(b"\x89PNG")
    with pytest.raises(UnsupportedFileType):
        load_file(path, "image.png")
    empty = tmp_path / "empty.txt"
    empty.write_text("   \n  ")
    with pytest.raises(EmptyDocumentError):
        load_file(empty, "empty.txt")


def test_split_documents_adds_chunk_index(tmp_path):
    path = tmp_path / "long.txt"
    path.write_text(" ".join(f"Sentence number {i}." for i in range(200)))
    chunks = split_documents(load_file(path, "long.txt"), chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 5
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert all(len(c.page_content) <= 200 for c in chunks)
