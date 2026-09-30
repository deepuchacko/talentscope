import io
from pathlib import Path

from .exceptions import EmptyFileError, UnreadableFileError


def parse_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
    except Exception as exc:
        raise UnreadableFileError(f"Could not read PDF: {exc}") from exc

    if not text:
        raise EmptyFileError("The uploaded PDF contains no extractable text.")
    return text


def parse_docx(data: bytes) -> str:
    try:
        import docx

        doc = docx.Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
    except Exception as exc:
        raise UnreadableFileError(f"Could not read Word document: {exc}") from exc

    if not text:
        raise EmptyFileError("The uploaded Word document contains no text.")
    return text


def parse_file(path: Path) -> str:
    data = path.read_bytes()
    if not data:
        raise EmptyFileError(f"The file '{path.name}' is empty.")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(data)
    if suffix in (".docx", ".doc"):
        return parse_docx(data)
    raise UnreadableFileError(
        f"Unsupported file type '{suffix}'. Please upload a PDF or Word document."
    )


def parse_resume_input(text: str | None, file_path: Path | None) -> str:
    """Return resume text from either a plain-text string or a file."""
    if file_path is not None:
        return parse_file(file_path)
    if text:
        return text.strip()
    raise EmptyFileError("No resume content was provided.")
