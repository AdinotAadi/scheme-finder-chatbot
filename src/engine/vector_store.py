"""
vector_store.py - Self-contained, robust Qdrant Vector Store indexing and retrieval.

Stores scheme documents with rich metadata and supports semantic similarity search
and filtered retrieval directly in local embedded Qdrant DB ('data/qdrant_db').
"""

import sqlite3
import re
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)

QDRANT_PATH = "data/qdrant_db"
COLLECTION_NAME = "myscheme_schemes"
VECTOR_DIM = 256

def compute_text_embedding(text: str, dim: int = VECTOR_DIM) -> List[float]:
    """
    Computes a deterministic, feature-hashed normalized term-frequency embedding.
    Ensures zero external model download latency and complete offline reproducibility.
    """
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return [0.0] * dim
        
    vec = np.zeros(dim, dtype=np.float32)
    for tok in tokens:
        # Hashing trick with MD5 to uniform buckets
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[idx] += sign
        
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()

class SchemeVectorStore:
    _instance = None
    _client = None

    def __init__(self, db_path: str = QDRANT_PATH):
        if db_path == ":memory:":
            self.client = QdrantClient(":memory:")
        else:
            Path(db_path).mkdir(parents=True, exist_ok=True)
            if SchemeVectorStore._client is None:
                SchemeVectorStore._client = QdrantClient(path=db_path)
            self.client = SchemeVectorStore._client
        self._init_collection()

    def _init_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
            )
            print(f"Created Qdrant collection: '{COLLECTION_NAME}'")

    def index_all_schemes_from_sqlite(self, sqlite_path: str = "data/schemes.db") -> int:
        """Reads all schemes from SQLite and indexes them into Qdrant."""
        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()
        cur.execute("""
        SELECT scheme_id, name, level, state, short_description, detailed_description,
               benefits_verbatim, eligibility_verbatim, documents_required_verbatim, source_url
        FROM schemes
        """)
        rows = cur.fetchall()
        conn.close()

        points = []
        for idx, row in enumerate(rows, 1):
            sid, name, level, state, s_desc, d_desc, benefits, elig, docs_req, url = row
            
            # Combine content for embedding
            text_to_embed = f"{name} {state or level} {s_desc} {elig} {benefits}"
            vector = compute_text_embedding(text_to_embed)
            
            payload = {
                "scheme_id": sid,
                "name": name,
                "level": level,
                "state": state,
                "short_description": s_desc,
                "benefits": benefits,
                "eligibility_verbatim": elig,
                "documents_required": docs_req,
                "source_url": url
            }
            
            points.append(PointStruct(id=idx, vector=vector, payload=payload))

        print(f"Uploading {len(points)} schemes into Qdrant vector store at {QDRANT_PATH}...")
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print("Qdrant indexing completed successfully!")
        return len(points)

    def search_schemes(self, query: str, state_filter: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs hybrid retrieval: combines dense vector similarity with lexical term matching
        to ensure high recall on critical domain concepts (e.g., pregnant, ambulance, nutrition).
        """
        query_vec = compute_text_embedding(query)
        q_tokens = set(re.findall(r"\w+", query.lower()))
        
        query_filter = None
        if state_filter and state_filter.strip().lower() not in ["all", "any", ""]:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="state",
                        match=MatchValue(value=state_filter)
                    )
                ]
            )

        # Retrieve a broader candidate pool from vector store
        search_results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec,
            query_filter=query_filter,
            limit=min(25, top_k * 4)
        )

        candidates = []
        for hit in search_results.points:
            p = hit.payload or {}
            vec_score = float(hit.score)
            
            # Compute lexical keyword match boost
            doc_corpus = f"{p.get('name', '')} {p.get('state', '')} {p.get('short_description', '')} {p.get('eligibility_verbatim', '')} {p.get('benefits', '')}".lower()
            keyword_matches = sum(1 for tok in q_tokens if tok in doc_corpus)
            
            # Priority matches for high-signal demographic terms
            priority_boost = 0.0
            for term in ["pregnant", "maternal", "maternity", "infant", "child", "girl", "adolescent", "transport", "ambulance", "checkup", "nutrition"]:
                if term in q_tokens and term in doc_corpus:
                    priority_boost += 0.08
                    
            hybrid_score = vec_score + (keyword_matches * 0.02) + priority_boost
            
            candidates.append({
                "score": hybrid_score,
                "scheme_id": p.get("scheme_id"),
                "name": p.get("name"),
                "state": p.get("state"),
                "eligibility_verbatim": p.get("eligibility_verbatim"),
                "benefits": p.get("benefits"),
                "documents_required": p.get("documents_required"),
                "source_url": p.get("source_url")
            })

        # Rank by hybrid score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

if __name__ == "__main__":
    store = SchemeVectorStore()
    count = store.index_all_schemes_from_sqlite()
    print(f"Total schemes indexed in Qdrant: {count}")

    test_queries = [
        "maternity benefit for pregnant women and newborn child",
        "adolescent girls health and sanitary napkins",
        "construction workers accident assistance and medical aid"
    ]
    for q in test_queries:
        print(f"\n--- Search results for: '{q}' ---")
        hits = store.search_schemes(q, top_k=2)
        for h in hits:
            print(f"  • [{h['score']:.3f}] {h['name']} ({h['state']}) -> {h['source_url']}")
