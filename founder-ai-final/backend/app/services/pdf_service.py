import fitz  # PyMuPDF
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PDFService:
    """Extracts and cleans text from PDF resumes."""

    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract raw text from a PDF file."""
        try:
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text("text"))
            doc.close()
            raw = "\n".join(text_parts)
            return self._clean_text(raw)
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Remove noise, normalize whitespace."""
        # Remove non-printable characters
        text = re.sub(r"[^\x20-\x7E\n]", " ", text)
        # Collapse multiple spaces
        text = re.sub(r" {2,}", " ", text)
        # Collapse 3+ newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


pdf_service = PDFService()
