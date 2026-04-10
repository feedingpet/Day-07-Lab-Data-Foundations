from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

SAMPLE_FILES = [
    "data/TRẦN ANH TÔNG.md",
    "data/TRẦN CẢNH.md",
    "data/TRẦN HẠO.md",
    "data/TRẦN KÍNH.md",
    "data/TRẦN MẠNH.md",
    "data/TRẦN MINH TÔNG.md",
    "data/TRẦN NGẠC.md",
    "data/Trần Nghệ Tông.md",
    "data/TRẦN NHÂN TÔNG.md",
    "data/NIÊN BIỀU KHÁI QUÁT CÁC SỰ KIỆN CÓ LIÊN QUAN TỚI VĂN HỌC.md" 
]

def load_documents_from_files(file_paths: list[str], chunker=None) -> list[Document]:
    """Load documents from file paths and apply chunking if provided."""
    allowed_extensions = {".md", ".txt"}
    documents: list[Document] = []

    for raw_path in file_paths:
        path = Path(raw_path)

        if path.suffix.lower() not in allowed_extensions:
            continue

        if not path.exists() or not path.is_file():
            print(f"Skipping missing file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        
        # Áp dụng Chunking ở đây
        if chunker:
            chunks = chunker.chunk(content)
            for i, chunk_text in enumerate(chunks):
                documents.append(
                    Document(
                        id=f"{path.stem}_chunk_{i}",
                        content=chunk_text,
                        metadata={
                            "source": str(path), 
                            "extension": path.suffix.lower(),
                            "chunk_index": i
                        },
                    )
                )
        else:
            documents.append(
                Document(
                    id=path.stem,
                    content=content,
                    metadata={"source": str(path), "extension": path.suffix.lower()},
                )
            )

    return documents


def demo_llm(prompt: str) -> str:
    """A simple mock LLM for manual RAG testing."""
    preview = prompt[:400].replace("\n", " ")
    return f"[DEMO LLM] Generated answer from prompt preview: {preview}..."


def run_manual_demo(question: str | None = None, sample_files: list[str] | None = None) -> int:
    files = sample_files or SAMPLE_FILES
    query = question or "Trần Kính (Duệ Tông) là con ai và làm vua bao nhiêu năm?"

    print("=== BẮT ĐẦU KIỂM TRA CHUNKING ===")
    print(f"Câu hỏi (Query): {query}\n")

    # Khởi tạo Embedder
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            embedder = LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    elif provider == "openai":
        try:
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    # Định nghĩa 3 chiến lược chunking
    chunking_strategies = {
        "FixedSize (Size: 500, Overlap: 50)": FixedSizeChunker(chunk_size=500, overlap=50),
        "Sentence (Max: 3 sentences)": SentenceChunker(max_sentences_per_chunk=3),
        "Recursive (Size: 500)": RecursiveChunker(chunk_size=500)
    }

    # Lặp qua từng chiến lược để test
    for strategy_name, chunker in chunking_strategies.items():
        print(f"\n" + "="*60)
        print(f"CHIẾN LƯỢC: {strategy_name}")
        print("="*60)

        # 1. Load và Cắt văn bản
        docs = load_documents_from_files(files, chunker=chunker)
        print(f"-> Đã chia thành {len(docs)} chunks.")

        # 2. Tạo Vector Store mới (để tránh lẫn lộn data giữa các chiến lược)
        safe_collection_name = f"store_{strategy_name.split()[0].lower()}"
        store = EmbeddingStore(collection_name=safe_collection_name, embedding_fn=embedder)
        store.add_documents(docs)

        # 3. Tìm kiếm
        search_results = store.search(query, top_k=3)
        print(f"\n[+] TOP 3 CHUNKS LIÊN QUAN NHẤT:")
        for index, result in enumerate(search_results, start=1):
            score = result.get('score', 0.0)
            source = result['metadata'].get('source', 'Unknown')
            preview = result['content'][:150].replace(chr(10), ' ')
            print(f"   {index}. Score: {score:.3f} | Nguồn: {source}")
            print(f"      Nội dung: {preview}...")

        # 4. Trả lời bằng Agent
        agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
        answer = agent.answer(query, top_k=3)
        print(f"\n[+] CÂU TRẢ LỜI TỪ AGENT:")
        print(answer)

    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else None
    return run_manual_demo(question=question)


if __name__ == "__main__":
    raise SystemExit(main())