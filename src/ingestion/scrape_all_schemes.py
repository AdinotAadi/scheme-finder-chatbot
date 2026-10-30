"""
scrape_all_schemes.py - Ingests all 145 schemes across all states, saves raw HTML/JSON snapshots,
and records structured content in SQLite for vector store indexing.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import datetime
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import httpx

from src.ingestion.fetch_schemes import (
    DB_PATH, SNAPSHOT_DIR, API_KEY, API_BASE, DEFAULT_HEADERS,
    init_db, extract_documents_text, parse_and_store_scheme, log_failure
)

HTML_SNAPSHOT_DIR = Path("data/raw_html")

def fetch_scheme_html_and_json(slug: str, original_url: str, client: httpx.Client, delay: float = 0.5) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Fetches both raw HTML page and JSON structured payload, saving both snapshots."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    fetch_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    json_snapshot_file = SNAPSHOT_DIR / f"{slug}_{fetch_date}.json"
    html_snapshot_file = HTML_SNAPSHOT_DIR / f"{slug}_{fetch_date}.html"

    time.sleep(delay)
    
    # 1. Fetch raw HTML page
    try:
        html_resp = client.get(original_url, timeout=12.0)
        if html_resp.status_code == 200:
            with open(html_snapshot_file, "w", encoding="utf-8") as hf:
                hf.write(html_resp.text)
    except Exception as e:
        # Don't fail if HTML fetch fails but JSON succeeds
        pass

    # 2. Fetch structured JSON payload from public API
    api_url = f"{API_BASE}?slug={slug}&lang=en"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = client.get(api_url, headers=DEFAULT_HEADERS, timeout=12.0)
            if resp.status_code == 200:
                body = resp.json()
                if body.get("status") == "Success" and "data" in body and body["data"]:
                    scheme_raw = body["data"]
                    
                    # Fetch documents required if internal _id exists
                    internal_id = scheme_raw.get("_id")
                    docs_text = ""
                    if internal_id:
                        time.sleep(0.2)
                        docs_url = f"{API_BASE}/{internal_id}/documents?lang=en"
                        try:
                            docs_resp = client.get(docs_url, headers=DEFAULT_HEADERS, timeout=8.0)
                            if docs_resp.status_code == 200:
                                docs_body = docs_resp.json()
                                docs_text = extract_documents_text(docs_body.get("data"))
                                scheme_raw["documents_details"] = docs_body.get("data")
                        except Exception:
                            pass
                    
                    with open(json_snapshot_file, "w", encoding="utf-8") as sf:
                        json.dump(scheme_raw, sf, indent=2, ensure_ascii=False)
                    
                    scheme_raw["_local_snapshot_path"] = str(json_snapshot_file)
                    scheme_raw["_extracted_docs_text"] = docs_text
                    return True, scheme_raw, None
                else:
                    return False, None, f"API error: {body.get('errorDescription') or body.get('error')}"
            elif resp.status_code == 429:
                time.sleep((attempt + 1) * 2)
                continue
            else:
                return False, None, f"HTTP {resp.status_code}"
        except Exception as e:
            if attempt == max_retries - 1:
                return False, None, str(e)
            time.sleep(1)

    return False, None, "Max retries exceeded"

def scrape_all(seed_csv: str = "data/clean/schemes_seed.csv"):
    init_db()
    with open(seed_csv, "r", encoding="utf-8") as f:
        schemes = list(csv.DictReader(f))

    print(f"Starting batch scrape of all {len(schemes)} schemes across all jurisdictions...")
    client = httpx.Client(timeout=15.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    
    success = 0
    failed = 0
    
    for idx, row in enumerate(schemes, 1):
        slug = row["scheme_id"]
        url = row["url"]
        
        # Check if already present in sqlite
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT scheme_id FROM schemes WHERE scheme_id = ?", (slug,))
        exists = cur.fetchone()
        conn.close()
        
        if exists:
            success += 1
            continue

        print(f"[{idx}/{len(schemes)}] Fetching {slug}...")
        ok, data, err = fetch_scheme_html_and_json(slug, url, client, delay=0.4)
        if ok and data:
            parse_and_store_scheme(slug, data, url)
            success += 1
        else:
            log_failure(slug, url, err or "Failed")
            failed += 1
            print(f"  ✗ {slug} failed: {err}")

    client.close()
    print(f"\nBatch Scrape Complete: {success} succeeded, {failed} failed.")

if __name__ == "__main__":
    scrape_all()

