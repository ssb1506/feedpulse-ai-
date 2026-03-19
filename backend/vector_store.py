"""
Vector Store — FAISS-based in-memory vector store for semantic search over posts.
Used by the AI agent to find relevant posts when answering questions.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import threading


class VectorStore:
    """In-memory FAISS vector store for social media posts."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print("[VectorStore] Loading embedding model...")
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # all-MiniLM-L6-v2 output dimension

        # FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)

        # Parallel list to store post metadata (FAISS only stores vectors)
        self.posts: list[dict] = []
        self._lock = threading.Lock()

        print("[VectorStore] Ready")

    def add_post(self, post: dict):
        """Embed a post and add to the index."""
        text = f"{post['username']}: {post['text']}"
        embedding = self.model.encode([text])[0].astype(np.float32)

        with self._lock:
            self.index.add(np.array([embedding]))
            self.posts.append(post)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search — find posts most similar to the query."""
        if self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode([query])[0].astype(np.float32)

        with self._lock:
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(np.array([query_embedding]), k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.posts):
                    post = self.posts[idx].copy()
                    post["relevance_score"] = round(1.0 / (1.0 + float(distances[0][i])), 3)
                    results.append(post)

        return results

    def get_count(self) -> int:
        """Number of posts in the vector store."""
        return self.index.ntotal
