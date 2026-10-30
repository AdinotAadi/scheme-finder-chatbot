"""
tests/test_slice1_ingestion.py - Unit and regression tests for Slice 1 ingestion & persistence.
"""

import sqlite3
import hashlib
from pathlib import Path
import pytest
from src.ingestion.fetch_schemes import DB_PATH, extract_documents_text

def test_database_structure_and_records():
    assert Path(DB_PATH).exists(), "Database file must exist"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    assert "schemes" in tables
    assert "ingestion_logs" in tables
    
    # Check pilot scheme count (at least 16 Uttarakhand schemes)
    cur.execute("SELECT COUNT(*) FROM schemes WHERE state='Uttarakhand'")
    count = cur.fetchone()[0]
    assert count >= 16, f"Expected at least 16 Uttarakhand schemes in DB, found {count}"
    
    # Check non-empty verbatim eligibility
    cur.execute("SELECT scheme_id, name, eligibility_verbatim, raw_snapshot_path, content_hash FROM schemes")
    rows = cur.fetchall()
    for row in rows:
        slug, name, elig_text, snap_path, chash = row
        assert len(slug) > 0
        assert len(name) > 0
        assert len(elig_text.strip()) > 0, f"Eligibility verbatim must not be empty for {slug}"
        assert Path(snap_path).exists(), f"Raw snapshot file {snap_path} must exist"
        assert len(chash) == 64, "SHA-256 hash must be 64 hex chars"
        
    conn.close()

def test_documents_extractor():
    sample_docs_json = {
        "en": {
            "documents_required": [
                {
                    "type": "ol_list",
                    "children": [
                        {"type": "list_item", "children": [{"text": "Aadhaar Card"}]},
                        {"type": "list_item", "children": [{"text": "Birth Certificate"}]}
                    ]
                }
            ]
        }
    }
    extracted = extract_documents_text(sample_docs_json)
    assert "- Aadhaar Card" in extracted
    assert "- Birth Certificate" in extracted

