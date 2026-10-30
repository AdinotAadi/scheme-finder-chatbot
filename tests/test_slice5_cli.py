"""
tests/test_slice5_cli.py - Regression and integration tests for Slice 5 CLI.
"""

import pytest
from src.cli import fetch_scheme_metadata
from src.engine.evaluator import evaluate_scheme, OverallSchemeCategory
from src.schema.rules import UserProfile
from data.gold_standard.gold_rules_uttarakhand import get_gold_rules_uttarakhand

def test_scheme_metadata_retrieval():
    meta = fetch_scheme_metadata()
    assert len(meta) >= 16
    for sid, m in meta.items():
        assert "name" in m and len(m["name"]) > 0
        assert "url" in m and m["url"].startswith("https://www.myscheme.gov.in/schemes/")
        assert "documents" in m

def test_cli_end_to_end_assessment_flow():
    # Simulate a user profile generated through CLI questionnaire
    profile = UserProfile(
        age=16,
        gender="female",
        state_residence="Uttarakhand",
        district_residence="Haridwar",
        is_student=True
    )
    gold_rules = get_gold_rules_uttarakhand()
    meta = fetch_scheme_metadata()

    matches = []
    need_info = []

    for sid, rule in gold_rules.items():
        rep = evaluate_scheme(rule, profile)
        if rep.category == OverallSchemeCategory.POTENTIAL_MATCH:
            matches.append((rep, meta.get(sid, {})))
        elif rep.category == OverallSchemeCategory.MORE_INFORMATION_NEEDED:
            need_info.append((rep, meta.get(sid, {})))

    # Kishori Balika Yojana (kbyuk) must be among the potential matches
    matched_ids = [rep.scheme_id for rep, m in matches]
    assert "kbyuk" in matched_ids
    assert "snduk" in matched_ids
    assert "snsu" in matched_ids

    # For every match, check required display contract
    for rep, m in matches:
        assert len(rep.satisfied_criteria) > 0
        assert m["url"].startswith("https://www.myscheme.gov.in")
        assert len(m["documents"]) > 0

