import pytest

from app.services.extraction import doc_type, extract_text
from conftest import KEY_PHRASE


def test_txt_happy_path(txt_file) -> None:
    text = extract_text(txt_file.name, txt_file.read_bytes())
    assert KEY_PHRASE in text


def test_pptx_happy_path(pptx_file) -> None:
    text = extract_text(pptx_file.name, pptx_file.read_bytes())
    assert KEY_PHRASE in text
    assert "chlorophyll" in text.lower()


def test_docx_happy_path(docx_file) -> None:
    text = extract_text(docx_file.name, docx_file.read_bytes())
    assert KEY_PHRASE in text


def test_pdf_happy_path(pdf_data) -> None:
    text = extract_text("sample.pdf", pdf_data)
    assert KEY_PHRASE in text


def test_newline_normalization(tmp_path) -> None:
    raw = ("Photosynthesis converts light\r\nenergy into chemical.\r\n\r\n\r\n\r\nIt happens in leaves.   ")
    path = tmp_path / "messy.txt"
    path.write_bytes(raw.encode("utf-8"))
    text = extract_text(path.name, path.read_bytes())
    assert "\r" not in text
    assert "\n\n\n" not in text
    assert text.endswith("It happens in leaves.")


def test_unsupported_extension_raises() -> None:
    with pytest.raises(ValueError):
        extract_text("malware.exe", b"MZfakebinary")


def test_empty_bytes_txt_raises() -> None:
    with pytest.raises(ValueError):
        extract_text("empty.txt", b"")


def test_whitespace_only_txt_raises() -> None:
    with pytest.raises(ValueError):
        extract_text("blank.txt", b"   \n\n  \t ")


def test_too_short_content_raises() -> None:
    with pytest.raises(ValueError):
        extract_text("tiny.txt", b"hi")


def test_no_extension_raises() -> None:
    with pytest.raises(ValueError):
        extract_text("README", b"some long enough content here")


def test_doc_type_values() -> None:
    assert doc_type("deck.pptx") == "pptx"
    assert doc_type("REPORT.PDF") == "pdf"
    assert doc_type("/a/b/notes.docx") == "docx"
    assert doc_type("plain.txt") == "txt"
