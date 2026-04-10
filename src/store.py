from __future__ import annotations

import uuid
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401
            
            self._use_chroma = True
            self._chroma_client = chromadb.Client()
            self._collection = self._chroma_client.get_or_create_collection(self._collection_name)
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        doc_id = getattr(doc, "id", str(uuid.uuid4()))
        text_content = getattr(doc, "content", getattr(doc, "text", str(doc)))
        metadata = dict(getattr(doc, "metadata", {}))
        
        # Fallback doc_id để phục vụ test xóa document
        if "doc_id" not in metadata:
            metadata["doc_id"] = doc_id
            
        return {
            "id": str(doc_id),
            "content": text_content,
            "metadata": metadata,
            "embedding": self._embedding_fn(text_content)
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_emb = self._embedding_fn(query)
        scored_records = []
        
        for record in records:
            score = _dot(query_emb, record["embedding"])
            scored_records.append((score, record))
            
        scored_records.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, rec in scored_records[:top_k]:
            res = rec.copy()
            res["score"] = score
            results.append(res)
            
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """
        for doc in docs:
            record = self._make_record(doc)
            
            if self._use_chroma and self._collection is not None:
                self._collection.add(
                    ids=[record["id"]],
                    documents=[record["content"]],
                    embeddings=[record["embedding"]],
                    metadatas=[record["metadata"]] if record["metadata"] else None
                )
            else:
                self._store.append(record)
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            ret = []
            if results and results.get("ids") and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    meta = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] else {}
                    dist = results["distances"][0][i] if results.get("distances") and results["distances"][0] else 0.0
                    ret.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": meta,
                        "score": 1.0 - dist # Convert distance to score
                    })
            ret.sort(key=lambda x: x["score"], reverse=True)
            return ret
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.
        """
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where=metadata_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            ret = []
            if results and results.get("ids") and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    meta = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] else {}
                    dist = results["distances"][0][i] if results.get("distances") and results["distances"][0] else 0.0
                    ret.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": meta,
                        "score": 1.0 - dist
                    })
            ret.sort(key=lambda x: x["score"], reverse=True)
            return ret
        else:
            filtered_records = self._store
            if metadata_filter:
                filtered_records = []
                for rec in self._store:
                    match = True
                    for k, v in metadata_filter.items():
                        if rec.get("metadata", {}).get(k) != v:
                            match = False
                            break
                    if match:
                        filtered_records.append(rec)
                        
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.
        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            initial_count = self._collection.count()
            self._collection.delete(where={"doc_id": doc_id})
            return self._collection.count() < initial_count
        else:
            initial_len = len(self._store)
            # Filter and keep only what DOES NOT match
            self._store = [rec for rec in self._store if rec.get("metadata", {}).get("doc_id") != doc_id]
            return len(self._store) < initial_len