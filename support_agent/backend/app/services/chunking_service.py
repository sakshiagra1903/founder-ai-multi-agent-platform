import uuid
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

class ChunkingService:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def create_chunks(self, pages_data: List[Dict[str, any]], document_id: str) -> List[Dict[str, any]]:
        """
        Splits extracted page contents into chunks.
        Keeps track of the source page number and builds custom chunk_ids.
        Returns:
            List[Dict]: [
                {
                    "chunk_id": "doc_id_p1_0",
                    "document_id": "...",
                    "page_number": 1,
                    "content": "..."
                }
            ]
        """
        chunks = []
        for page in pages_data:
            page_num = page["page_number"]
            text_content = page["content"]
            
            # Split the content of the individual page
            split_texts = self.splitter.split_text(text_content)
            
            for idx, chunk_text in enumerate(split_texts):
                chunk_uuid = f"{document_id}_p{page_num}_c{idx}"
                chunks.append({
                    "chunk_id": chunk_uuid,
                    "document_id": document_id,
                    "page_number": page_num,
                    "content": chunk_text
                })
        
        return chunks

chunking_service = ChunkingService()
