# TECHNICAL SPECIFICATION: AUTOMATED WELFARE APPLICATION ENGINE

## 1. IDENTIFICATION AND METADATA
- **Document Title**: Automated Welfare Application Form Engine Technical Specification
- **Standard**: ASD-STE100 (Simplified Technical English)
- **Document Version**: 1.0.0
- **Status**: Approved for Technical Review
- **Audience**: Systems Architects, Lead Engineers, Government Policy Reviewers, Technical Auditors

---

## 2. PURPOSE
This document describes the design, architecture, and operation of the Application Form Auto-Fill Engine.
The engine helps citizens generate completed application forms for Indian welfare schemes.
The system does not send citizen personal information to cloud servers. All document operations execute on the local computer.

---

## 3. SCOPE
The software component includes two modules:
1. **The Universal Multi-Domain Form Engine**: Generates single-page standardized intake forms for all 145 welfare schemes in the local database.
2. **The 1:1 Official Form Overlay Engine**: Places typed citizen text onto authentic scanned government PDF forms at exact millimeter coordinates.

---

## 4. SYSTEM ARCHITECTURE

```
+-------------------------------------------------------------+
|                     Citizen User Interface                  |
|                 (Streamlit Web Application)                 |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 Profile Extraction Engine                   |
|               (src/engine/profile_extractor.py)              |
|   - Extracts: Full Name, Age, Domicile, Income, Ration ID   |
+------------------------------+------------------------------+
                               |
               +---------------+---------------+
               |                               |
               v                               v
+-----------------------------+ +-----------------------------+
|  Universal Form Generator   | |   1:1 Proforma Overlay      |
| (src/engine/pdf_generator)  | | (src/engine/template_overlay) |
| - ReportLab Canvas          | | - pypdf Clone/Merge Stream  |
| - 145+ Schemes Covered      | | - Authentic Scanned PDFs    |
| - Standard Single Window    | | - Exact Physical Alignment  |
+--------------+--------------+ +--------------+--------------+
               |                               |
               +---------------+---------------+
                               |
                               v
+-------------------------------------------------------------+
|                Verified Application PDF File                |
|                    (Local A4 File Output)                   |
+-------------------------------------------------------------+
```

---

## 5. TECHNICAL DESCRIPTION OF MODULES

### 5.1 Profile Extraction Module (`src/engine/profile_extractor.py`)
- The module monitors conversation messages between the citizen and the system.
- It parses input text with regular expressions.
- It extracts citizen attributes:
  - Applicant full name
  - Age and gender
  - State and district of residence
  - Monthly and annual family income
  - BPL (Below Poverty Line) status
  - Student and employment status
- The module stores attributes in a strict data schema (`src/schema/rules.py:UserProfile`).

### 5.2 Universal Multi-Domain Form Engine (`src/engine/form_autofill.py` & `src/engine/pdf_generator.py`)
- The module detects the domain of the selected welfare scheme:
  - Health & Medical Grants
  - Education & Scholarships
  - Maternal & Child Welfare
  - Construction & Labour Assistance
  - Social Security & Pensions
- The module queries the local SQLite database (`data/schemes.db`) to obtain mandatory document checklists.
- The module generates an A4 PDF document with:
  - Official department title and reference number
  - Auto-filled particulars table
  - Legal declaration of the applicant
  - Official attestation block for the designated authority
  - Verbatim list of required documents

### 5.3 1:1 Pixel-Perfect Official Form Overlay Engine (`src/engine/template_overlay.py`)
- The module uses authentic scanned government application forms as background templates:
  - **Rashtriya Arogya Nidhi (RAN) & HMDG**: 4-page official Ministry of Health proforma.
  - **Delhi Arogya Nidhi (DAN) / DAK**: 3-page official Government of NCT of Delhi proforma.
- The module creates a transparent graphic layer with ReportLab.
- The module places typed text in blue ink (`#002B7F`) at calibrated physical positions:
  - Row 1 (Patient Name and Age): $x = 235\text{ pt}, y = 748\text{ pt}$
  - Row 2 (Father or Husband Name): $x = 235\text{ pt}, y = 726\text{ pt}$
  - Row 3 (Residential Address and Domicile): $x = 325\text{ pt}, y = 703\text{ pt}$
  - Row 4 (Disease Name and Care Urgency): $x = 325\text{ pt}, y = 628\text{ pt}$
  - Row 5 (Treating Hospital): $x = 325\text{ pt}, y = 591\text{ pt}$
  - Row 6 (Requested Financial Assistance): $x = 325\text{ pt}, y = 553\text{ pt}$
  - Row 7 (SDM Income Certificate Details): $x = 325\text{ pt}, y = 475\text{ pt}$
  - Rows 9 & 10 (Prior Financial Assistance): $x = 325\text{ pt}$
- The module uses `pypdf.PdfWriter(clone_from=...)` to merge text layers into the template.
- The output maintains all official graphics, serial marks, and government emblems.

---

## 6. VERIFICATION AND QUALITY ASSURANCE
- The test suite executes with `pytest`.
- The suite contains 27 unit and integration tests (`tests/test_form_autofill.py`):
  - Test 1: Health domain mapping and ReportLab table rendering.
  - Test 2: Education domain mapping with roll number and school verification.
  - Test 3: Maternal nutrition mapping with Anganwadi center verification.
  - Test 4: Construction labour mapping with BOCW passbook verification.
  - Test 5: 1:1 physical coordinate overlay on authentic scanned templates.
- All 27 tests pass with zero errors.

---

## 7. USER INSTRUCTIONS

### 7.1 Generate an Application Form
1. Open your web browser at `http://localhost:8501`.
2. Enter your citizen details in the chat window. For example:
   > *"I am Sunita Rawat, 38 years old living in East Delhi. I have heart disease requiring treatment at LNJP Hospital. My family monthly income is 5000 with a BPL card. What schemes can assist me?"*
3. Read the verified scheme recommendations from the assistant.
4. Expand the **Auto-Fill Official Application Form & Download PDF** section.
5. Select your target scheme from the dropdown list.
6. Select your preferred form format:
   - **1:1 Authentic Official Paper Proforma**: Available for schemes with scanned templates.
   - **Universal Standardized Digital Proforma**: Available for all 145+ schemes.
7. Click the **Download Filled Official Form** button.
8. Save and print the completed PDF document.
