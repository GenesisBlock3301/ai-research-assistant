from sqlalchemy.orm import Session
from app.db.models import Document
from app.services import EmbeddingService
from app.services.vector_store import VectorStorage
from app.utils import load_pdf
import re


class IngestionService:

    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStorage(db)
        self.embedding_service = EmbeddingService()

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove extra whitespace, line breaks, and non-printable characters."""
        text = re.sub(r'\s+', ' ', text)  # collapse whitespace
        text = re.sub(r'[^\x20-\x7E\n]+', ' ', text)  # remove weird chars
        return text.strip()

    @staticmethod
    def chunk_text(text: str, max_chunk_size: int = 500):
        """
        Break text into chunks of roughly max_chunk_size words.
        Keeps semantic boundaries by splitting on sentence endings where possible.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, current_chunk = [], []

        for sentence in sentences:
            if len(" ".join(current_chunk + [sentence]).split()) > max_chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
            else:
                current_chunk.append(sentence)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return [c.strip() for c in chunks if len(c.strip()) > 0]

    def ingest_pdf(self, file_path: str, title: str, owner_id: int):
        doc = Document(title=title, owner_id=owner_id)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        # Extract and clean text
        raw_text = load_pdf(file_path)
        clean_text = self.clean_text(raw_text)

        # Chunk into meaningful sections
        chunks = self.chunk_text(clean_text, max_chunk_size=500)
        print(f"[Ingestion] Extracted {len(chunks)} chunks from PDF: {title}")

        # Embed and store each chunk
        for idx, chunk in enumerate(chunks):
            embedding = self.embedding_service.embed_texts([chunk])[0]
            self.vector_store.insert_chunk(
                document_id=doc.id,
                chunk_text=chunk,
                embedding=embedding,
                start_pos=0,
                end_pos=len(chunk),
                tokens=len(chunk.split()),
                metadata={
                    "title": title,
                    "chunk_index": idx,
                },
            )

        print(f"[Ingestion] Successfully ingested '{title}' with {len(chunks)} chunks.")
        return doc
