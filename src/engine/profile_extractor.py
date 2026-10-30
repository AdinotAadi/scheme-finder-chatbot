"""
profile_extractor.py - Extracts user demographic attributes from natural conversation history.
Maintains stateful user profile across conversational turns.
"""

import re
from typing import Dict, Any, List, Optional
from src.schema.rules import UserProfile

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Puducherry", "Chandigarh", "Jammu and Kashmir", "Ladakh"
]

def extract_attributes_from_messages(messages: List[Dict[str, str]], current_profile: Optional[UserProfile] = None) -> UserProfile:
    """
    Scans entire user conversation history to incrementally populate UserProfile attributes.
    """
    profile_dict = current_profile.model_dump() if current_profile else {}
    
    user_texts = " ".join([m["content"] for m in messages if m["role"] == "user"]).lower()

    # 1. State extraction
    if not profile_dict.get("state_residence"):
        for state in INDIAN_STATES:
            if state.lower() in user_texts:
                profile_dict["state_residence"] = state
                break

    # 2. Gender extraction (using word boundaries to avoid substring false positives like 'he' in 'health')
    if not profile_dict.get("gender"):
        female_patterns = [r"\bgirl\b", r"\bwoman\b", r"\bfemale\b", r"\bmother\b", r"\blady\b", r"\bshe\b", r"\bdaughter\b", r"\bpregnant\b", r"\blactating\b"]
        male_patterns = [r"\bman\b", r"\bmale\b", r"\bboy\b", r"\bson\b", r"\bfather\b"]
        
        if any(re.search(pat, user_texts) for pat in female_patterns):
            profile_dict["gender"] = "female"
        elif any(re.search(pat, user_texts) for pat in male_patterns):
            profile_dict["gender"] = "male"

    # 3. Age extraction (e.g., "17-year-old", "16 years old", "age 24", "am 16")
    if profile_dict.get("age") is None:
        age_patterns = [
            r"\b([0-9]{1,2})\s*[-]?\s*year[- ]old\b",
            r"\b(?:i am|age|aged|am)\s*([0-9]{1,2})\b",
            r"\b([0-9]{1,2})\s*(?:years?\s*old|yo|yr|yrs)\b"
        ]
        for pat in age_patterns:
            m = re.search(pat, user_texts)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 100:
                    profile_dict["age"] = val
                    break

    # 4. Pregnancy & Lactation
    if "pregnant" in user_texts or "expecting" in user_texts:
        profile_dict["is_pregnant"] = True
        profile_dict["gender"] = "female"
    if "lactating" in user_texts or "nursing" in user_texts or "breastfeeding" in user_texts:
        profile_dict["is_lactating"] = True
        profile_dict["gender"] = "female"

    # 5. Student status
    if any(w in user_texts for w in ["student", "studying", "college", "school"]):
        profile_dict["is_student"] = True

    # 6. Occupation category / worker status
    if any(w in user_texts for w in ["construction", "labor", "labour", "bocw", "daily wage"]):
        profile_dict["occupation_category"] = "construction_worker"
        profile_dict["registered_worker"] = True
    elif any(w in user_texts for w in ["govt employee", "government employee", "pensioner"]):
        profile_dict["occupation_category"] = "govt_employee"

    # 7. Annual income
    if profile_dict.get("annual_income_inr") is None:
        inc_match = re.search(r"\b(?:income|earn|salary|rupees|rs\.?|inr)\s*(?:is|of)?\s*([0-9,]+)\b", user_texts)
        if inc_match:
            try:
                clean_num = float(inc_match.group(1).replace(",", ""))
                profile_dict["annual_income_inr"] = clean_num
            except Exception:
                pass

    return UserProfile(**profile_dict)

def get_missing_essential_attributes(profile: UserProfile) -> List[str]:
    """
    Identifies which essential filters are still missing before scheme recommendations can be made.
    Essential triage attributes:
      1. State of residence (State schemes depend heavily on domicile)
      2. Gender
      3. Age
    """
    missing = []
    if not profile.state_residence:
        missing.append("state_residence")
    if not profile.gender:
        missing.append("gender")
    if profile.age is None:
        missing.append("age")
    return missing
