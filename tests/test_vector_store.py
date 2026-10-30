"""
tests/test_vector_store.py - Tests for Qdrant vector store and RAG pipeline.
"""

import pytest
from src.engine.vector_store import SchemeVectorStore
from src.engine.rag_pipeline import SchemeRAGPipeline

def test_qdrant_vector_store_retrieval():
    store = SchemeVectorStore()
    
    # Query for maternity schemes
    results = store.search_schemes("maternity assistance for pregnant women", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "scheme_id" in top
    assert "name" in top
    assert "source_url" in top
    assert top["source_url"].startswith("https://www.myscheme.gov.in/schemes/")

def test_qdrant_state_filtering():
    store = SchemeVectorStore()
    
    # Query with Uttarakhand state filter
    results = store.search_schemes("sanitary napkin scheme", state_filter="Uttarakhand", top_k=3)
    assert len(results) > 0
    for r in results:
        assert r["state"] == "Uttarakhand"

def test_rag_pipeline_execution():
    pipeline = SchemeRAGPipeline()
    res = pipeline.retrieve_and_answer("maternity assistance in Chhattisgarh", state_filter="Chhattisgarh", top_k=2)
    assert "answer" in res
    assert "may be eligible" in res["answer"].lower()
    assert len(res["retrieved_schemes"]) > 0

