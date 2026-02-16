"""CV text extraction from PDF, DOCX, and Markdown files."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader


class CVParser:
    """Extracts plain text from CV files (PDF, DOCX, Markdown)."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md"}

    def extract_text(self, file_path: str) -> str:
        """Extract plain text from a CV file based on its extension."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(path)
        elif ext == ".docx":
            return self._extract_docx(path)
        elif ext == ".md":
            return self._extract_markdown(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def extract_text_from_bytes(self, content: bytes, filename: str) -> str:
        """Extract text from in-memory bytes. Writes to temp file if needed."""
        import tempfile

        ext = Path(filename).suffix.lower()

        if ext == ".md":
            return content.decode("utf-8", errors="replace")

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            return self.extract_text(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()

    @staticmethod
    def _extract_docx(path: Path) -> str:
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs).strip()

    @staticmethod
    def _extract_markdown(path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()
