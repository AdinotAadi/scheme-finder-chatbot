"""
cli.py - Interactive CLI interface for trustworthy scheme eligibility assessment (Slice 5).

Hard Rules Enforced:
1. Collects: age, annual income, gender, profession/occupation, marital status & number of children (asked only for women), and state.
2. Evaluates eligibility deterministically using three-valued logic.
3. Every match explicitly states:
   - "May be eligible" (NEVER promises benefits).
   - Why it may fit (satisfied conditions).
   - What remains unknown (missing conditions).
   - Official source link.
   - Required documents (or advice on where to check if none listed).
"""

import sys
import sqlite3
from typing import Optional, Dict, Any, List
from src.schema.rules import UserProfile
from src.engine.evaluator import evaluate_scheme, OverallSchemeCategory
from data.gold_standard.gold_rules_uttarakhand import get_gold_rules_uttarakhand

def prompt_optional(prompt_text: str) -> Optional[str]:
    """Helper to collect optional input; blank input evaluates to None (unknown)."""
    val = input(prompt_text).strip()
    return val if val else None

def collect_user_profile() -> UserProfile:
    """Interactively collects user profile attributes with clear optional defaults."""
    print("\n" + "=" * 65)
    print("📋 Scheme Eligibility Assessment - User Questionnaire")
    print("   (Press Enter without typing if an answer is unknown or not shared)")
    print("=" * 65)

    # 1. State of residence
    state = prompt_optional("\n1. State of residence (e.g., Uttarakhand, Rajasthan): ")
    
    # 2. District (optional)
    district = None
    if state and state.lower() == "uttarakhand":
        district = prompt_optional("   District in Uttarakhand (e.g., Haridwar, Dehradun): ")

    # 3. Gender
    print("\n2. Gender:")
    print("   [1] Female")
    print("   [2] Male")
    print("   [3] Other / Prefer not to say")
    gender_choice = prompt_optional("   Select (1/2/3): ")
    gender = None
    if gender_choice == "1":
        gender = "female"
    elif gender_choice == "2":
        gender = "male"
    elif gender_choice == "3":
        gender = "other"

    # 4. Age
    age_str = prompt_optional("\n3. Age in years: ")
    age = None
    if age_str:
        try:
            age = int(age_str)
        except ValueError:
            print("   ⚠️ Invalid age format; recorded as unknown.")

    # 5. Annual family income (INR)
    income_str = prompt_optional("\n4. Annual family income in INR (e.g., 150000): ")
    income = None
    if income_str:
        try:
            income = float(income_str)
        except ValueError:
            print("   ⚠️ Invalid income format; recorded as unknown.")

    # 6. Profession / Occupation
    print("\n5. Profession / Occupation Category:")
    print("   [1] Construction worker (BOCW registered or daily wage labour)")
    print("   [2] Government employee / Pensioner")
    print("   [3] Student")
    print("   [4] Self-employed / Unorganized worker / Homemaker / Other")
    occ_choice = prompt_optional("   Select (1/2/3/4): ")
    occ_category = None
    registered_worker = None
    is_student = None
    if occ_choice == "1":
        occ_category = "construction_worker"
        reg_str = prompt_optional("   Are you registered with the Building & Construction Workers Board (y/n)? ")
        if reg_str:
            registered_worker = reg_str.lower().startswith("y")
    elif occ_choice == "2":
        occ_category = "govt_employee"
    elif occ_choice == "3":
        is_student = True
        occ_category = "student"
    elif occ_choice == "4":
        occ_category = "unorganized"

    # 7. Marital status and children (Asked ONLY if gender is female)
    marital_status = None
    num_children = None
    is_pregnant = None
    is_lactating = None
    
    if gender == "female":
        print("\n6. Marital Status (Women-specific questionnaire):")
        print("   [1] Unmarried / Single")
        print("   [2] Married")
        print("   [3] Widowed")
        print("   [4] Divorced / Deserted")
        mar_choice = prompt_optional("   Select (1/2/3/4): ")
        if mar_choice == "1":
            marital_status = "unmarried"
        elif mar_choice == "2":
            marital_status = "married"
        elif mar_choice == "3":
            marital_status = "widowed"
        elif mar_choice == "4":
            marital_status = "divorced"

        children_str = prompt_optional("   Number of children: ")
        if children_str:
            try:
                num_children = int(children_str)
            except ValueError:
                pass

        preg_str = prompt_optional("   Are you currently pregnant (y/n)? ")
        if preg_str:
            is_pregnant = preg_str.lower().startswith("y")

        lact_str = prompt_optional("   Are you currently a lactating/nursing mother (y/n)? ")
        if lact_str:
            is_lactating = lact_str.lower().startswith("y")

    return UserProfile(
        age=age,
        annual_income_inr=income,
        gender=gender,
        marital_status=marital_status,
        number_of_children=num_children,
        state_residence=state,
        district_residence=district,
        is_pregnant=is_pregnant,
        is_lactating=is_lactating,
        is_student=is_student,
        occupation_category=occ_category,
        registered_worker=registered_worker
    )

def fetch_scheme_metadata(db_path: str = "data/schemes.db") -> Dict[str, Dict[str, str]]:
    """Loads scheme title, official link, and required documents from SQLite."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT scheme_id, name, source_url, documents_required_verbatim FROM schemes")
    meta = {}
    for sid, name, url, docs in cur.fetchall():
        meta[sid] = {
            "name": name,
            "url": url,
            "documents": docs.strip() if docs else "Consult official portal for document specifications."
        }
    conn.close()
    return meta

def run_cli():
    """Main CLI execution loop."""
    print("\n" + "#" * 65)
    print("  WELCOME TO SCHEME FINDER (PhD Research Prototype)")
    print("  Trustworthy Government Scheme Eligibility Assessment")
    print("#" * 65)
    print("⚠️  IMPORTANT NOTICE:")
    print("   This tool assesses whether you MAY BE ELIGIBLE based on official rules.")
    print("   It NEVER promises or guarantees a benefit. All applications must be")
    print("   submitted through the official government portal.")

    profile = collect_user_profile()
    scheme_meta = fetch_scheme_metadata()
    gold_rules = get_gold_rules_uttarakhand()

    matches = []
    need_info = []

    for sid, rule in gold_rules.items():
        report = evaluate_scheme(rule, profile)
        if report.category == OverallSchemeCategory.POTENTIAL_MATCH:
            matches.append((report, scheme_meta.get(sid, {})))
        elif report.category == OverallSchemeCategory.MORE_INFORMATION_NEEDED:
            need_info.append((report, scheme_meta.get(sid, {})))

    print("\n" + "=" * 65)
    print("🎯 ELIGIBILITY ASSESSMENT RESULTS")
    print("=" * 65)

    if matches:
        print(f"\n✅ SCHEMES YOU MAY BE ELIGIBLE FOR ({len(matches)} potential match{'es' if len(matches) > 1 else ''}):\n")
        for idx, (rep, meta) in enumerate(matches, 1):
            name = meta.get("name", rep.scheme_id)
            url = meta.get("url", "https://www.myscheme.gov.in")
            docs = meta.get("documents", "")

            print(f"[{idx}] {name}")
            print(f"    • Status: MAY BE ELIGIBLE")
            print(f"    • Official Source: {url}")
            print("    • Why you may fit:")
            for sat in rep.satisfied_criteria:
                print(f"      ✓ {sat}")
            print("    • Documents Needed:")
            for doc_line in docs.split("\n"):
                if doc_line.strip():
                    print(f"      {doc_line.strip()}")
            print("-" * 65)
    else:
        print("\nℹ️  No immediate verified matches found based on the provided profile.")

    if need_info:
        print(f"\n🔍 SCHEMES WHERE MORE INFORMATION IS NEEDED ({len(need_info)} scheme{'s' if len(need_info) > 1 else ''}):\n")
        for idx, (rep, meta) in enumerate(need_info[:5], 1): # Top 5 to keep concise
            name = meta.get("name", rep.scheme_id)
            url = meta.get("url", "https://www.myscheme.gov.in")
            print(f"[{idx}] {name}")
            print(f"    • Official Source: {url}")
            print("    • What is unknown / to verify:")
            for mis in rep.missing_criteria:
                print(f"      ❓ {mis}")
            print("-" * 65)

    print("\n✨ Thank you for using Scheme Finder research prototype.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_cli()

