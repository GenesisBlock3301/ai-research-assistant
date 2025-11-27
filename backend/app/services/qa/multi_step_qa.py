from typing import List, TypedDict

from app.config import settings
from app.db import Document
from app.services import LLaMAWrapper, EmbeddingService
from app.services.retriever import PostgresRetriever
from app.services.vector_store import VectorStorage


class State(TypedDict):
    query: str
    docs: List[Document]
    summary: str


def retrieve_documents(
        state: State,
        vector_storage: VectorStorage,
        owner_id: int,
        k: int = 5,
        similarity_threshold: float = 0.5
) -> State:
    retriever = PostgresRetriever(
        vector_storage=vector_storage,
        embedding_service=EmbeddingService(),
        owner_id=owner_id,
        k=k,
        similarity_threshold=similarity_threshold,
    )
    docs = retriever.invoke(state["query"])
    state["docs"] = docs
    print(f"[DEBUG] Retrieved {len(docs)} documents from vector store")
    return state


def summarize_documents(state: State) -> State:
    """
    Summarize retrieved documents using LLM.
    """
    llm = LLaMAWrapper(endpoint=settings.LLM_SERVER_URL)

    if state.get("docs"):
        context = "\n".join([d.page_content for d in state["docs"]])
        prompt = f"Summarize the following documents:\n{context}"
        summary = llm._call(prompt)
        state["summary"] = summary or ""
        print(f"[DEBUG] Summary generated: {state['summary'][:100]}...")  # first 100 chars
    else:
        state["summary"] = ""

    return state


def multiline_step_qa(
        query: str,
        db,
        owner_id: int,
        k: int = 5,
        similarity_threshold: float = 0.5
) -> State:
    state: State = {"query": query, "docs": [], "summary": ""}

    vector_storage = VectorStorage(db)

    state = retrieve_documents(
        state,
        vector_storage,
        owner_id=owner_id,
        k=k,
        similarity_threshold=similarity_threshold
    )

    if state["docs"]:
        state = summarize_documents(state)

    return state
