"""
form_autofill.py - Maps conversational UserProfile attributes to formal application form models.
Supports Universal Multi-Domain auto-mapping across all 145+ schemes in the database.
"""

import re
from typing import Dict, Any, Tuple, List, Optional
from src.schema.rules import UserProfile
from src.schema.forms import (
    RAN_HMDG_ApplicationForm,
    DelhiArogyaNidhi_ApplicationForm,
    UniversalWelfareApplicationForm,
    WelfareDomain,
    GrantType,
    HospitalType
)


class FormAutoFillEngine:
    """Orchestrates demographic data mapping from chat to official government forms."""

    @staticmethod
    def detect_scheme_domain(scheme_dict: Dict[str, Any]) -> Tuple[WelfareDomain, str, str]:
        """
        Infers the welfare domain and appropriate attestation authority from scheme content.
        Uses priority-ranked keyword scoring to avoid cross-domain collisions.
        Returns (domain, department_name, attestation_authority_title).
        """
        text = f"{scheme_dict.get('name', '')} {scheme_dict.get('short_description', '')} {scheme_dict.get('eligibility_verbatim', '')} {scheme_dict.get('benefits', '')}".lower()
        
        # Priority keyword buckets
        scores = {
            WelfareDomain.EDUCATION_SCHOLARSHIP: sum(text.count(w) for w in ["scholarship", "student", "school", "college", "education", "stipend", "tuition", "bicycle", "adolescent girl"]),
            WelfareDomain.LABOUR_EMPLOYMENT: sum(text.count(w) for w in ["bocw", "construction worker", "unorganized worker", "shramik", "labor board", "labour board", "registered worker"]),
            WelfareDomain.MATERNAL_CHILD: sum(text.count(w) for w in ["pregnant", "maternal", "maternity", "lactating", "infant", "anganwadi", "pushti", "poshan", "khushiyon ki sawari"]),
            WelfareDomain.HEALTH_MEDICAL: sum(text.count(w) for w in ["hospital", "medical", "disease", "treatment", "doctor", "medicine", "arogya", "swasthya", "ambulance", "surgery", "clinic"])
        }
        
        # Pick domain with highest score, defaulting to GENERAL_SOCIAL_SECURITY
        best_domain = max(scores, key=scores.get)
        if scores[best_domain] == 0:
            best_domain = WelfareDomain.GENERAL_SOCIAL_SECURITY

        domain_meta = {
            WelfareDomain.EDUCATION_SCHOLARSHIP: (
                "Department of School & Higher Education",
                "Principal / Headmaster of the Enrolled Institution"
            ),
            WelfareDomain.LABOUR_EMPLOYMENT: (
                "Building & Other Construction Workers (BOCW) Welfare Board",
                "Assistant Labour Commissioner / Labour Enforcement Officer"
            ),
            WelfareDomain.MATERNAL_CHILD: (
                "Department of Women Empowerment & Child Development",
                "Child Development Project Officer (CDPO) / Anganwadi Supervisor"
            ),
            WelfareDomain.HEALTH_MEDICAL: (
                "Department of Medical Health & Family Welfare",
                "Chief Medical Officer / Medical Superintendent"
            ),
            WelfareDomain.GENERAL_SOCIAL_SECURITY: (
                "Department of Social Welfare & Empowerment",
                "District Social Welfare Officer / Tehsildar"
            )
        }
        dept, auth = domain_meta[best_domain]
        return best_domain, dept, auth

    @staticmethod
    def map_to_universal_form(
        scheme_dict: Dict[str, Any],
        profile: UserProfile,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[UniversalWelfareApplicationForm, List[str]]:
        """
        Generates a comprehensive, universal application form dynamically tailored
        to ANY of the 145+ schemes in the database.
        """
        data = extracted_data or {}
        domain, default_dept, default_auth = FormAutoFillEngine.detect_scheme_domain(scheme_dict)
        
        # 1. Applicant Core Demographics
        applicant_name = data.get("applicant_name") or data.get("patient_name") or data.get("name") or "Beneficiary Citizen"
        applicant_age = data.get("applicant_age") or data.get("patient_age") or profile.age
        applicant_gender = profile.gender.capitalize() if profile.gender else "Female"
        
        # 2. Address & Jurisdiction
        state = scheme_dict.get("state") or profile.state_residence or "Uttarakhand"
        district = profile.district_residence or "Haridwar"
        address = data.get("permanent_address") or f"Village/Town, {district}, {state}, India"
        
        # 3. Income Conversion
        monthly_income = 0.0
        if profile.annual_income_inr:
            monthly_income = round(profile.annual_income_inr / 12.0, 2)
        elif data.get("monthly_family_income_inr"):
            monthly_income = float(data["monthly_family_income_inr"])
        elif data.get("monthly_income_inr"):
            monthly_income = float(data["monthly_income_inr"])
            
        # 4. Parse Document Checklist from Verbatim Source
        doc_raw = scheme_dict.get("documents_required") or scheme_dict.get("documents_required_verbatim") or ""
        checklist = []
        if doc_raw:
            # Clean lines and bullet points
            lines = [l.strip("-*• \t\n") for l in re.split(r"[\n\r;]", doc_raw) if len(l.strip()) > 3]
            checklist = lines[:6]
        if not checklist:
            checklist = [
                "1. Self-attested copy of Domicile / Residence Certificate",
                "2. Attested copy of Monthly Family Income Certificate (Issued by Tehsildar / SDM)",
                "3. Attested copy of BPL / Antyodaya / Priority Ration Card",
                "4. Copy of Aadhaar Card of Applicant",
                "5. Bank Passbook photocopy showing Account No. and IFSC Code"
            ]

        # 5. Extract Domain Specific Attributes
        domain_attrs = {}
        if domain == WelfareDomain.HEALTH_MEDICAL:
            domain_attrs["Name of Disease / Medical Condition"] = data.get("disease_name") or "Severe Medical Condition Requiring Treatment"
            domain_attrs["Treating Hospital Name & Location"] = data.get("hospital_name") or "Government Medical College / AIIMS"
            domain_attrs["Hospital Registration / OPD No."] = data.get("hospital_registration_no") or "Attached with estimate"
            domain_attrs["Estimated Financial Assistance Required"] = f"₹ {float(data.get('financial_assistance_required_inr', 150000.0)):,.2f}"
        elif domain == WelfareDomain.MATERNAL_CHILD:
            domain_attrs["Current Pregnancy / Lactation Status"] = "Pregnant (6 Months)" if profile.is_pregnant else "Eligible Mother / Child"
            domain_attrs["Local Anganwadi Centre (AWC) Name"] = data.get("anganwadi_name") or "Local Sector Anganwadi Centre"
            domain_attrs["Mother and Child Protection (MCP) Card No."] = data.get("mcp_card_no") or "Enclosed"
        elif domain == WelfareDomain.EDUCATION_SCHOLARSHIP:
            domain_attrs["Educational Institution Enrolled"] = data.get("school_name") or "Government Inter College / University"
            domain_attrs["Class / Degree Programme"] = data.get("class_enrolled") or "Class 12"
            domain_attrs["Enrollment / Roll Number"] = data.get("roll_no") or "Enclosed on ID card"
        elif domain == WelfareDomain.LABOUR_EMPLOYMENT:
            domain_attrs["BOCW Labour Board Registration Number"] = data.get("bocw_regn_no") or "BOCW-UK-Active"
            domain_attrs["Trade / Nature of Construction Work"] = data.get("trade") or "Unorganized Construction Worker"
            domain_attrs["Nominee Name & Relationship"] = data.get("nominee") or "Spouse / Dependent"
        else:
            domain_attrs["Nature of Benefit Claimed"] = "Social Security Welfare Allowance"
            domain_attrs["Local Ward / Gram Panchayat"] = district

        form = UniversalWelfareApplicationForm(
            scheme_id=scheme_dict.get("scheme_id") or "general_scheme",
            scheme_name=scheme_dict.get("name") or "Government Welfare Scheme",
            administering_department=default_dept,
            jurisdiction_level=scheme_dict.get("level") or "State",
            state_residence=state,
            domain=domain,
            applicant_name=applicant_name,
            applicant_age=applicant_age,
            applicant_gender=applicant_gender,
            father_or_spouse_name=data.get("parent_name") or data.get("father_or_spouse_name") or "Family Head",
            permanent_address=address,
            mobile_no=data.get("mobile_no"),
            email=data.get("email"),
            monthly_family_income_inr=monthly_income,
            caste_category=profile.social_category or "General",
            ration_card_no=data.get("ration_card_no") or ("BPL-Card-Enclosed" if profile.is_bpl else None),
            aadhaar_no=data.get("aadhaar_no"),
            bank_account_no=data.get("bank_account_no") or "DBT-Linked Account",
            bank_ifsc=data.get("bank_ifsc") or "SBIN0001234",
            domain_attributes=domain_attrs,
            attestation_authority_title=default_auth,
            official_documents_checklist=checklist
        )

        missing = []
        if not data.get("applicant_name") and not data.get("name"):
            missing.append("Applicant Legal Name")
        if not form.applicant_age:
            missing.append("Applicant Age")
        if not form.mobile_no:
            missing.append("Mobile Number")
            
        return form, missing

    @staticmethod
    def map_to_ran_hmdg(
        profile: UserProfile,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[RAN_HMDG_ApplicationForm, List[str]]:
        """Maps known profile and conversation details to RAN_HMDG_ApplicationForm."""
        data = extracted_data or {}
        patient_name = data.get("patient_name") or data.get("name") or "Beneficiary"
        patient_age = data.get("patient_age") or profile.age
        patient_gender = profile.gender.capitalize() if profile.gender else "Female"
        
        address_parts = []
        if profile.district_residence:
            address_parts.append(profile.district_residence)
        if profile.state_residence:
            address_parts.append(profile.state_residence)
        permanent_address = data.get("permanent_address") or (", ".join(address_parts) if address_parts else "India")
        
        monthly_income = 0.0
        if profile.annual_income_inr:
            monthly_income = round(profile.annual_income_inr / 12.0, 2)
        elif data.get("monthly_income_inr"):
            monthly_income = float(data["monthly_income_inr"])
            
        form = RAN_HMDG_ApplicationForm(
            grant_type=GrantType.RAN,
            patient_name=patient_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
            permanent_address=permanent_address,
            correspondence_address=data.get("correspondence_address") or permanent_address,
            email=data.get("email"),
            mobile_no=data.get("mobile_no"),
            parent_name=data.get("parent_name"),
            spouse_name=data.get("spouse_name"),
            applicant_name=data.get("applicant_name") or patient_name,
            applicant_relationship=data.get("applicant_relationship", "Self"),
            disease_name=data.get("disease_name") or "Severe Medical Condition (See Doctor Estimate)",
            hospital_name=data.get("hospital_name") or "Government Super Specialty Hospital / AIIMS",
            hospital_registration_no=data.get("hospital_registration_no"),
            hospital_type=HospitalType.GOVERNMENT,
            is_operated=bool(data.get("is_operated", False)),
            operation_date=data.get("operation_date"),
            is_govt_employee_or_pensioner=bool(data.get("is_govt_employee_or_pensioner", False)),
            monthly_income_inr=monthly_income,
            income_certificate_issuer=data.get("income_certificate_issuer") or "Tehsildar / SDM",
            ration_card_no=data.get("ration_card_no"),
            aadhaar_no=data.get("aadhaar_no"),
            financial_assistance_required_inr=float(data.get("financial_assistance_required_inr", 150000.0)),
            other_assistance_received_details=data.get("other_assistance_received_details", "None")
        )
        
        missing = []
        if not data.get("patient_name") and not data.get("name"):
            missing.append("Patient Full Name")
        if not form.patient_age:
            missing.append("Patient Age")
        return form, missing

    @staticmethod
    def map_to_delhi_arogya_nidhi(
        profile: UserProfile,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[DelhiArogyaNidhi_ApplicationForm, List[str]]:
        """Maps known profile and conversation details to DelhiArogyaNidhi_ApplicationForm."""
        data = extracted_data or {}
        patient_name = data.get("patient_name") or data.get("name") or "Beneficiary"
        patient_age = data.get("patient_age") or profile.age
        address = data.get("residential_address") or (
            f"{profile.district_residence or 'Delhi'}, Delhi, India" if profile.state_residence == "Delhi" else "Delhi, India"
        )
        
        monthly_income = 0.0
        if profile.annual_income_inr:
            monthly_income = round(profile.annual_income_inr / 12.0, 2)
        elif data.get("monthly_family_income_inr"):
            monthly_income = float(data["monthly_family_income_inr"])
            
        form = DelhiArogyaNidhi_ApplicationForm(
            grant_type=GrantType.DAN,
            patient_name=patient_name,
            patient_age=patient_age,
            parent_or_husband_name=data.get("parent_or_husband_name"),
            residential_address=address,
            domicile_duration_years=int(data.get("domicile_duration_years", 3)),
            disease_name=data.get("disease_name") or "Medical Illness Requiring Financial Aid",
            hospital_name=data.get("hospital_name") or "Govt Hospital of NCT of Delhi",
            opd_regn_no=data.get("opd_regn_no"),
            financial_assistance_required_inr=float(data.get("financial_assistance_required_inr", 100000.0)),
            is_cyclical_treatment=bool(data.get("is_cyclical_treatment", False)),
            monthly_family_income_inr=monthly_income,
            income_certificate_sdm_issued=True,
            is_central_or_state_govt_employee=False,
            prior_assistance_details=data.get("prior_assistance_details", "None"),
            deponent_relationship=data.get("deponent_relationship", "Self")
        )
        
        missing = []
        if not data.get("patient_name") and not data.get("name"):
            missing.append("Patient Full Name")
        if not form.patient_age:
            missing.append("Patient Age")
        return form, missing
