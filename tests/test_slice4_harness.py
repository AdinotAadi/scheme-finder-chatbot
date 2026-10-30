"""
tests/test_slice4_harness.py - Automated regression test for evaluation harness (Slice 4).
"""

import pytest
from src.engine.harness import run_evaluation

def test_evaluation_metrics_benchmark():
    metrics = run_evaluation(top_k=5)
    
    # Core research contribution checks:
    # 1. Deterministic engine has zero eligibility error rate on verified gold set
    assert metrics["engine_false_positives"] == 0, "Deterministic engine must have 0 false positives"
    assert metrics["engine_false_negatives"] == 0, "Deterministic engine must have 0 false negatives"
    assert metrics["engine_error_rate"] == 0.0
    
    # 2. Evidence Support Rate is 100% (every recommendation traces to verbatim source)
    assert metrics["evidence_support_rate"] == 1.0
    
    # 3. Deterministic engine significantly outperforms keyword baseline in Precision@5
    assert metrics["engine_precision_at_k"] > metrics["baseline_precision_at_k"] + 0.30
    assert metrics["engine_precision_at_k"] >= 0.80
    assert metrics["engine_recall_at_k"] >= 0.90

