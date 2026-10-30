"""
review_queue.py - Review queue exporter and importer for human-in-the-loop rule verification (Slice 2).
"""

import csv
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.schema.rules import SchemeEligibilityRule, SingleCriterion, CriterionGroup, ReviewStatus, AttributeName, Operator, LogicalGroupOperator

REVIEW_DIR = Path("data/review")

def init_review_db(db_path: str = "data/schemes.db"):
    """Creates table for structured criteria and review tracking."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scheme_rules (
        criterion_id TEXT PRIMARY KEY,
        scheme_id TEXT NOT NULL,
        attribute TEXT NOT NULL,
        operator TEXT NOT NULL,
        target_value TEXT NOT NULL,
        verbatim_source_sentence TEXT NOT NULL,
        is_mandatory INTEGER NOT NULL,
        review_status TEXT NOT NULL,
        reviewer_note TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (scheme_id) REFERENCES schemes(scheme_id)
    )
    """)
    conn.commit()
    conn.close()

def export_review_csv(rules: List[SchemeEligibilityRule], output_file: str):
    """Exports proposed rules to CSV for offline human review."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for scheme_rule in rules:
        scheme_id = scheme_rule.scheme_id
        
        def traverse(group: CriterionGroup):
            for item in group.criteria:
                if isinstance(item, SingleCriterion):
                    rows.append({
                        "scheme_id": scheme_id,
                        "criterion_id": item.criterion_id,
                        "attribute": item.attribute.value,
                        "operator": item.operator.value,
                        "target_value": json.dumps(item.target_value),
                        "is_mandatory": "TRUE" if item.is_mandatory else "FALSE",
                        "verbatim_source_sentence": item.verbatim_source_sentence,
                        "review_status": item.review_status.value,
                        "reviewer_note": item.reviewer_note or "",
                        "human_override_json": ""  # Reserved for human edits
                    })
                elif isinstance(item, CriterionGroup):
                    traverse(item)
                    
        traverse(scheme_rule.rule_group)
        
    fieldnames = [
        "scheme_id",
        "criterion_id",
        "attribute",
        "operator",
        "target_value",
        "is_mandatory",
        "verbatim_source_sentence",
        "review_status",
        "reviewer_note",
        "human_override_json"
    ]
    
    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    return len(rows)

def import_review_csv(csv_path: str, db_path: str = "data/schemes.db") -> int:
    """Imports human-reviewed rules into SQLite store."""
    init_review_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["criterion_id"]
            sid = row["scheme_id"]
            status = row["review_status"].strip().lower()
            note = row.get("reviewer_note", "").strip()
            
            # Check if there is a human override
            override_raw = row.get("human_override_json", "").strip()
            if override_raw:
                try:
                    override_data = json.loads(override_raw)
                    attr = override_data.get("attribute", row["attribute"])
                    op = override_data.get("operator", row["operator"])
                    val = json.dumps(override_data.get("target_value", json.loads(row["target_value"])))
                    is_mand = 1 if override_data.get("is_mandatory", row["is_mandatory"].upper() == "TRUE") else 0
                except Exception:
                    attr = row["attribute"]
                    op = row["operator"]
                    val = row["target_value"]
                    is_mand = 1 if row["is_mandatory"].upper() == "TRUE" else 0
            else:
                attr = row["attribute"]
                op = row["operator"]
                val = row["target_value"]
                is_mand = 1 if row["is_mandatory"].upper() == "TRUE" else 0
                
            cur.execute("""
            INSERT OR REPLACE INTO scheme_rules (
                criterion_id, scheme_id, attribute, operator, target_value,
                verbatim_source_sentence, is_mandatory, review_status, reviewer_note,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                cid, sid, attr, op, val,
                row["verbatim_source_sentence"], is_mand, status, note
            ))
            count += 1
            
    conn.commit()
    conn.close()
    return count

