# Slice 0 Data-Quality & Audit Report

**Date**: 2026-10-30  
**Artifact Path**: `data/clean/schemes_seed.csv`  
**Input Source**: `Docs/Final data 1.xlsx` (Sheet1 & Sheet2)

---

## 1. Executive Summary

This report documents the audit and normalization of the raw scraped scheme dataset for the PhD research prototype on trustworthy eligibility assessment.
- **Raw Rows Processed**: 293 in Sheet1 (129 data rows, 162 empty rows) + 10 in Sheet2 (16 offset records).
- **Cleaned Dataset Count**: **145 unique schemes** after merging Sheet1 and Sheet2.
- **Duplicates**: **0 duplicate slugs** detected across sheets.
- **Key Finding**: In Sheet1, all detailed fields (`Eligibility_Criteria`, `Benefits`, `Application_Process`, `Documents_Required`) were **100% empty (0/129)** due to web scraper extraction failure. The actual eligibility rules and requirements must be retrieved directly from the live myScheme portal (`https://www.myscheme.gov.in/schemes/<slug>`) in Slice 1.

---

## 2. Structural Audit of Raw Excel

### Sheet1 Analysis
- **Row breakdown**:
  - Row 1: Header names.
  - Rows 2–130: 129 scheme entries.
  - Rows 131–293: Blank trailing rows with empty cells.
- **Column misalignment mapping**:
  - `data` (Col 4): Actual Jurisdiction (State name or Central Ministry name).
  - `data2` (Col 5): Scheme Title.
  - `data3` (Col 6): Short Summary / Description.
  - `data4` to `data8` (Cols 7–11): Category Tags (e.g. *Hospital, Non BPL, Relief Fund*).
  - Columns 12–44: Reserved for scraped content but entirely unpopulated for all rows.

### Sheet2 Analysis
- Layout: Asymmetric, non-standard tabular format.
  - Cols 1–2: Pairs of `[Scheme Name, Scheme URL]` (10 rows).
  - Cols 9–10: Pairs of `[Scheme Name, Scheme URL]` (6 rows).
- Total records found: 16 unique schemes.
- All 16 URLs represent schemes not present in Sheet1 (0% overlap).

---

## 3. Jurisdiction & Pilot State Counts

### Breakdown by Governance Level
- **State Schemes**: 108 schemes (74.5%)
- **Central Ministry Schemes**: 18 schemes (12.4%)
- **Union Territory Schemes**: 17 schemes (11.7%)
- **Unclassified / Incomplete**: 2 schemes (1.4% from Sheet2)

### Top Jurisdictions in Dataset
| Jurisdiction | Scheme Count | Level | Key Beneficiary Focus |
| :--- | :--- | :--- | :--- |
| **Uttarakhand** | **16** | State | Adolescent girls, maternal nutrition, sanitary napkins, workers |
| **Chhattisgarh** | **12** | State | Unorganized women workers, maternity relief, accident aid |
| **Puducherry** | **10** | UT | Healthcare aid, specialized treatment |
| **Gujarat** | **10** | State | Health insurance, child & maternal welfare |
| **Assam** | 7 | State | Medical assistance, general welfare |
| **West Bengal** | 5 | State | Healthcare relief |
| **Madhya Pradesh** | 5 | State | Adolescent health, women schemes |
| **Odisha** | 5 | State | Medical care |
| **Central Ministries** | 18 | Central | Health & Family Welfare, Social Justice, Women & Child Dev |

---

## 4. Recommendation for Pilot State: **Uttarakhand**

We recommend **Uttarakhand** (16 schemes) as the initial pilot benchmark:
1. **Critical Mass**: Largest single-state representation in the seed dataset (16 distinct schemes).
2. **Relevance to Chatbot Audience**: Direct coverage of women, maternal health, and young girls (*Kishori Balika Yojana*, *Mukhyamantri Sampoorna Pushti Yojana*, *Sanitary Napkin Schemes*).
3. **Diverse Eligibility Constraints**: Criteria involve age intervals (e.g., 11–18 for Kishori Balika), student status, pregnancy/maternal status, BPL/income, and construction worker registration (UKBOCWWB).

---

## 5. Verification & Test Evidence
- **Automated Tests**: `tests/test_slice0_cleaning.py` passes all assertions (100% test coverage for slug extraction, level classification, and schema integrity).
- **Target CSV**: Produced at `data/clean/schemes_seed.csv` with standard columns: `scheme_id`, `name`, `level`, `state_or_ministry`, `short_description`, `tags`, `url`, `source_sheet`.

