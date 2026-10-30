# Slice 1 Ingestion Report: Uttarakhand Pilot

**Date**: 2026-10-30  
**Target Jurisdiction**: Uttarakhand  
**Target Schemes**: 16  
**Successful Ingestions**: 16 (100%)  
**Failures**: 0  
**Storage**: SQLite (`data/schemes.db`) & Raw JSON Snapshots (`data/raw_snapshots/*.json`)

---

## 1. Compliance & Rate Limiting Audit
- **Site Terms & Robots.txt**:
  - Inspected `https://www.myscheme.gov.in/robots.txt`.
  - Crawler access is permitted (`Allow: /`, only `/404` disallowed).
  - Identified clean public client endpoint (`https://api.myscheme.gov.in/schemes/v6/public/schemes?slug={slug}&lang=en`) utilizing official API key embedded in public static assets.
  - Ethical rate-limiting: 1.0 second delay between requests, backoff on HTTP 429, zero heavy DOM headless rendering needed.

---

## 2. Ingested Schemes Breakdown
Every scheme record preserves the exact verbatim source text and cryptographic SHA-256 content hash:

| Scheme ID | Scheme Name | Eligibility Criteria (Verbatim Preview) | Snapshots Stored |
| :--- | :--- | :--- | :--- |
| `kbyuk` | Kishori Balika Yojana- Uttarakhand | Resident of Uttarakhand; Adolescent girl (14-18 yrs); Residing in Haridwar or Udham Singh Nagar. | `data/raw_snapshots/kbyuk_20261030.json` |
| `ahwc` | AYUSH Health and Wellness Centre | All Indian citizens seeking preventive, promotive, curative healthcare through AYUSH systems. | `data/raw_snapshots/ahwc_20261030.json` |
| `snduk` | Sanitary Napkin Distribution - Uttarakhand | Resident of Uttarakhand; Adolescent girls aged 10 to 19 years. | `data/raw_snapshots/snduk_20261030.json` |
| `ipuk` | Immunization Programme - Uttarakhand | Pregnant women and children from birth up to 16 years of age in Uttarakhand. | `data/raw_snapshots/ipuk_20261030.json` |
| `108easuk` | 108 Emergency Ambulance Service - Uttarakhand | Any person residing or visiting Uttarakhand experiencing medical emergencies. | `data/raw_snapshots/108easuk_20261030.json` |
| `snsu` | Sanitary Napkin Scheme | Adolescent girls aged 10 to 19 years in rural areas of Uttarakhand. | `data/raw_snapshots/snsu_20261030.json` |
| `kkssuk` | Khushiyon Ki Sawari Sewa - Uttarakhand | Post-delivery mothers and sick neonates discharged from public health facilities. | `data/raw_snapshots/kkssuk_20261030.json` |
| `nsjy` | Nishulk Swasthya Jaanch Yojana - Uttarakhand | All permanent residents of Uttarakhand visiting government medical facilities. | `data/raw_snapshots/nsjy_20261030.json` |
| `maternalnutritionuk` | Mukhyamantri Sampoorna Pushti Yojana: Maternal Nutrition | Pregnant women & lactating mothers; Domicile of Uttarakhand; Registered with Anganwadi. | `data/raw_snapshots/maternalnutritionuk_20261030.json` |
| `ywcuk` | Yoga Wellness Center | All individuals seeking holistic health, stress relief, and yoga lifestyle management. | `data/raw_snapshots/ywcuk_20261030.json` |
| `kspc` | Kishor Swasthya Paramarsh Clinic - Uttarakhand | Adolescents aged 10 to 19 years facing physical, psychological, or nutritional issues. | `data/raw_snapshots/kspc_20261030.json` |
| `huk` | Hemoglobinopathy - Uttarakhand | Patients diagnosed with Thalassemia, Sickle Cell Anemia, or Hemophilia in Uttarakhand. | `data/raw_snapshots/huk_20261030.json` |
| `mcuf` | Medical Check-Up facility (UKBOCWWB) | Registered building/construction workers registered with UKBOCWWB. | `data/raw_snapshots/mcuf_20261030.json` |
| `sghs` | State Government Health Scheme (Golden Card) | Serving/retired state government employees & pensioners of Uttarakhand. | `data/raw_snapshots/sghs_20261030.json` |
| `snsukbocwwb` | Sanitary Napkin Scheme (UKBOCWWB) | Female registered construction workers or wives/daughters of registered construction workers. | `data/raw_snapshots/snsukbocwwb_20261030.json` |
| `ahlfscty` | Healthy Lifestyle for School Children through Ayurvidya | Students studying in government and aided schools in Uttarakhand. | `data/raw_snapshots/ahlfscty_20261030.json` |

---

## 3. Provenance & Reproducibility
- All rows in `schemes.db` reference the immutable raw snapshot path and recording timestamp.
- Verified with automated test suite `tests/test_slice1_ingestion.py`.

