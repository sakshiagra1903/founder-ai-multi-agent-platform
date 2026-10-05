import fitz  # PyMuPDF
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class PDFService:
    def extract_text(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extracts text from a PDF file.
        Returns a list of dicts containing page number and page content.
        E.g., [{"page_number": 1, "content": "..."}]
        """
        pages_data = []
        try:
            # Open PDF document
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF at {file_path}: {str(e)}")
            raise ValueError(f"Corrupted or invalid PDF file: {str(e)}")

        try:
            for page_idx, page in enumerate(doc):
                # Page numbers in user-facing context are usually 1-indexed
                page_num = page_idx + 1
                text = page.get_text()
                
                # Clean text: remove redundant whitespaces/newlines
                clean_text = " ".join(text.split())
                
                if clean_text:
                    pages_data.append({
                        "page_number": page_num,
                        "content": clean_text
                    })
                else:
                    logger.warning(f"Empty page or failed extraction on page {page_num} of {file_path}")
            
            doc.close()
        except Exception as e:
            logger.error(f"Error reading pages from PDF at {file_path}: {str(e)}")
            raise ValueError(f"Failed to read PDF pages: {str(e)}")

        if not pages_data:
            raise ValueError("No text could be extracted from the PDF file. It might be empty or scanned.")

        return pages_data

pdf_service = PDFService()
