"""
evaluator.py - Deterministic eligibility engine with three-valued logic (Slice 3).

Truth values:
  - SATISFIED
  - NOT_SATISFIED
  - UNKNOWN

Hard constraints:
  - Uncertainty is never swallowed (missing info remains missing).
  - 'Likely not eligible' is ONLY derived from verified mandatory criteria.
  - Returns clear explanation of satisfied, missing, and failed criteria.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel, Field
from src.schema.rules import (
    UserProfile, SchemeEligibilityRule, SingleCriterion, CriterionGroup,
    ReviewStatus, Operator, LogicalGroupOperator, AttributeName
)

class EvaluationResult(str, Enum):
    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"
    UNKNOWN = "unknown"

class OverallSchemeCategory(str, Enum):
    POTENTIAL_MATCH = "potential_match"                     # All verified criteria satisfied
    MORE_INFORMATION_NEEDED = "more_information_needed"     # No verified failures, but 1+ unknown
    LIKELY_NOT_ELIGIBLE = "likely_not_eligible"             # 1+ verified mandatory criteria failed
    NEEDS_MANUAL_VERIFICATION = "needs_manual_verification" # Unreviewed rules or unmodeled conditions

class CriterionEvaluation(BaseModel):
    criterion_id: str
    attribute: str
    operator: str
    target_value: Any
    user_value: Any
    result: EvaluationResult
    is_mandatory: bool
    review_status: ReviewStatus
    verbatim_source_sentence: str
    explanation: str

class SchemeEvaluationReport(BaseModel):
    scheme_id: str
    category: OverallSchemeCategory
    per_criterion_results: List[CriterionEvaluation]
    satisfied_criteria: List[str]
    missing_criteria: List[str]
    failed_criteria: List[str]
    verbatim_sources: List[str]
    explanation: str

def evaluate_single_criterion(criterion: SingleCriterion, profile: UserProfile) -> CriterionEvaluation:
    """Evaluates an atomic criterion against user profile using three-valued logic."""
    attr_str = criterion.attribute.value
    user_val = getattr(profile, attr_str, None)
    
    # Missing information -> UNKNOWN
    if user_val is None:
        return CriterionEvaluation(
            criterion_id=criterion.criterion_id,
            attribute=attr_str,
            operator=criterion.operator.value,
            target_value=criterion.target_value,
            user_value=None,
            result=EvaluationResult.UNKNOWN,
            is_mandatory=criterion.is_mandatory,
            review_status=criterion.review_status,
            verbatim_source_sentence=criterion.verbatim_source_sentence,
            explanation=f"User profile does not specify '{attr_str}' (required by: '{criterion.verbatim_source_sentence}')"
        )
        
    target = criterion.target_value
    op = criterion.operator
    res = EvaluationResult.NOT_SATISFIED
    
    if op == Operator.EQ:
        if isinstance(user_val, str) and isinstance(target, str):
            res = EvaluationResult.SATISFIED if user_val.strip().lower() == target.strip().lower() else EvaluationResult.NOT_SATISFIED
        else:
            res = EvaluationResult.SATISFIED if user_val == target else EvaluationResult.NOT_SATISFIED
    elif op == Operator.NEQ:
        if isinstance(user_val, str) and isinstance(target, str):
            res = EvaluationResult.SATISFIED if user_val.strip().lower() != target.strip().lower() else EvaluationResult.NOT_SATISFIED
        else:
            res = EvaluationResult.SATISFIED if user_val != target else EvaluationResult.NOT_SATISFIED
    elif op == Operator.GTE:
        res = EvaluationResult.SATISFIED if user_val >= target else EvaluationResult.NOT_SATISFIED
    elif op == Operator.LTE:
        res = EvaluationResult.SATISFIED if user_val <= target else EvaluationResult.NOT_SATISFIED
    elif op == Operator.IN:
        if isinstance(target, list):
            target_norm = [t.strip().lower() if isinstance(t, str) else t for t in target]
            user_norm = user_val.strip().lower() if isinstance(user_val, str) else user_val
            res = EvaluationResult.SATISFIED if user_norm in target_norm else EvaluationResult.NOT_SATISFIED
    elif op == Operator.CONTAINS:
        if isinstance(user_val, list):
            user_norm = [u.strip().lower() if isinstance(u, str) else u for u in user_val]
            target_norm = target.strip().lower() if isinstance(target, str) else target
            res = EvaluationResult.SATISFIED if target_norm in user_norm else EvaluationResult.NOT_SATISFIED
        elif isinstance(user_val, str) and isinstance(target, str):
            res = EvaluationResult.SATISFIED if target.lower() in user_val.lower() else EvaluationResult.NOT_SATISFIED
            
    status_text = "satisfied" if res == EvaluationResult.SATISFIED else "not satisfied"
    explanation = f"Condition {attr_str} {op.value} {target} is {status_text} (user has: {user_val})"
    
    return CriterionEvaluation(
        criterion_id=criterion.criterion_id,
        attribute=attr_str,
        operator=op.value,
        target_value=target,
        user_value=user_val,
        result=res,
        is_mandatory=criterion.is_mandatory,
        review_status=criterion.review_status,
        verbatim_source_sentence=criterion.verbatim_source_sentence,
        explanation=explanation
    )

def evaluate_criterion_group(group: CriterionGroup, profile: UserProfile) -> Tuple[EvaluationResult, List[CriterionEvaluation]]:
    """Evaluates nested boolean groups (ALL, ANY, NOT) under Kleene / Lukasiewicz 3-valued logic."""
    sub_evaluations: List[CriterionEvaluation] = []
    sub_results: List[EvaluationResult] = []
    
    for item in group.criteria:
        if isinstance(item, SingleCriterion):
            eval_res = evaluate_single_criterion(item, profile)
            sub_evaluations.append(eval_res)
            sub_results.append(eval_res.result)
        elif isinstance(item, CriterionGroup):
            grp_res, grp_evals = evaluate_criterion_group(item, profile)
            sub_evaluations.extend(grp_evals)
            sub_results.append(grp_res)
            
    if group.operator == LogicalGroupOperator.ALL:
        # ALL / AND:
        # If any NOT_SATISFIED -> NOT_SATISFIED
        # Else if any UNKNOWN -> UNKNOWN
        # Else -> SATISFIED
        if EvaluationResult.NOT_SATISFIED in sub_results:
            overall = EvaluationResult.NOT_SATISFIED
        elif EvaluationResult.UNKNOWN in sub_results:
            overall = EvaluationResult.UNKNOWN
        else:
            overall = EvaluationResult.SATISFIED
            
    elif group.operator == LogicalGroupOperator.ANY:
        # ANY / OR:
        # If any SATISFIED -> SATISFIED
        # Else if any UNKNOWN -> UNKNOWN
        # Else -> NOT_SATISFIED
        if EvaluationResult.SATISFIED in sub_results:
            overall = EvaluationResult.SATISFIED
        elif EvaluationResult.UNKNOWN in sub_results:
            overall = EvaluationResult.UNKNOWN
        else:
            overall = EvaluationResult.NOT_SATISFIED
            
    elif group.operator == LogicalGroupOperator.NOT:
        # NOT:
        # SATISFIED -> NOT_SATISFIED
        # NOT_SATISFIED -> SATISFIED
        # UNKNOWN -> UNKNOWN
        inner = sub_results[0] if sub_results else EvaluationResult.UNKNOWN
        if inner == EvaluationResult.SATISFIED:
            overall = EvaluationResult.NOT_SATISFIED
        elif inner == EvaluationResult.NOT_SATISFIED:
            overall = EvaluationResult.SATISFIED
        else:
            overall = EvaluationResult.UNKNOWN
            
    return overall, sub_evaluations

def evaluate_scheme(scheme_rule: SchemeEligibilityRule, profile: UserProfile) -> SchemeEvaluationReport:
    """Evaluates full scheme eligibility and assigns research-compliant categorical outcome."""
    group_result, all_evaluations = evaluate_criterion_group(scheme_rule.rule_group, profile)
    
    satisfied_c = []
    missing_c = []
    failed_c = []
    sources = []
    
    has_unreviewed = False
    
    for ev in all_evaluations:
        if ev.verbatim_source_sentence not in sources:
            sources.append(ev.verbatim_source_sentence)
            
        if ev.review_status != ReviewStatus.VERIFIED:
            has_unreviewed = True
            
        if ev.result == EvaluationResult.SATISFIED:
            satisfied_c.append(ev.explanation)
        elif ev.result == EvaluationResult.NOT_SATISFIED:
            failed_c.append(ev.explanation)
        elif ev.result == EvaluationResult.UNKNOWN:
            missing_c.append(ev.explanation)
            
    # Decision logic based on Three-Valued Logic and Hard Rules:
    # 1. If overall group evaluation is NOT_SATISFIED and contains verified mandatory failures -> LIKELY_NOT_ELIGIBLE
    # 2. If unreviewed rules exist or discretionary administrative conditions present -> NEEDS_MANUAL_VERIFICATION
    # 3. If group evaluation is UNKNOWN -> MORE_INFORMATION_NEEDED
    # 4. If group evaluation is SATISFIED -> POTENTIAL_MATCH
    
    if group_result == EvaluationResult.NOT_SATISFIED:
        # Check if failed criteria are verified and mandatory
        verified_mand_fails = [ev for ev in all_evaluations if ev.result == EvaluationResult.NOT_SATISFIED and ev.review_status == ReviewStatus.VERIFIED and ev.is_mandatory]
        if verified_mand_fails:
            category = OverallSchemeCategory.LIKELY_NOT_ELIGIBLE
            explanation = f"User is likely not eligible due to failing verified mandatory criteria: {'; '.join(failed_c)}"
        else:
            category = OverallSchemeCategory.NEEDS_MANUAL_VERIFICATION
            explanation = "Criteria failed but rules require human review or are non-mandatory."
    elif has_unreviewed or scheme_rule.unmodeled_discretionary_conditions:
        category = OverallSchemeCategory.NEEDS_MANUAL_VERIFICATION
        explanation = "Scheme contains unreviewed rules or discretionary administrative conditions requiring human verification."
    elif group_result == EvaluationResult.UNKNOWN:
        category = OverallSchemeCategory.MORE_INFORMATION_NEEDED
        explanation = f"Eligibility cannot be determined yet because information is missing: {'; '.join(missing_c)}"
    else:
        category = OverallSchemeCategory.POTENTIAL_MATCH
        explanation = "User satisfies all verified eligibility criteria."
        
    return SchemeEvaluationReport(
        scheme_id=scheme_rule.scheme_id,
        category=category,
        per_criterion_results=all_evaluations,
        satisfied_criteria=satisfied_c,
        missing_criteria=missing_c,
        failed_criteria=failed_c,
        verbatim_sources=sources,
        explanation=explanation
    )
