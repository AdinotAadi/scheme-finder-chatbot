"""
test_form_autofill.py - Unit and regression tests for Universal Multi-Domain application form auto-fill and PDF generation.
"""

import pytest
from src.schema.rules import UserProfile
from src.schema.forms import (
    RAN_HMDG_ApplicationForm,
    DelhiArogyaNidhi_ApplicationForm,
    UniversalWelfareApplicationForm,
    WelfareDomain
)
from src.engine.form_autofill import FormAutoFillEngine
from src.engine.pdf_generator import ApplicationFormPDFGenerator


def test_ran_hmdg_autofill_mapping():
    profile = UserProfile(
        age=24,
        gender="female",
        state_residence="Uttarakhand",
        district_residence="Dehradun",
        annual_income_inr=72000.0,
        is_pregnant=True
    )
    
    extracted_data = {
        "patient_name": "Sunita Devi",
        "disease_name": "Severe Chronic Kidney Disease",
        "hospital_name": "AIIMS Rishikesh",
        "ration_card_no": "BPL-UK-987654",
        "aadhaar_no": "1234-5678-9012"
    }
    
    form, missing = FormAutoFillEngine.map_to_ran_hmdg(profile, extracted_data)
    
    assert form.patient_name == "Sunita Devi"
    assert form.patient_age == 24
    assert form.patient_gender == "Female"
    assert "Dehradun" in form.permanent_address
    assert "Uttarakhand" in form.permanent_address
    assert form.monthly_income_inr == 6000.0 # 72000 / 12
    assert form.disease_name == "Severe Chronic Kidney Disease"
    assert form.hospital_name == "AIIMS Rishikesh"
    assert form.ration_card_no == "BPL-UK-987654"


def test_universal_form_education_scholarship():
    profile = UserProfile(
        age=17,
        gender="female",
        state_residence="Uttarakhand",
        district_residence="Haridwar",
        is_student=True,
        annual_income_inr=60000.0
    )
    scheme_dict = {
        "scheme_id": "kbyuk",
        "name": "Kishori Balika Yojana - Uttarakhand",
        "state": "Uttarakhand",
        "level": "State",
        "short_description": "Nutrition, student education and welfare for adolescent girls in Uttarakhand schools.",
        "documents_required": "- School enrollment ID certificate\n- Ration Card copy\n- Bank Passbook with IFSC\n- Domicile certificate"
    }
    
    form, missing = FormAutoFillEngine.map_to_universal_form(
        scheme_dict=scheme_dict,
        profile=profile,
        extracted_data={"applicant_name": "Ananya Rawat", "mobile_no": "9876543210"}
    )
    
    assert form.applicant_name == "Ananya Rawat"
    assert form.applicant_age == 17
    assert form.applicant_gender == "Female"
    assert form.domain == WelfareDomain.EDUCATION_SCHOLARSHIP
    assert form.monthly_family_income_inr == 5000.0
    assert "Haridwar" in form.permanent_address
    assert len(form.official_documents_checklist) >= 4
    
    # Test Universal PDF synthesis
    pdf_bytes = ApplicationFormPDFGenerator.generate_universal_welfare_pdf(form)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_universal_form_maternal_nutrition():
    profile = UserProfile(
        age=23,
        gender="female",
        state_residence="Uttarakhand",
        district_residence="Nainital",
        is_pregnant=True,
        annual_income_inr=48000.0
    )
    scheme_dict = {
        "scheme_id": "kkssuk",
        "name": "Khushiyon Ki Sawari Sewa",
        "state": "Uttarakhand",
        "level": "State",
        "short_description": "Free transportation and maternal nutrition care for pregnant women and newborns.",
        "documents_required": "MCP Card; Domicile Certificate; Income Certificate"
    }
    
    form, missing = FormAutoFillEngine.map_to_universal_form(
        scheme_dict=scheme_dict,
        profile=profile,
        extracted_data={"applicant_name": "Kavita Bisht", "mobile_no": "9123456780"}
    )
    
    assert form.domain == WelfareDomain.MATERNAL_CHILD
    assert form.domain_attributes["Current Pregnancy / Lactation Status"] == "Pregnant (6 Months)"
    assert "Child Development Project Officer" in form.attestation_authority_title
    
    pdf_bytes = ApplicationFormPDFGenerator.generate_universal_welfare_pdf(form)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_universal_form_construction_labour():
    profile = UserProfile(
        age=34,
        gender="male",
        state_residence="Uttarakhand",
        district_residence="Dehradun",
        registered_worker=True,
        occupation_category="construction_worker",
        annual_income_inr=84000.0
    )
    scheme_dict = {
        "scheme_id": "mcuf",
        "name": "Mukhyamantri Construction Worker Relief Fund",
        "state": "Uttarakhand",
        "level": "State",
        "short_description": "Financial assistance, medical and accident support for registered BOCW workers.",
        "documents_required": "- BOCW Labour Board Passbook\n- Aadhaar card\n- Bank passbook"
    }
    
    form, _ = FormAutoFillEngine.map_to_universal_form(
        scheme_dict=scheme_dict,
        profile=profile,
        extracted_data={"applicant_name": "Ramesh Chandra", "bocw_regn_no": "BOCW-UK-887766"}
    )
    
    assert form.domain == WelfareDomain.LABOUR_EMPLOYMENT
    assert form.domain_attributes["BOCW Labour Board Registration Number"] == "BOCW-UK-887766"
    assert "Labour" in form.attestation_authority_title
    
    pdf_bytes = ApplicationFormPDFGenerator.generate_universal_welfare_pdf(form)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_1to1_template_overlay_ran():
    from src.engine.template_overlay import OfficialTemplateOverlayEngine
    from src.schema.rules import UserProfile
    import pypdf, io

    profile = UserProfile(
        full_name="Ramesh Kumar",
        age=45,
        gender="male",
        state_residence="Delhi",
        district_residence="East Delhi",
        annual_income_inr=48000.0,
        is_bpl=True
    )

    pdf_bytes = OfficialTemplateOverlayEngine.fill_ran_hmdg_official(
        profile=profile,
        hospital_name="AIIMS New Delhi",
        disease_name="Chronic Kidney Disease",
        amount_requested=150000.0,
        applicant_name="Ramesh Kumar",
        parent_spouse_name="Shri Ram Kumar",
        contact_mobile="9876543210",
        ration_card_no="BPL-Antyodaya-07123"
    )

    assert len(pdf_bytes) > 50000
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 4
    txt_page2 = reader.pages[1].extract_text()
    assert "RAMESH KUMAR" in txt_page2
    assert "Chronic Kidney Disease" in txt_page2
