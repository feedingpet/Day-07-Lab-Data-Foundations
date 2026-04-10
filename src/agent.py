from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve top-k relevant chunks
        results = self.store.search(question, top_k=top_k)
        
        # 2. Build context and prompt (Lấy content thay vì text)
        context_parts = [res.get("content", "") for res in results]
        context_text = "\n\n---\n\n".join(context_parts)
        
        prompt = (
            "Bạn là một sử học gia. Tài liệu gồm lịch sử, tiểu sử và đặc biệt là di sản văn học, tư tưởng của các vị vua và nhân vật lịch sử thời Trần, kéo dài sang cả thời Hồ và thời kỳ kháng chiến chống Minh. Hãy cung cấp chính xác các thông tin liên quan đến nội dung trên\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        
        # 3. Call LLM
        return self.llm_fn(prompt)