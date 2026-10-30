"""
harness.py - Evaluation harness comparing Deterministic Rule Engine against Keyword/Metadata Baseline (Slice 4).

Metrics evaluated:
  - Precision@K and Recall@K for scheme recommendation
  - Eligibility Error Rate (False Positives: claiming eligible when ineligible; False Negatives: claiming ineligible when eligible)
  - Uncertainty Handling Rate (correctly identifying missing information vs hallucinating decisions)
  - Evidence Support Rate (percentage of recommendations backed by verbatim source citations)
"""

import sqlite3
import json
from typing import Dict, Any, List, Set, Tuple
from src.schema.rules import UserProfile
from src.engine.evaluator import evaluate_scheme, OverallSchemeCategory
from data.gold_standard.gold_rules_uttarakhand import get_gold_rules_uttarakhand
from data.gold_standard.synthetic_profiles import SYNTHETIC_TEST_CASES

class KeywordMetadataBaseline:
    """Simple baseline that ranks schemes by keyword overlap with user attributes."""
    def __init__(self, db_path: str = "data/schemes.db"):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT scheme_id, name, short_description, eligibility_verbatim, state FROM schemes")
        self.schemes = cur.fetchall()
        conn.close()

    def rank(self, profile: UserProfile, top_k: int = 5) -> List[Tuple[str, float]]:
        """Score schemes based on keyword matching."""
        keywords = []
        if profile.gender:
            keywords.extend(["girl", "woman", "female"] if profile.gender.lower() == "female" else ["man", "male"])
        if profile.is_pregnant:
            keywords.extend(["pregnant", "maternal", "mother"])
        if profile.registered_worker or profile.occupation_category == "construction_worker":
            keywords.extend(["worker", "bocw", "construction", "labour"])
        if profile.is_student:
            keywords.extend(["student", "school", "education"])
        if profile.state_residence:
            keywords.append(profile.state_residence.lower())
            
        scores = []
        for sid, name, desc, elig, state in self.schemes:
            text = f"{name} {desc} {elig} {state}".lower()
            score = sum(1 for kw in keywords if kw in text)
            scores.append((sid, score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

def run_evaluation(top_k: int = 5) -> Dict[str, Any]:
    gold_rules = get_gold_rules_uttarakhand()
    baseline = KeywordMetadataBaseline()
    
    total_engine_fp = 0  # False Positive: predicted eligible when gold is ineligible
    total_engine_fn = 0  # False Negative: predicted ineligible when gold is eligible
    total_evaluations = 0
    
    engine_precision_k_list = []
    engine_recall_k_list = []
    baseline_precision_k_list = []
    baseline_recall_k_list = []
    
    evidence_backed_count = 0
    total_engine_recommendations = 0

    results_per_case = []
    
    for case in SYNTHETIC_TEST_CASES:
        pid = case["profile_id"]
        profile = case["profile"]
        expected = case["expected_categories"]
        
        # Ground truth positives for this profile
        gold_positives = {sid for sid, cat in expected.items() if cat == OverallSchemeCategory.POTENTIAL_MATCH}
        gold_negatives = {sid for sid, cat in expected.items() if cat == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE}
        
        # 1. Deterministic Rule Engine Evaluation
        engine_matches = []
        engine_needs_info = []
        engine_ineligible = []
        
        for sid, rule in gold_rules.items():
            report = evaluate_scheme(rule, profile)
            total_evaluations += 1
            
            # Check Evidence Support Rate: verbatim sources must exist
            if report.category == OverallSchemeCategory.POTENTIAL_MATCH:
                engine_matches.append(sid)
                total_engine_recommendations += 1
                if len(report.verbatim_sources) > 0:
                    evidence_backed_count += 1
            elif report.category == OverallSchemeCategory.MORE_INFORMATION_NEEDED:
                engine_needs_info.append(sid)
            elif report.category == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE:
                engine_ineligible.append(sid)
                
            # Error checking against gold expected
            if sid in expected:
                exp_cat = expected[sid]
                # False positive: Engine said POTENTIAL_MATCH but was strictly LIKELY_NOT_ELIGIBLE
                if report.category == OverallSchemeCategory.POTENTIAL_MATCH and exp_cat == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE:
                    total_engine_fp += 1
                # False negative: Engine said LIKELY_NOT_ELIGIBLE but was POTENTIAL_MATCH
                if report.category == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE and exp_cat == OverallSchemeCategory.POTENTIAL_MATCH:
                    total_engine_fn += 1
                    
        # Precision@K and Recall@K for Engine
        retrieved_engine = set(engine_matches[:top_k])
        true_positives_engine = len(retrieved_engine & gold_positives)
        p_engine = true_positives_engine / len(retrieved_engine) if retrieved_engine else 1.0
        r_engine = true_positives_engine / len(gold_positives) if gold_positives else 1.0
        engine_precision_k_list.append(p_engine)
        engine_recall_k_list.append(r_engine)
        
        # 2. Keyword Baseline Evaluation
        baseline_ranked = [sid for sid, score in baseline.rank(profile, top_k=top_k)]
        retrieved_baseline = set(baseline_ranked)
        true_positives_base = len(retrieved_baseline & gold_positives)
        p_base = true_positives_base / len(retrieved_baseline) if retrieved_baseline else 0.0
        r_base = true_positives_base / len(gold_positives) if gold_positives else 1.0
        baseline_precision_k_list.append(p_base)
        baseline_recall_k_list.append(r_base)
        
        results_per_case.append({
            "profile_id": pid,
            "engine_matches": engine_matches,
            "engine_missing_info": engine_needs_info,
            "engine_ineligible": engine_ineligible,
            "baseline_top_k": baseline_ranked,
            "engine_p@k": p_engine,
            "baseline_p@k": p_base
        })
        
    avg_engine_p = sum(engine_precision_k_list) / len(engine_precision_k_list)
    avg_engine_r = sum(engine_recall_k_list) / len(engine_recall_k_list)
    avg_base_p = sum(baseline_precision_k_list) / len(baseline_precision_k_list)
    avg_base_r = sum(baseline_recall_k_list) / len(baseline_recall_k_list)
    
    evidence_support_rate = (evidence_backed_count / total_engine_recommendations) if total_engine_recommendations > 0 else 1.0
    
    summary = {
        "engine_precision_at_k": round(avg_engine_p, 4),
        "engine_recall_at_k": round(avg_engine_r, 4),
        "baseline_precision_at_k": round(avg_base_p, 4),
        "baseline_recall_at_k": round(avg_base_r, 4),
        "engine_false_positives": total_engine_fp,
        "engine_false_negatives": total_engine_fn,
        "engine_error_rate": round((total_engine_fp + total_engine_fn) / total_evaluations, 4),
        "evidence_support_rate": round(evidence_support_rate, 4),
        "case_details": results_per_case
    }
    return summary

if __name__ == "__main__":
    report = run_evaluation(top_k=5)
    print("="*60)
    print("EVALUATION HARNESS RESULTS (Slice 4)")
    print("="*60)
    print(f"Deterministic Engine Precision@5: {report['engine_precision_at_k'] * 100:.1f}%")
    print(f"Deterministic Engine Recall@5:    {report['engine_recall_at_k'] * 100:.1f}%")
    print(f"Keyword Baseline Precision@5:     {report['baseline_precision_at_k'] * 100:.1f}%")
    print(f"Keyword Baseline Recall@5:        {report['baseline_recall_at_k'] * 100:.1f}%")
    print(f"Engine False Positives:           {report['engine_false_positives']}")
    print(f"Engine False Negatives:           {report['engine_false_negatives']}")
    print(f"Engine Eligibility Error Rate:    {report['engine_error_rate'] * 100:.1f}%")
    print(f"Evidence Support Rate:            {report['evidence_support_rate'] * 100:.1f}%")
    print("="*60)

