"""
forms.py - Strongly-typed Pydantic schemas for government welfare application forms.
Includes domain-specific forms and a Universal Multi-Domain Welfare Application Model.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WelfareDomain(str, Enum):
    HEALTH_MEDICAL = "Health & Medical Assistance"
    MATERNAL_CHILD = "Maternal, Infant & Child Welfare"
    EDUCATION_SCHOLARSHIP = "Education, Student & Girl Child Aid"
    LABOUR_EMPLOYMENT = "Unorganized & Construction Labour Welfare"
    GENERAL_SOCIAL_SECURITY = "Social Security, Disability & Financial Aid"


class GrantType(str, Enum):
    RAN = "Rashtriya Arogya Nidhi (RAN)"
    HMDG = "Health Minister's Discretionary Grant (HMDG)"
    DAN = "Delhi Arogya Nidhi (DAN)"
    DAK = "Delhi Arogya Kosh (DAK)"
    UNIVERSAL = "Universal Government Welfare Grant"


class HospitalType(str, Enum):
    GOVERNMENT = "Government"
    PRIVATE = "Private"
    AUTONOMOUS_AIIMS = "Autonomous / AIIMS / Central Institute"


class UniversalWelfareApplicationForm(BaseModel):
    """
    Polymorphic, universal application form schema applicable across all 145+
    central and state government welfare schemes.
    """
    # Scheme & Issuing Authority Context
    scheme_id: str = Field(..., description="Unique scheme identifier slug")
    scheme_name: str = Field(..., description="Official scheme name")
    administering_department: str = Field(default="Government Department / Ministry", description="Administering authority")
    jurisdiction_level: str = Field(default="State", description="Central or State/UT")
    state_residence: str = Field(..., description="Domicile state or Union Territory")
    domain: WelfareDomain = Field(default=WelfareDomain.HEALTH_MEDICAL, description="Domain category")

    # Core Citizen Identity (Common to 100% of Indian forms)
    applicant_name: str = Field(..., description="Full legal name of the applicant")
    applicant_age: Optional[int] = Field(None, description="Age in years")
    applicant_gender: Optional[str] = Field("Female", description="Gender")
    father_or_spouse_name: Optional[str] = Field(None, description="Father / Mother / Husband name")
    permanent_address: str = Field(..., description="Complete residential address with district and state")
    mobile_no: Optional[str] = Field(None, description="10-digit mobile number")
    email: Optional[str] = Field(None, description="Email address if available")

    # Socio-Economic & Entitlement Identifiers
    monthly_family_income_inr: float = Field(default=0.0, description="Monthly household income in INR")
    caste_category: Optional[str] = Field(None, description="General, SC, ST, OBC, EWS")
    ration_card_no: Optional[str] = Field(None, description="BPL / Antyodaya / Priority Ration Card No")
    aadhaar_no: Optional[str] = Field(None, description="12-digit Aadhaar number")
    bank_account_no: Optional[str] = Field(None, description="Direct Benefit Transfer (DBT) Bank Account No")
    bank_ifsc: Optional[str] = Field(None, description="Bank Branch IFSC Code")

    # Dynamic Domain-Specific Particulars
    # E.g. Health: {"disease": "...", "hospital": "..."}
    # Education: {"school_name": "...", "class_enrolled": "..."}
    # Labour: {"bocw_registration_no": "...", "trade": "..."}
    domain_attributes: Dict[str, Any] = Field(default_factory=dict, description="Domain specific particulars")

    # Official Attestation & Required Checklist
    attestation_authority_title: str = Field(
        default="Competent Authorized Officer",
        description="Designation of official required to sign (e.g. Medical Superintendent, Principal, Tehsildar, Labour Officer)"
    )
    official_documents_checklist: List[str] = Field(
        default_factory=list,
        description="Itemized document attachments required per official portal records"
    )


class RAN_HMDG_ApplicationForm(BaseModel):
    """Specific form for Rashtriya Arogya Nidhi (RAN) & HMDG - MoHFW."""
    grant_type: GrantType = Field(default=GrantType.RAN, description="RAN or HMDG")
    patient_name: str = Field(..., description="Full name of the patient in block letters")
    patient_age: Optional[int] = Field(None, description="Age of patient")
    patient_gender: Optional[str] = Field("Female", description="Gender of the patient")
    permanent_address: str = Field(..., description="Permanent residential address with PIN code")
    correspondence_address: Optional[str] = Field(None, description="Address for correspondence")
    email: Optional[str] = Field(None, description="Email address if available")
    mobile_no: Optional[str] = Field(None, description="Mobile / Telephone number")
    parent_name: Optional[str] = Field(None, description="Name of father / mother")
    spouse_name: Optional[str] = Field(None, description="Name of wife / husband")
    applicant_name: Optional[str] = Field(None, description="Name of applicant if different from patient")
    applicant_relationship: Optional[str] = Field("Self", description="Relationship of applicant to patient")
    disease_name: str = Field(..., description="Name of disease / clinical condition")
    hospital_name: str = Field(..., description="Treating Hospital Name")
    hospital_registration_no: Optional[str] = Field(None, description="Hospital Registration number")
    hospital_type: HospitalType = Field(default=HospitalType.GOVERNMENT, description="Government or Private")
    is_operated: bool = Field(default=False, description="Whether patient has been operated")
    operation_date: Optional[str] = Field(None, description="Date of operation if applicable")
    is_govt_employee_or_pensioner: bool = Field(default=False, description="Whether employee of Govt/PSU")
    govt_office_details: Optional[str] = Field(None, description="Details of office if working in Govt/PSU")
    monthly_income_inr: float = Field(default=0.0, description="Monthly income from all sources in INR")
    income_certificate_issuer: Optional[str] = Field(None, description="Designation of issuing authority")
    ration_card_no: Optional[str] = Field(None, description="Ration card number")
    aadhaar_no: Optional[str] = Field(None, description="Aadhaar number")
    financial_assistance_required_inr: float = Field(default=0.0, description="Amount recommended by treating doctor")
    other_assistance_received_details: Optional[str] = Field("None", description="Details of other assistance")


class DelhiArogyaNidhi_ApplicationForm(BaseModel):
    """Specific form for Delhi Arogya Nidhi / Kosh (DAN / DAK) - Govt of NCT of Delhi."""
    grant_type: GrantType = Field(default=GrantType.DAN, description="DAN or DAK")
    patient_name: str = Field(..., description="Full name of the patient")
    patient_age: Optional[int] = Field(None, description="Age of patient")
    parent_or_husband_name: Optional[str] = Field(None, description="Father or Husband's name")
    residential_address: str = Field(..., description="Residential address in Delhi")
    domicile_duration_years: int = Field(default=3, description="Proof of domicile in Delhi (minimum 3 years)")
    disease_name: str = Field(..., description="Name of disease and treatment required")
    hospital_name: str = Field(..., description="Name of hospital where taking treatment")
    opd_regn_no: Optional[str] = Field(None, description="OPD / Registration number")
    financial_assistance_required_inr: float = Field(default=0.0, description="Amount required as per estimate")
    is_cyclical_treatment: bool = Field(default=False, description="Whether undergoing cyclical treatment")
    monthly_family_income_inr: float = Field(default=0.0, description="Monthly family income from all sources")
    income_certificate_sdm_issued: bool = Field(default=True, description="Whether SDM income certificate attached")
    is_central_or_state_govt_employee: bool = Field(default=False, description="Govt employee status")
    prior_assistance_details: Optional[str] = Field("None", description="Prior assistance taken earlier")
    deponent_relationship: str = Field(default="Self", description="Self, Father, Husband or Guardian")
