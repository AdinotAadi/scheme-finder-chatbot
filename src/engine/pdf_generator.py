"""
pdf_generator.py - Generates clean, authentic, print-ready official PDF application forms.
Supports:
1. Specific RAN/HMDG Central Government Medical Forms
2. Specific Delhi Arogya Nidhi/Kosh Forms
3. Universal Multi-Domain Welfare Forms across all 145+ Central and State Schemes.
"""

import io
from typing import Union
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from src.schema.forms import (
    RAN_HMDG_ApplicationForm,
    DelhiArogyaNidhi_ApplicationForm,
    UniversalWelfareApplicationForm
)


class ApplicationFormPDFGenerator:
    """Generates official government application form PDFs from validated form models."""

    @staticmethod
    def generate_universal_welfare_pdf(form: UniversalWelfareApplicationForm) -> bytes:
        """
        Synthesizes a standardized, professional, print-ready official application form
        dynamically customized for ANY government welfare scheme.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "UnivTitle",
            parent=styles["Heading1"],
            fontSize=13,
            leading=16,
            alignment=1,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0d233a")
        )
        subtitle_style = ParagraphStyle(
            "UnivSubTitle",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            alignment=1,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#333333")
        )
        sub_dept_style = ParagraphStyle(
            "UnivDept",
            parent=styles["Normal"],
            fontSize=9.0,
            leading=12,
            alignment=1,
            fontName="Helvetica",
            textColor=colors.HexColor("#555555")
        )
        section_style = ParagraphStyle(
            "UnivSection",
            parent=styles["Heading2"],
            fontSize=10.0,
            leading=13,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0d233a")
        )
        body_style = ParagraphStyle(
            "UnivBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            fontName="Helvetica"
        )
        body_bold = ParagraphStyle(
            "UnivBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        # 1. Official Government Header
        elements.append(Paragraph("APPLICATION FORM FOR WELFARE ASSISTANCE", title_style))
        elements.append(Paragraph(f"<b>{form.administering_department.upper()}</b>", subtitle_style))
        elements.append(Paragraph(f"<b>Scheme:</b> {form.scheme_name} (Jurisdiction: {form.jurisdiction_level} / {form.state_residence})", sub_dept_style))
        elements.append(Spacer(1, 10))

        # Domain Badge Row
        domain_badge = f"<b>Welfare Category:</b> {form.domain.value} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Application Reference:</b> SF-APP-{form.scheme_id.upper()}-2026"
        elements.append(Paragraph(domain_badge, body_bold))
        elements.append(Spacer(1, 8))

        # 2. Part 1: Applicant Demographic Particulars Table
        table_rows = [
            [Paragraph("<b>No.</b>", body_bold), Paragraph("<b>Field Description</b>", body_bold), Paragraph("<b>Verified Particulars (Auto-Filled)</b>", body_bold)],
            [Paragraph("1.", body_style), Paragraph("Full Name of Applicant / Beneficiary", body_style), Paragraph(f"<b>{form.applicant_name.upper()}</b>", body_style)],
            [Paragraph("2.", body_style), Paragraph("Age & Gender", body_style), Paragraph(f"{form.applicant_age or '____'} Years / {form.applicant_gender or '____'}", body_style)],
            [Paragraph("3.", body_style), Paragraph("Father's / Mother's / Husband's Name", body_style), Paragraph(form.father_or_spouse_name or "________________________________", body_style)],
            [Paragraph("4.", body_style), Paragraph("Residential Address & Domicile", body_style), Paragraph(f"{form.permanent_address}", body_style)],
            [Paragraph("5.", body_style), Paragraph("Contact Details", body_style), Paragraph(f"Mobile: {form.mobile_no or '________________'} | Email: {form.email or 'N/A'}", body_style)],
            [Paragraph("6.", body_style), Paragraph("Monthly Family Income & Category", body_style), Paragraph(f"₹ {form.monthly_family_income_inr:,.2f} / month | Social Category: {form.caste_category or 'General'}", body_style)],
            [Paragraph("7.", body_style), Paragraph("Ration Card / Food Security ID", body_style), Paragraph(form.ration_card_no or "Attached Copy [  ]", body_style)],
            [Paragraph("8.", body_style), Paragraph("Aadhaar Card Number", body_style), Paragraph(form.aadhaar_no or "Attached Copy [  ]", body_style)],
            [Paragraph("9.", body_style), Paragraph("Bank Account & IFSC (for DBT Transfer)", body_style), Paragraph(f"A/C: {form.bank_account_no} (IFSC: {form.bank_ifsc})", body_style)],
        ]

        # Append dynamic domain attributes into the table
        row_num = 10
        for attr_k, attr_v in form.domain_attributes.items():
            table_rows.append([
                Paragraph(f"{row_num}.", body_style),
                Paragraph(f"<b>{attr_k}</b>", body_style),
                Paragraph(f"{attr_v}", body_style)
            ])
            row_num += 1

        main_table = Table(table_rows, colWidths=[0.4 * inch, 2.7 * inch, 4.0 * inch])
        main_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f4f8")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0d233a")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#b0bec5")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(main_table)
        elements.append(Spacer(1, 10))

        # 3. Applicant Declaration
        declaration_text = (
            "<b>APPLICANT'S DECLARATION:</b> I hereby declare that all information furnished in this application is "
            "true, complete and verified against my original identity and income records. I fulfill all domicile and eligibility "
            "conditions governing this scheme. If any particulars are found false or misleading at any stage, my claim shall stand canceled."
        )
        elements.append(Paragraph(declaration_text, body_style))
        elements.append(Spacer(1, 12))

        # Signature row
        sig_data = [
            [Paragraph("<b>Date:</b> " + "________________", body_style), Paragraph("<b>Signature / Thumb Impression of Applicant</b>", body_style)]
        ]
        elements.append(Table(sig_data, colWidths=[3.5 * inch, 3.6 * inch]))
        elements.append(Spacer(1, 12))

        # 4. Official Verification & Attestation Section (Department Specific)
        elements.append(Paragraph(f"<b>OFFICIAL ATTESTATION: TO BE COMPLETED BY {form.attestation_authority_title.upper()}</b>", section_style))
        elements.append(Spacer(1, 4))
        
        attest_text = (
            f"Certified that the applicant <b>{form.applicant_name}</b> has been examined / verified. "
            f"The claims made under <b>{form.scheme_name}</b> are recommended for sanction as per departmental guidelines."
        )
        elements.append(Paragraph(attest_text, body_style))
        elements.append(Spacer(1, 18))

        officer_sig = [
            [Paragraph("<b>Office Seal & Date:</b> _______________", body_style), Paragraph(f"<b>Signature of {form.attestation_authority_title}</b>", body_style)]
        ]
        elements.append(Table(officer_sig, colWidths=[3.5 * inch, 3.6 * inch]))
        elements.append(Spacer(1, 10))

        # 5. Verified Document Checklist
        elements.append(Paragraph("<b>MANDATORY ENCLOSURES & DOCUMENT CHECKLIST:</b>", body_bold))
        checklist_items = "<br/>".join([f"[  ] {item}" for item in form.official_documents_checklist])
        elements.append(Paragraph(checklist_items, body_style))

        # Build document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_ran_hmdg_pdf(form: RAN_HMDG_ApplicationForm) -> bytes:
        """Generates standard printable PDF for Rashtriya Arogya Nidhi (RAN) & HMDG."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=13,
            leading=16,
            alignment=1,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0d233a")
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            alignment=1,
            fontName="Helvetica",
            textColor=colors.HexColor("#333333")
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=10.5,
            leading=14,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0d233a")
        )
        body_style = ParagraphStyle(
            "FormBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            fontName="Helvetica"
        )
        body_bold = ParagraphStyle(
            "FormBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        elements.append(Paragraph("APPLICATION FOR FINANCIAL ASSISTANCE", title_style))
        elements.append(Paragraph("<b>MINISTRY OF HEALTH & FAMILY WELFARE, GOVERNMENT OF INDIA</b>", subtitle_style))
        elements.append(Paragraph("Under Rashtriya Arogya Nidhi (RAN) & Health Minister’s Discretionary Grant (HMDG)", subtitle_style))
        elements.append(Spacer(1, 12))

        scheme_check = f"<b>Selected Scheme:</b> [ {'X' if 'RAN' in form.grant_type.value else '  '} ] RASHTRIYA AROGYA NIDHI (RAN) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [ {'X' if 'HMDG' in form.grant_type.value else '  '} ] HEALTH MINISTER'S DISCRETIONARY GRANT (HMDG)"
        elements.append(Paragraph(scheme_check, body_bold))
        elements.append(Spacer(1, 8))

        table_data = [
            [Paragraph("<b>Col</b>", body_bold), Paragraph("<b>Field Description</b>", body_bold), Paragraph("<b>Particulars (Auto-Filled)</b>", body_bold)],
            [Paragraph("1", body_style), Paragraph("Name of the Patient (Block Letters)", body_style), Paragraph(f"<b>{form.patient_name.upper()}</b>", body_style)],
            [Paragraph("2", body_style), Paragraph("Age & Gender", body_style), Paragraph(f"{form.patient_age or '____'} Years / {form.patient_gender or '____'}", body_style)],
            [Paragraph("3(a)", body_style), Paragraph("Permanent Address (with PIN)", body_style), Paragraph(form.permanent_address, body_style)],
            [Paragraph("3(b)", body_style), Paragraph("Address for Correspondence", body_style), Paragraph(form.correspondence_address or form.permanent_address, body_style)],
            [Paragraph("4", body_style), Paragraph("Contact Mobile & Email", body_style), Paragraph(f"Mob: {form.mobile_no or '________________'} | Email: {form.email or 'N/A'}", body_style)],
            [Paragraph("5", body_style), Paragraph("Father's / Mother's Name", body_style), Paragraph(form.parent_name or "________________________________", body_style)],
            [Paragraph("6", body_style), Paragraph("Relationship of Applicant to Patient", body_style), Paragraph(form.applicant_relationship or "Self", body_style)],
            [Paragraph("7", body_style), Paragraph("Disease from which suffering", body_style), Paragraph(f"<b>{form.disease_name}</b>", body_style)],
            [Paragraph("8", body_style), Paragraph("Govt / PSU Employee or Pensioner?", body_style), Paragraph("Yes [ ] / No [ X ]", body_style)],
            [Paragraph("9", body_style), Paragraph("Monthly Family Income & Issuer", body_style), Paragraph(f"₹ {form.monthly_income_inr:,.2f} / month (Certified by: {form.income_certificate_issuer or 'Tehsildar'})", body_style)],
            [Paragraph("10", body_style), Paragraph("Financial Assistance Required", body_style), Paragraph(f"<b>₹ {form.financial_assistance_required_inr:,.2f}</b>", body_style)],
            [Paragraph("11", body_style), Paragraph("Other Assistance Received Earlier", body_style), Paragraph(form.other_assistance_received_details or "None", body_style)],
            [Paragraph("12", body_style), Paragraph("Ration Card No. (BPL/Antyodaya)", body_style), Paragraph(form.ration_card_no or "Attached [  ]", body_style)],
            [Paragraph("13", body_style), Paragraph("Aadhaar Card No.", body_style), Paragraph(form.aadhaar_no or "Attached copy [  ]", body_style)],
        ]

        patient_table = Table(table_data, colWidths=[0.4 * inch, 2.7 * inch, 4.0 * inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f4f8")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0d233a")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#b0bec5")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(patient_table)
        elements.append(Spacer(1, 10))

        declaration_text = (
            "<b>DECLARATION:</b> I declare that the information given above is correct and complete in all respect. "
            "I have not concealed any material fact regarding my income or employment status. "
            "I understand that any false statement renders this application liable for immediate rejection."
        )
        elements.append(Paragraph(declaration_text, body_style))
        elements.append(Spacer(1, 14))

        sig_data = [
            [Paragraph("<b>Date:</b> " + "________________", body_style), Paragraph("<b>Signature / Thumb Impression of Applicant/Patient</b>", body_style)]
        ]
        elements.append(Table(sig_data, colWidths=[3.5 * inch, 3.6 * inch]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>PART 2: TO BE COMPLETED BY THE MEDICAL SUPERINTENDENT / TREATING DOCTOR</b>", section_style))
        elements.append(Spacer(1, 4))
        
        doc_data = [
            [Paragraph("1. Name of Patient & Hospital Regn No.", body_style), Paragraph(f"{form.patient_name} (Regn: {form.hospital_registration_no or '________________'})", body_style)],
            [Paragraph("2. Treating Hospital Name & Type", body_style), Paragraph(f"<b>{form.hospital_name}</b> ({form.hospital_type.value})", body_style)],
            [Paragraph("3. Clinical Diagnosis & Condition Note", body_style), Paragraph(form.disease_name, body_style)],
            [Paragraph("4. Recommended Financial Assistance", body_style), Paragraph(f"<b>₹ {form.financial_assistance_required_inr:,.2f}</b>", body_style)],
            [Paragraph("5. Official Signatures & Verification", body_style), Paragraph("\n\n___________________________________\nSignature of Treating Consultant / HOD\n(with Official Seal)", body_style)]
        ]
        doc_table = Table(doc_data, colWidths=[3.1 * inch, 4.0 * inch])
        doc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#b0bec5")),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f9fafb")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(doc_table)
        elements.append(Spacer(1, 10))

        checklist = (
            "<b>MANDATORY ATTACHMENTS CHECKLIST:</b><br/>"
            "[   ] 1. Original Medical Estimate Certificate signed by HOD / Medical Superintendent.<br/>"
            "[   ] 2. Attested copy of Monthly Income Certificate issued by Tehsildar / SDM.<br/>"
            "[   ] 3. Attested copy of BPL / Antyodaya Ration Card.<br/>"
            "[   ] 4. Attested copy of Aadhaar Card.<br/>"
            "[   ] 5. Hospital OPD / IPD admission slip and diagnostic reports."
        )
        elements.append(Paragraph(checklist, body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_delhi_arogya_nidhi_pdf(form: DelhiArogyaNidhi_ApplicationForm) -> bytes:
        """Generates standard printable PDF for Delhi Arogya Nidhi / Kosh."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DanTitle",
            parent=styles["Heading1"],
            fontSize=13,
            leading=16,
            alignment=1,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0d233a")
        )
        subtitle_style = ParagraphStyle(
            "DanSubtitle",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            alignment=1,
            fontName="Helvetica"
        )
        body_style = ParagraphStyle("DanBody", parent=styles["Normal"], fontSize=8.5, leading=11, fontName="Helvetica")
        body_bold = ParagraphStyle("DanBodyBold", parent=body_style, fontName="Helvetica-Bold")

        elements = []

        elements.append(Paragraph("APPLICATION FORM FOR FINANCIAL AID", title_style))
        elements.append(Paragraph("<b>GOVERNMENT OF NCT OF DELHI — DELHI AROGYA NIDHI / KOSH</b>", subtitle_style))
        elements.append(Paragraph("Directorate of Health Services, Swasthya Sewa Nideshalaya, F-17 Karkardooma, Delhi", subtitle_style))
        elements.append(Spacer(1, 12))

        table_data = [
            [Paragraph("<b>No.</b>", body_bold), Paragraph("<b>Description</b>", body_bold), Paragraph("<b>Applicant / Patient Particulars</b>", body_bold)],
            [Paragraph("1.", body_style), Paragraph("Name & Age of Patient", body_style), Paragraph(f"<b>{form.patient_name}</b>, Age: {form.patient_age or '____'} Years", body_style)],
            [Paragraph("2.", body_style), Paragraph("Father / Husband's Name", body_style), Paragraph(form.parent_or_husband_name or "________________________________", body_style)],
            [Paragraph("3.", body_style), Paragraph("Residential Address in Delhi<br/>(Proof of Domicile for last 3 years)", body_style), Paragraph(f"{form.residential_address}<br/>(Domicile Proof Attached: Yes)", body_style)],
            [Paragraph("4.", body_style), Paragraph("Name of Disease & Treatment", body_style), Paragraph(f"<b>{form.disease_name}</b>", body_style)],
            [Paragraph("5.", body_style), Paragraph("Hospital Name & OPD Regn. No.", body_style), Paragraph(f"<b>{form.hospital_name}</b> (OPD: {form.opd_regn_no or 'Attached'})", body_style)],
            [Paragraph("6.", body_style), Paragraph("Financial Assistance Required", body_style), Paragraph(f"<b>₹ {form.financial_assistance_required_inr:,.2f}</b> (As per Doctor's estimate)", body_style)],
            [Paragraph("7.", body_style), Paragraph("Monthly Income Certificate in Original", body_style), Paragraph(f"Monthly: ₹ {form.monthly_family_income_inr:,.2f} (Issued by SDM)", body_style)],
            [Paragraph("8.", body_style), Paragraph("Two Passport Photographs Attested", body_style), Paragraph("Attached: [ X ] Enclosed on form and estimate", body_style)],
            [Paragraph("9.", body_style), Paragraph("Assistance from any other sources?", body_style), Paragraph("None", body_style)],
            [Paragraph("10.", body_style), Paragraph("Earlier Assistance from DAN / DAK?", body_style), Paragraph(form.prior_assistance_details or "No", body_style)],
        ]

        table = Table(table_data, colWidths=[0.4 * inch, 2.7 * inch, 4.0 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f4f8")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#b0bec5")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        cert_text = (
            "It is certified that the information furnished above is true to the best of my knowledge & belief "
            "and that I am in no position at all to arrange/provide funds for the purpose stated above. "
            "I also declare that neither my parents nor I are employees of the Central / State Govt. or a local body."
        )
        elements.append(Paragraph(cert_text, body_style))
        elements.append(Spacer(1, 14))

        sig_data = [
            [Paragraph("<b>Date:</b> ______________", body_style), Paragraph("<b>Signature of the Applicant / Patient</b>", body_style)]
        ]
        elements.append(Table(sig_data, colWidths=[3.5 * inch, 3.6 * inch]))
        elements.append(Spacer(1, 14))

        elements.append(Paragraph("<b>ESTIMATE CERTIFICATE & UNDERTAKING ATTACHED</b>", body_bold))
        undertaking_text = (
            "1. Hospital Estimate Certificate signed by Treating Consultant and Medical Superintendent.<br/>"
            "2. Signed Undertaking / Affidavit declaring total family income and non-government employment.<br/>"
            "3. 3-Year Delhi Domicile proof (Voter ID / Electricity Bill / Ration Card)."
        )
        elements.append(Paragraph(undertaking_text, body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
