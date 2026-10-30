"""
gold_rules_uttarakhand.py - Gold standard verified structured eligibility rules for 16 Uttarakhand schemes.
Hand-labeled and verified against verbatim portal text (Slice 4).
"""

from typing import List, Dict
from src.schema.rules import (
    SchemeEligibilityRule, SingleCriterion, CriterionGroup,
    ReviewStatus, Operator, LogicalGroupOperator, AttributeName
)

def get_gold_rules_uttarakhand() -> Dict[str, SchemeEligibilityRule]:
    """Returns hand-curated and verified gold eligibility rules for the 16 Uttarakhand schemes."""
    rules = {}
    
    # 1. kbyuk: Kishori Balika Yojana
    # Res Uttarakhand + Female + Age 14-18 + District Haridwar/Udham Singh Nagar
    c_kbyuk_res = SingleCriterion(
        criterion_id="kbyuk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The applicant must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kbyuk_fem = SingleCriterion(
        criterion_id="kbyuk_c2", attribute=AttributeName.GENDER, operator=Operator.EQ, target_value="female",
        verbatim_source_sentence="The applicant must be an adolescent girl in the age group of 14 to 18 years.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kbyuk_min = SingleCriterion(
        criterion_id="kbyuk_c3", attribute=AttributeName.AGE, operator=Operator.GTE, target_value=14,
        verbatim_source_sentence="The applicant must be an adolescent girl in the age group of 14 to 18 years.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kbyuk_max = SingleCriterion(
        criterion_id="kbyuk_c4", attribute=AttributeName.AGE, operator=Operator.LTE, target_value=18,
        verbatim_source_sentence="The applicant must be an adolescent girl in the age group of 14 to 18 years.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kbyuk_dist = SingleCriterion(
        criterion_id="kbyuk_c5", attribute=AttributeName.DISTRICT_RESIDENCE, operator=Operator.IN, target_value=["Haridwar", "Udham Singh Nagar"],
        verbatim_source_sentence="The applicant must be residing in one of the aspirational districts of Uttarakhand- Haridwar or Udham Singh Nagar.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["kbyuk"] = SchemeEligibilityRule(
        scheme_id="kbyuk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_kbyuk_res, c_kbyuk_fem, c_kbyuk_min, c_kbyuk_max, c_kbyuk_dist])
    )

    # 2. ahwc: AYUSH Health and Wellness Centre
    # Res Uttarakhand
    c_ahwc_res = SingleCriterion(
        criterion_id="ahwc_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["ahwc"] = SchemeEligibilityRule(
        scheme_id="ahwc",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_ahwc_res]),
        unmodeled_discretionary_conditions="The beneficiary must be registered at a government-recognized Ayurvedic, Unani, or Homeopathic dispensary or hospital."
    )

    # 3. snduk: Sanitary Napkin Distribution - Uttarakhand
    # Res Uttarakhand + Female + Age 10-19
    c_snduk_res = SingleCriterion(
        criterion_id="snduk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="All girls aged between 10 to 19 years residing in Uttarakhand are eligible under this scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_snduk_fem = SingleCriterion(
        criterion_id="snduk_c2", attribute=AttributeName.GENDER, operator=Operator.EQ, target_value="female",
        verbatim_source_sentence="All girls aged between 10 to 19 years residing in Uttarakhand are eligible under this scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_snduk_min = SingleCriterion(
        criterion_id="snduk_c3", attribute=AttributeName.AGE, operator=Operator.GTE, target_value=10,
        verbatim_source_sentence="All girls aged between 10 to 19 years residing in Uttarakhand are eligible under this scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_snduk_max = SingleCriterion(
        criterion_id="snduk_c4", attribute=AttributeName.AGE, operator=Operator.LTE, target_value=19,
        verbatim_source_sentence="All girls aged between 10 to 19 years residing in Uttarakhand are eligible under this scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["snduk"] = SchemeEligibilityRule(
        scheme_id="snduk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_snduk_res, c_snduk_fem, c_snduk_min, c_snduk_max])
    )

    # 4. ipuk: Immunization Programme - Uttarakhand
    # Res Uttarakhand + Age <= 16
    c_ipuk_res = SingleCriterion(
        criterion_id="ipuk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="All children of Uttarakhand aged 0–16 years who require vaccination are eligible under the scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_ipuk_age = SingleCriterion(
        criterion_id="ipuk_c2", attribute=AttributeName.AGE, operator=Operator.LTE, target_value=16,
        verbatim_source_sentence="All children of Uttarakhand aged 0–16 years who require vaccination are eligible under the scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["ipuk"] = SchemeEligibilityRule(
        scheme_id="ipuk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_ipuk_res, c_ipuk_age])
    )

    # 5. 108easuk: 108 Emergency Ambulance Service
    # Res Uttarakhand
    c_108_res = SingleCriterion(
        criterion_id="108easuk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["108easuk"] = SchemeEligibilityRule(
        scheme_id="108easuk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_108_res]),
        unmodeled_discretionary_conditions="The benefit is provided to accident victims and individuals requiring emergency services."
    )

    # 6. snsu: Sanitary Napkin Scheme
    # Female
    c_snsu_fem = SingleCriterion(
        criterion_id="snsu_c1", attribute=AttributeName.GENDER, operator=Operator.EQ, target_value="female",
        verbatim_source_sentence="All adolescent girls and women are eligible to purchase sanitary napkins at subsidized rates from Anganwadi centres.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["snsu"] = SchemeEligibilityRule(
        scheme_id="snsu",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_snsu_fem])
    )

    # 7. kkssuk: Khushiyon Ki Sawari Sewa
    # Res Uttarakhand + (Pregnant or Age <= 1)
    c_kkssuk_res = SingleCriterion(
        criterion_id="kkssuk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kkssuk_preg = SingleCriterion(
        criterion_id="kkssuk_c2", attribute=AttributeName.IS_PREGNANT, operator=Operator.EQ, target_value=True,
        verbatim_source_sentence="The beneficiary must be a pregnant woman or a newborn baby aged 0 to 1 year.",
        is_mandatory=False, review_status=ReviewStatus.VERIFIED
    )
    c_kkssuk_infant = SingleCriterion(
        criterion_id="kkssuk_c3", attribute=AttributeName.AGE, operator=Operator.LTE, target_value=1,
        verbatim_source_sentence="The beneficiary must be a pregnant woman or a newborn baby aged 0 to 1 year.",
        is_mandatory=False, review_status=ReviewStatus.VERIFIED
    )
    group_target = CriterionGroup(operator=LogicalGroupOperator.ANY, criteria=[c_kkssuk_preg, c_kkssuk_infant])
    rules["kkssuk"] = SchemeEligibilityRule(
        scheme_id="kkssuk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_kkssuk_res, group_target])
    )

    # 8. nsjy: Nishulk Swasthya Jaanch Yojana
    # Res Uttarakhand
    c_nsjy_res = SingleCriterion(
        criterion_id="nsjy_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["nsjy"] = SchemeEligibilityRule(
        scheme_id="nsjy",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_nsjy_res]),
        unmodeled_discretionary_conditions="The beneficiary can avail free health check-ups after registering at any government hospital in the state."
    )

    # 9. maternalnutritionuk: Mukhyamantri Sampoorna Pushti Yojana
    # Res Odisha (per official verbatim portal text) + (Pregnant or Lactating)
    c_mat_res = SingleCriterion(
        criterion_id="mat_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Odisha",
        verbatim_source_sentence="The beneficiary must be a resident of Odisha.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_mat_preg = SingleCriterion(
        criterion_id="mat_c2", attribute=AttributeName.IS_PREGNANT, operator=Operator.EQ, target_value=True,
        verbatim_source_sentence="The beneficiary must be a pregnant woman or a lactating mother registered and residing within the service area of the concerned Anganwadi Centre (AWC).",
        is_mandatory=False, review_status=ReviewStatus.VERIFIED
    )
    c_mat_lact = SingleCriterion(
        criterion_id="mat_c3", attribute=AttributeName.IS_LACTATING, operator=Operator.EQ, target_value=True,
        verbatim_source_sentence="The beneficiary must be a pregnant woman or a lactating mother registered and residing within the service area of the concerned Anganwadi Centre (AWC).",
        is_mandatory=False, review_status=ReviewStatus.VERIFIED
    )
    group_preg_lact = CriterionGroup(operator=LogicalGroupOperator.ANY, criteria=[c_mat_preg, c_mat_lact])
    rules["maternalnutritionuk"] = SchemeEligibilityRule(
        scheme_id="maternalnutritionuk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_mat_res, group_preg_lact])
    )

    # 10. ywcuk: Yoga Wellness Center
    # Res Uttarakhand
    c_ywcuk_res = SingleCriterion(
        criterion_id="ywcuk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["ywcuk"] = SchemeEligibilityRule(
        scheme_id="ywcuk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_ywcuk_res]),
        unmodeled_discretionary_conditions="The beneficiary must be registered at an identified Government Ayurvedic Centre or Hospital."
    )

    # 11. kspc: Kishor Swasthya Paramarsh Clinic
    # Res Uttarakhand + Age 10-19
    c_kspc_res = SingleCriterion(
        criterion_id="kspc_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be an adolescent between 10 and 19 years of age from Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kspc_min = SingleCriterion(
        criterion_id="kspc_c2", attribute=AttributeName.AGE, operator=Operator.GTE, target_value=10,
        verbatim_source_sentence="The beneficiary must be an adolescent between 10 and 19 years of age from Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_kspc_max = SingleCriterion(
        criterion_id="kspc_c3", attribute=AttributeName.AGE, operator=Operator.LTE, target_value=19,
        verbatim_source_sentence="The beneficiary must be an adolescent between 10 and 19 years of age from Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["kspc"] = SchemeEligibilityRule(
        scheme_id="kspc",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_kspc_res, c_kspc_min, c_kspc_max])
    )

    # 12. huk: Hemoglobinopathy
    # Res Uttarakhand + Specific Diagnosis
    c_huk_res = SingleCriterion(
        criterion_id="huk_c1", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The applicant must be a resident of Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_huk_diag = SingleCriterion(
        criterion_id="huk_c2", attribute=AttributeName.SPECIFIC_DIAGNOSIS, operator=Operator.CONTAINS, target_value="hemoglobinopathy",
        verbatim_source_sentence="The applicant must be suffering from Thalassemia or Haemophilia.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["huk"] = SchemeEligibilityRule(
        scheme_id="huk",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_huk_res, c_huk_diag])
    )

    # 13. mcuf: Medical Check-Up facility (UKBOCWWB)
    # Registered Construction Worker
    c_mcuf_reg = SingleCriterion(
        criterion_id="mcuf_c1", attribute=AttributeName.REGISTERED_WORKER, operator=Operator.EQ, target_value=True,
        verbatim_source_sentence="The applicant must be a construction worker registered with the Uttarakhand Building and Other Construction Workers Welfare Board.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["mcuf"] = SchemeEligibilityRule(
        scheme_id="mcuf",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_mcuf_reg])
    )

    # 14. sghs: State Government Health Scheme
    # Govt Employee
    c_sghs_emp = SingleCriterion(
        criterion_id="sghs_c1", attribute=AttributeName.OCCUPATION_CATEGORY, operator=Operator.IN, target_value=["govt_employee", "pensioner"],
        verbatim_source_sentence="All government employees and pensioners of Uttarakhand who have obtained Golden Cards and make monthly contributions are eligible under the scheme.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["sghs"] = SchemeEligibilityRule(
        scheme_id="sghs",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_sghs_emp]),
        unmodeled_discretionary_conditions="Who have obtained Golden Cards and make monthly contributions."
    )

    # 15. snsukbocwwb: Sanitary Napkin Scheme (UKBOCWWB)
    # Registered Construction Worker + Female
    c_snsb_reg = SingleCriterion(
        criterion_id="snsukbocwwb_c1", attribute=AttributeName.REGISTERED_WORKER, operator=Operator.EQ, target_value=True,
        verbatim_source_sentence="The applicant must be a registered construction worker with the Uttarakhand Building and Other Construction Workers Welfare Board.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_snsb_fem = SingleCriterion(
        criterion_id="snsukbocwwb_c2", attribute=AttributeName.GENDER, operator=Operator.EQ, target_value="female",
        verbatim_source_sentence="The benefits of the scheme will be provided to the daughters of registered construction workers and to women construction workers registered with the Board.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["snsukbocwwb"] = SchemeEligibilityRule(
        scheme_id="snsukbocwwb",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_snsb_reg, c_snsb_fem])
    )

    # 16. ahlfscty: Healthy Lifestyle for School Children through Ayurvidya
    # Student + Res Uttarakhand
    c_ahl_stu = SingleCriterion(
        criterion_id="ahlfscty_c1", attribute=AttributeName.IS_STUDENT, operator=Operator.EQ, target_value=True,
        verbatim_source_sentence="The beneficiary must be a student enrolled in a government school in Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    c_ahl_res = SingleCriterion(
        criterion_id="ahlfscty_c2", attribute=AttributeName.STATE_RESIDENCE, operator=Operator.EQ, target_value="Uttarakhand",
        verbatim_source_sentence="The beneficiary must be a student enrolled in a government school in Uttarakhand.",
        is_mandatory=True, review_status=ReviewStatus.VERIFIED
    )
    rules["ahlfscty"] = SchemeEligibilityRule(
        scheme_id="ahlfscty",
        rule_group=CriterionGroup(operator=LogicalGroupOperator.ALL, criteria=[c_ahl_stu, c_ahl_res])
    )

    return rules

