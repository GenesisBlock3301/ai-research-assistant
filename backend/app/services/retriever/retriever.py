import numpy as np
from langchain_core.documents import Document as LCDocument
from langchain.schema import BaseRetriever
from pydantic import Field

from app.services import EmbeddingService
from app.services.vector_store import VectorStorage


class PostgresRetriever(BaseRetriever):
    """
    Retriever for fetching relevant document chunks from Postgres + pgvector.
    """

    vector_storage: VectorStorage = Field(...)
    embedding_service: EmbeddingService = Field(...)
    owner_id: int = Field(None)
    k: int = Field(default=5)
    metadata_filter: dict = Field(default_factory=dict)
    similarity_threshold: float = Field(default=0.5)

    def filter_relevant_chunks(self, query_emb, chunks):
        """
        Filter chunks by metadata and cosine similarity.
        """

        def is_metadata_match(chunk):
            if not self.metadata_filter:
                return True
            if not chunk.meta_info:
                return False
            return all(chunk.meta_info.get(k) == v for k, v in self.metadata_filter.items())

        def cosine_similarity(a, b):
            a, b = np.array(a), np.array(b)
            if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
                return 0.0
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        relevant = []
        for chunk in chunks:
            if not is_metadata_match(chunk):
                continue
            sim = cosine_similarity(query_emb, chunk.embedding)
            print(f"[DEBUG] Chunk ID: {chunk.document_id}, similarity: {sim}")
            if sim >= self.similarity_threshold:
                relevant.append(chunk)

        return relevant

    def _get_relevant_documents(self, query: str, run_manager=None):
        query_emb = self.embedding_service.embed_texts([query])[0]
        print(f"[DEBUG] Query embedding generated: {query_emb[:5]} ...")

        chunks = self.vector_storage.search(
            query_emb, k=self.k, owner_id=self.owner_id
        )
        print(f"[DEBUG] Chunks retrieved from vector store: {len(chunks)}")
        chunks = self.filter_relevant_chunks(query_emb, chunks)
        print(f"[DEBUG] Chunks after filtering: {len(chunks)}")
        docs = [
            LCDocument(
                page_content=chunk.chunk_text,
                metadata={"doc_id": chunk.document_id, **(chunk.meta_info or {})}
            )
            for chunk in chunks
        ]
        return docs

    def invoke(self, query: str):
        return self._get_relevant_documents(query)
