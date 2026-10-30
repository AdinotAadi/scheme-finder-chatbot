"""
fetch_schemes.py - Ingestion script with provenance and rate-limiting (Slice 1).

Fetches official scheme metadata and verbatim text from myScheme via the public API
with exponential backoff, rate limiting (polite scraping), raw JSON snapshot storage,
and structured SQLite persistence.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import httpx
import csv

DB_PATH = "data/schemes.db"
SNAPSHOT_DIR = Path("data/raw_snapshots")
API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
API_BASE = "https://api.myscheme.gov.in/schemes/v6/public/schemes"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) SchemeFinderResearch/1.0",
    "Origin": "https://www.myscheme.gov.in",
    "Referer": "https://www.myscheme.gov.in/",
    "x-api-key": API_KEY,
    "Accept": "application/json, text/plain, */*"
}

def init_db(db_path: str = DB_PATH):
    """Initializes SQLite database with provenance and scheme tables."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        scheme_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        level TEXT,
        state TEXT,
        ministry TEXT,
        nodal_department TEXT,
        short_description TEXT,
        detailed_description TEXT,
        benefits_verbatim TEXT,
        eligibility_verbatim TEXT NOT NULL,
        application_process_verbatim TEXT,
        documents_required_verbatim TEXT,
        source_url TEXT NOT NULL,
        fetch_timestamp TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        raw_snapshot_path TEXT NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scheme_id TEXT NOT NULL,
        source_url TEXT NOT NULL,
        status TEXT NOT NULL,
        http_status INTEGER,
        error_message TEXT,
        timestamp TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

def extract_documents_text(docs_json: Optional[Dict[str, Any]]) -> str:
    """Extract clean string list from documents required structure."""
    if not docs_json:
        return ""
    en_docs = docs_json.get("en", {}).get("documents_required", [])
    doc_lines = []
    for item in en_docs:
        if isinstance(item, dict):
            for child in item.get("children", []):
                if isinstance(child, dict):
                    texts = [c.get("text", "") for c in child.get("children", []) if isinstance(c, dict)]
                    line = "".join(texts).strip()
                    if line:
                        doc_lines.append(f"- {line}")
                elif isinstance(child, str) and child.strip():
                    doc_lines.append(f"- {child.strip()}")
        elif isinstance(item, str) and item.strip():
            doc_lines.append(f"- {item.strip()}")
    return "\n".join(doc_lines)

def fetch_single_scheme(slug: str, client: httpx.Client, delay: float = 1.0) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Fetch a single scheme with backoff, snapshot caching, and sub-document retrieval."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    fetch_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    snapshot_file = SNAPSHOT_DIR / f"{slug}_{fetch_date}.json"
    
    # Polite rate limiting
    time.sleep(delay)
    
    url = f"{API_BASE}?slug={slug}&lang=en"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = client.get(url, headers=DEFAULT_HEADERS, timeout=12.0)
            if resp.status_code == 200:
                body = resp.json()
                if body.get("status") == "Success" and "data" in body and body["data"]:
                    scheme_raw = body["data"]
                    
                    # Fetch documents required if internal _id exists
                    internal_id = scheme_raw.get("_id")
                    docs_text = ""
                    if internal_id:
                        time.sleep(0.3)
                        docs_url = f"{API_BASE}/{internal_id}/documents?lang=en"
                        try:
                            docs_resp = client.get(docs_url, headers=DEFAULT_HEADERS, timeout=8.0)
                            if docs_resp.status_code == 200:
                                docs_body = docs_resp.json()
                                docs_text = extract_documents_text(docs_body.get("data"))
                                scheme_raw["documents_details"] = docs_body.get("data")
                        except Exception:
                            pass
                    
                    # Save raw snapshot
                    with open(snapshot_file, "w", encoding="utf-8") as sf:
                        json.dump(scheme_raw, sf, indent=2, ensure_ascii=False)
                    
                    scheme_raw["_local_snapshot_path"] = str(snapshot_file)
                    scheme_raw["_extracted_docs_text"] = docs_text
                    return True, scheme_raw, None
                else:
                    err = f"API returned non-success body: {body.get('errorDescription') or body.get('error')}"
                    return False, None, err
            elif resp.status_code == 429:
                wait_time = (attempt + 1) * 3
                time.sleep(wait_time)
                continue
            else:
                return False, None, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            if attempt == max_retries - 1:
                return False, None, str(e)
            time.sleep(2)
            
    return False, None, "Max retries exceeded"

def _extract_text_or_md(val: Any) -> str:
    """Safely extracts text whether field is string, markdown, or nested rich-text AST list."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, (int, float, bool)):
        return str(val)
    if isinstance(val, list):
        out = []
        for item in val:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                children = item.get("children", [])
                for child in children:
                    if isinstance(child, dict):
                        if "text" in child:
                            out.append(child["text"])
                        elif "children" in child:
                            for sub in child["children"]:
                                if isinstance(sub, dict) and "text" in sub:
                                    out.append(sub["text"])
                    elif isinstance(child, str):
                        out.append(child)
        return "\n".join(out).strip()
    if isinstance(val, dict):
        return json.dumps(val, ensure_ascii=False)
    return str(val)

def parse_and_store_scheme(slug: str, raw_data: Dict[str, Any], original_url: str, db_path: str = DB_PATH):
    """Normalize extracted API structure and insert into SQLite with content hash."""
    en = raw_data.get("en", {})
    basic = en.get("basicDetails", {})
    content = en.get("schemeContent", {})
    eligibility_obj = en.get("eligibilityCriteria", {})
    app_proc_list = en.get("applicationProcess", [])
    
    name = basic.get("schemeName") or slug
    level = basic.get("level", {}).get("label") if isinstance(basic.get("level"), dict) else str(basic.get("level") or "")
    state = basic.get("state", {}).get("label") if isinstance(basic.get("state"), dict) else str(basic.get("state") or "")
    nodal_dept = basic.get("nodalDepartmentName", {}).get("label") if isinstance(basic.get("nodalDepartmentName"), dict) else str(basic.get("nodalDepartmentName") or "")
    
    # Description
    short_desc = _extract_text_or_md(content.get("briefDescription"))
    detailed_desc = _extract_text_or_md(content.get("detailedDescription_md") or content.get("detailedDescription"))
    
    # Verbatim fields
    benefits_verbatim = _extract_text_or_md(content.get("benefits_md") or content.get("benefits"))
    eligibility_verbatim = _extract_text_or_md(eligibility_obj.get("eligibilityDescription_md") or eligibility_obj.get("eligibilityDescription"))
    
    # Application process
    app_process_parts = []
    for proc in app_proc_list:
        if isinstance(proc, dict):
            p_md = proc.get("process_md") or _extract_text_or_md(proc.get("process"))
            if p_md:
                app_process_parts.append(str(p_md).strip())
    app_process_verbatim = "\n\n".join(app_process_parts)
    
    docs_required_verbatim = str(raw_data.get("_extracted_docs_text", ""))
    snapshot_path = str(raw_data.get("_local_snapshot_path", ""))
    fetch_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    combined_content = f"{name}{eligibility_verbatim}{benefits_verbatim}"
    content_hash = hashlib.sha256(combined_content.encode("utf-8")).hexdigest()
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO schemes (
        scheme_id, name, level, state, ministry, nodal_department,
        short_description, detailed_description, benefits_verbatim,
        eligibility_verbatim, application_process_verbatim, documents_required_verbatim,
        source_url, fetch_timestamp, content_hash, raw_snapshot_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        slug, name, level, state, "", nodal_dept,
        short_desc, detailed_desc, benefits_verbatim,
        eligibility_verbatim, app_process_verbatim, docs_required_verbatim,
        original_url, fetch_ts, content_hash, snapshot_path
    ))
    
    cur.execute("""
    INSERT INTO ingestion_logs (scheme_id, source_url, status, http_status, error_message, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (slug, original_url, "SUCCESS", 200, None, fetch_ts))
    
    conn.commit()
    conn.close()

def log_failure(slug: str, original_url: str, error_msg: str, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO ingestion_logs (scheme_id, source_url, status, http_status, error_message, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (slug, original_url, "FAILURE", None, error_msg, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def ingest_pilot_state(state_name: str = "Uttarakhand", seed_csv: str = "data/clean/schemes_seed.csv"):
    """Ingests schemes for a specific pilot jurisdiction."""
    init_db()
    with open(seed_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    target_schemes = [row for row in reader if row.get("state_or_ministry") == state_name]
    print(f"Starting ingestion for pilot jurisdiction: {state_name} ({len(target_schemes)} schemes)...")
    
    client = httpx.Client(timeout=15.0, follow_redirects=True)
    success_count = 0
    failure_count = 0
    
    for idx, row in enumerate(target_schemes, 1):
        slug = row["scheme_id"]
        url = row["url"]
        print(f"[{idx}/{len(target_schemes)}] Fetching {slug}...")
        ok, data, err = fetch_single_scheme(slug, client, delay=1.0)
        if ok and data:
            parse_and_store_scheme(slug, data, url)
            success_count += 1
            print(f"  ✓ {slug}: Saved snapshot & recorded verbatim text.")
        else:
            log_failure(slug, url, err or "Unknown failure")
            failure_count += 1
            print(f"  ✗ {slug} failed: {err}")
            
    client.close()
    print(f"\nIngestion Complete: {success_count} succeeded, {failure_count} failed.")

if __name__ == "__main__":
    pilot = sys.argv[1] if len(sys.argv) > 1 else "Uttarakhand"
    ingest_pilot_state(pilot)
