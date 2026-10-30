"""
synthetic_profiles.py - Ground truth synthetic user profiles with expected outcomes for Slice 4.
"""

from typing import List, Dict, Any
from src.schema.rules import UserProfile
from src.engine.evaluator import OverallSchemeCategory

# Define 10 diverse synthetic test personas representing target beneficiaries and negative controls
SYNTHETIC_TEST_CASES = [
    {
        "profile_id": "P1_adolescent_girl_haridwar",
        "description": "16yo girl residing in Haridwar, Uttarakhand. Eligible for Kishori Balika, Sanitary Napkin, Clinic.",
        "profile": UserProfile(
            age=16,
            gender="female",
            state_residence="Uttarakhand",
            district_residence="Haridwar",
            is_student=True
        ),
        "expected_categories": {
            "kbyuk": OverallSchemeCategory.POTENTIAL_MATCH,
            "snduk": OverallSchemeCategory.POTENTIAL_MATCH,
            "snsu": OverallSchemeCategory.POTENTIAL_MATCH,
            "kspc": OverallSchemeCategory.POTENTIAL_MATCH,
            "ipuk": OverallSchemeCategory.POTENTIAL_MATCH,
            "ahlfscty": OverallSchemeCategory.POTENTIAL_MATCH,
            "mcuf": OverallSchemeCategory.MORE_INFORMATION_NEEDED, # registered worker unknown
            "maternalnutritionuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE, # state is Odisha in verbatim
            "sghs": OverallSchemeCategory.MORE_INFORMATION_NEEDED
        }
    },
    {
        "profile_id": "P2_pregnant_mother_uttarakhand",
        "description": "24yo pregnant woman residing in Dehradun, Uttarakhand.",
        "profile": UserProfile(
            age=24,
            gender="female",
            state_residence="Uttarakhand",
            district_residence="Dehradun",
            is_pregnant=True
        ),
        "expected_categories": {
            "kbyuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE, # Age 24 > 18
            "snduk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE, # Age 24 > 19
            "snsu": OverallSchemeCategory.POTENTIAL_MATCH,       # All women
            "kkssuk": OverallSchemeCategory.POTENTIAL_MATCH,     # Pregnant woman in UK
            "ipuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE,   # Age 24 > 16
            "maternalnutritionuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE
        }
    },
    {
        "profile_id": "P3_male_construction_worker_uk",
        "description": "35yo registered male construction worker in Uttarakhand.",
        "profile": UserProfile(
            age=35,
            gender="male",
            state_residence="Uttarakhand",
            registered_worker=True,
            occupation_category="construction_worker"
        ),
        "expected_categories": {
            "kbyuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE, # Female only
            "snduk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE, # Female only
            "snsu": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE,  # Female only
            "snsukbocwwb": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE, # Female daughter/worker only
            "mcuf": OverallSchemeCategory.POTENTIAL_MATCH,      # Registered BOCW worker
            "ipuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE
        }
    },
    {
        "profile_id": "P4_female_construction_worker_uk",
        "description": "28yo registered female construction worker in Uttarakhand.",
        "profile": UserProfile(
            age=28,
            gender="female",
            state_residence="Uttarakhand",
            registered_worker=True,
            occupation_category="construction_worker"
        ),
        "expected_categories": {
            "mcuf": OverallSchemeCategory.POTENTIAL_MATCH,
            "snsukbocwwb": OverallSchemeCategory.POTENTIAL_MATCH, # Female registered worker
            "snsu": OverallSchemeCategory.POTENTIAL_MATCH,
            "kbyuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE    # Age 28 > 18
        }
    },
    {
        "profile_id": "P5_rajasthan_resident_control",
        "description": "20yo female residing in Rajasthan (negative control for UK domicile).",
        "profile": UserProfile(
            age=20,
            gender="female",
            state_residence="Rajasthan"
        ),
        "expected_categories": {
            "kbyuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE,
            "snduk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE,
            "108easuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE,
            "kspc": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE,
            "ipuk": OverallSchemeCategory.LIKELY_NOT_ELIGIBLE
        }
    },
    {
        "profile_id": "P6_unknown_state_and_age",
        "description": "Sparse profile: only female specified, state and age unknown.",
        "profile": UserProfile(
            gender="female"
        ),
        "expected_categories": {
            "kbyuk": OverallSchemeCategory.MORE_INFORMATION_NEEDED,
            "snduk": OverallSchemeCategory.MORE_INFORMATION_NEEDED,
            "108easuk": OverallSchemeCategory.MORE_INFORMATION_NEEDED,
            "snsu": OverallSchemeCategory.POTENTIAL_MATCH # snsu only requires female
        }
    }
]

