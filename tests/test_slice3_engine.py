"""
tests/test_slice3_engine.py - Comprehensive tests for deterministic eligibility engine (Slice 3).
"""

import pytest
from src.schema.rules import (
    UserProfile, SchemeEligibilityRule, SingleCriterion, CriterionGroup,
    ReviewStatus, Operator, LogicalGroupOperator, AttributeName
)
from src.engine.evaluator import (
    evaluate_single_criterion, evaluate_criterion_group, evaluate_scheme,
    EvaluationResult, OverallSchemeCategory
)

@pytest.fixture
def kbyuk_rule():
    """Rule model for Kishori Balika Yojana Uttarakhand (kbyuk)."""
    # Eligibility:
    # 1. Resident of Uttarakhand
    # 2. Adolescent girl age 14 to 18
    # 3. Residing in Haridwar or Udham Singh Nagar
    c1 = SingleCriterion(
        criterion_id="kbyuk_c1",
        attribute=AttributeName.STATE_RESIDENCE,
        operator=Operator.EQ,
        target_value="Uttarakhand",
        verbatim_source_sentence="The applicant must be a resident of Uttarakhand.",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    c2_gender = SingleCriterion(
        criterion_id="kbyuk_c2_gender",
        attribute=AttributeName.GENDER,
        operator=Operator.EQ,
        target_value="female",
        verbatim_source_sentence="The applicant must be an adolescent girl in the age group of 14 to 18 years.",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    c2_age_min = SingleCriterion(
        criterion_id="kbyuk_c2_age_min",
        attribute=AttributeName.AGE,
        operator=Operator.GTE,
        target_value=14,
        verbatim_source_sentence="The applicant must be an adolescent girl in the age group of 14 to 18 years.",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    c2_age_max = SingleCriterion(
        criterion_id="kbyuk_c2_age_max",
        attribute=AttributeName.AGE,
        operator=Operator.LTE,
        target_value=18,
        verbatim_source_sentence="The applicant must be an adolescent girl in the age group of 14 to 18 years.",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    c3_district = SingleCriterion(
        criterion_id="kbyuk_c3_dist",
        attribute=AttributeName.DISTRICT_RESIDENCE,
        operator=Operator.IN,
        target_value=["Haridwar", "Udham Singh Nagar"],
        verbatim_source_sentence="The applicant must be residing in one of the aspirational districts of Uttarakhand- Haridwar or Udham Singh Nagar.",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    
    group = CriterionGroup(
        operator=LogicalGroupOperator.ALL,
        criteria=[c1, c2_gender, c2_age_min, c2_age_max, c3_district]
    )
    
    return SchemeEligibilityRule(scheme_id="kbyuk", rule_group=group)

def test_kbyuk_perfect_match(kbyuk_rule):
    profile = UserProfile(
        age=16,
        gender="female",
        state_residence="Uttarakhand",
        district_residence="Haridwar"
    )
    report = evaluate_scheme(kbyuk_rule, profile)
    assert report.category == OverallSchemeCategory.POTENTIAL_MATCH
    assert len(report.failed_criteria) == 0
    assert len(report.missing_criteria) == 0

def test_kbyuk_age_boundary_edges(kbyuk_rule):
    # Boundary: Age 13 -> LIKELY_NOT_ELIGIBLE
    p13 = UserProfile(age=13, gender="female", state_residence="Uttarakhand", district_residence="Haridwar")
    r13 = evaluate_scheme(kbyuk_rule, p13)
    assert r13.category == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE
    
    # Boundary: Age 14 -> MATCH
    p14 = UserProfile(age=14, gender="female", state_residence="Uttarakhand", district_residence="Haridwar")
    r14 = evaluate_scheme(kbyuk_rule, p14)
    assert r14.category == OverallSchemeCategory.POTENTIAL_MATCH
    
    # Boundary: Age 18 -> MATCH
    p18 = UserProfile(age=18, gender="female", state_residence="Uttarakhand", district_residence="Haridwar")
    r18 = evaluate_scheme(kbyuk_rule, p18)
    assert r18.category == OverallSchemeCategory.POTENTIAL_MATCH
    
    # Boundary: Age 19 -> LIKELY_NOT_ELIGIBLE
    p19 = UserProfile(age=19, gender="female", state_residence="Uttarakhand", district_residence="Haridwar")
    r19 = evaluate_scheme(kbyuk_rule, p19)
    assert r19.category == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE

def test_missing_data_stays_missing(kbyuk_rule):
    # Missing district -> MORE_INFORMATION_NEEDED, NEVER assume failed or satisfied
    p_partial = UserProfile(age=16, gender="female", state_residence="Uttarakhand")
    r = evaluate_scheme(kbyuk_rule, p_partial)
    assert r.category == OverallSchemeCategory.MORE_INFORMATION_NEEDED
    assert any("district_residence" in m for m in r.missing_criteria)

def test_state_mismatch(kbyuk_rule):
    # User from Rajasthan applying for Uttarakhand scheme -> LIKELY_NOT_ELIGIBLE
    p = UserProfile(age=16, gender="female", state_residence="Rajasthan", district_residence="Jaipur")
    r = evaluate_scheme(kbyuk_rule, p)
    assert r.category == OverallSchemeCategory.LIKELY_NOT_ELIGIBLE
    assert any("state_residence" in f for f in r.failed_criteria)

def test_unreviewed_rules_trigger_manual_verification(kbyuk_rule):
    # Mark one rule as unreviewed
    kbyuk_rule.rule_group.criteria[0].review_status = ReviewStatus.UNREVIEWED
    profile = UserProfile(age=16, gender="female", state_residence="Uttarakhand", district_residence="Haridwar")
    r = evaluate_scheme(kbyuk_rule, profile)
    assert r.category == OverallSchemeCategory.NEEDS_MANUAL_VERIFICATION

def test_complex_any_and_not_logic():
    # Target: Registered BOCW Worker OR (BPL AND Rural)
    c_bocw = SingleCriterion(
        criterion_id="c_bocw",
        attribute=AttributeName.REGISTERED_WORKER,
        operator=Operator.EQ,
        target_value=True,
        verbatim_source_sentence="Must be registered construction worker",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    c_bpl = SingleCriterion(
        criterion_id="c_bpl",
        attribute=AttributeName.IS_BPL,
        operator=Operator.EQ,
        target_value=True,
        verbatim_source_sentence="Must have BPL card",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    c_rural = SingleCriterion(
        criterion_id="c_rural",
        attribute=AttributeName.RESIDENCE_AREA,
        operator=Operator.EQ,
        target_value="rural",
        verbatim_source_sentence="Must reside in rural region",
        is_mandatory=True,
        review_status=ReviewStatus.VERIFIED
    )
    
    bpl_rural = CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_bpl, c_rural])
    top_group = CriterionGroup(operator=LogicalGroupOperator.ANY, criteria=[c_bocw, bpl_rural])
    rule = SchemeEligibilityRule(scheme_id="test_any", rule_group=top_group)
    
    # Case 1: Has BOCW only -> MATCH
    p1 = UserProfile(registered_worker=True)
    r1 = evaluate_scheme(rule, p1)
    assert r1.category == OverallSchemeCategory.POTENTIAL_MATCH
    
    # Case 2: Not BOCW, but BPL and Rural -> MATCH
    p2 = UserProfile(registered_worker=False, is_bpl=True, residence_area="rural")
    r2 = evaluate_scheme(rule, p2)
    assert r2.category == OverallSchemeCategory.POTENTIAL_MATCH
    
    # Case 3: Not BOCW, BPL is True, but area is missing -> MORE_INFORMATION_NEEDED
    p3 = UserProfile(registered_worker=False, is_bpl=True)
    r3 = evaluate_scheme(rule, p3)
    assert r3.category == OverallSchemeCategory.MORE_INFORMATION_NEEDED

