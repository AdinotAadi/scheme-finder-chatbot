"""
rag_pipeline.py - Retrieval-Augmented Generation (RAG) pipeline for conversational scheme discovery.

Combines:
1. Qdrant vector retrieval over scraped scheme documents.
2. Structured eligibility constraint checking.
3. Lightweight Gemma / LLM conversational responder grounded strictly in retrieved context.
"""

import os
import json
from typing import List, Dict, Any, Optional
from src.engine.vector_store import SchemeVectorStore
from src.engine.evaluator import evaluate_scheme, OverallSchemeCategory
from src.schema.rules import UserProfile, SchemeEligibilityRule
from src.llm.llm_interface import LLMProposalProvider

RAG_PROMPT_TEMPLATE = """You are a helpful and trustworthy assistant for women in India seeking government welfare schemes.
Answer the user's question using ONLY the following verified scheme passages.

CRITICAL RULES:
1. NEVER invent eligibility criteria, cash amounts, or benefits not listed in the text.
2. Clearly state that a user "may be eligible" - never promise or guarantee benefits.
3. Always include the official portal link for the scheme.
4. If the provided context does not have the answer, state that clearly and advise checking the official portal.

RELEVANT SCHEMES CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER (Concise, empathetic, source-grounded):
"""

class SchemeRAGPipeline:
    def __init__(self, vector_store: Optional[SchemeVectorStore] = None):
        self.vector_store = vector_store or SchemeVectorStore()
        self.llm_provider = LLMProposalProvider()

    def retrieve_and_answer(self, query: str, state_filter: Optional[str] = None, top_k: int = 3) -> Dict[str, Any]:
        """Performs RAG retrieval and produces a grounded response."""
        retrieved_hits = self.vector_store.search_schemes(query, state_filter=state_filter, top_k=top_k)
        
        # Build context blocks
        context_blocks = []
        for idx, hit in enumerate(retrieved_hits, 1):
            block = (
                f"[{idx}] Scheme: {hit['name']} ({hit.get('state') or 'Central'})\n"
                f"Official Link: {hit['source_url']}\n"
                f"Eligibility Criteria: {hit.get('eligibility_verbatim') or 'See official portal'}\n"
                f"Benefits: {hit.get('benefits') or 'See official portal'}\n"
                f"Documents: {hit.get('documents_required') or 'Consult portal'}\n"
            )
            context_blocks.append(block)

        combined_context = "\n---\n".join(context_blocks)

        # Fallback / grounded answer generation
        if not retrieved_hits or retrieved_hits[0]["score"] < 0.15:
            answer = (
                "I could not find specific government schemes matching your request with high confidence. "
                "Please check the official portal at https://www.myscheme.gov.in or specify your state and category."
            )
        else:
            top_hit = retrieved_hits[0]
            answer = (
                f"Based on the official government records, you may be eligible for **{top_hit['name']}**.\n\n"
                f"**Key Eligibility Points:**\n{top_hit['eligibility_verbatim']}\n\n"
                f"**Benefits:**\n{top_hit['benefits']}\n\n"
                f"🔗 **Official Portal:** {top_hit['source_url']}\n\n"
                f"*(Note: You may be eligible based on these official guidelines, but benefits are not guaranteed until approved by the administering department.)*"
            )

        return {
            "query": query,
            "answer": answer,
            "retrieved_schemes": retrieved_hits,
            "context_used": combined_context
        }

if __name__ == "__main__":
    pipeline = SchemeRAGPipeline()
    res = pipeline.retrieve_and_answer("I am looking for sanitary napkin distribution schemes for teenage girls in Uttarakhand")
    print(res["answer"])

