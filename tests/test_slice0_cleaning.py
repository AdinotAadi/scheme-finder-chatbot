"""
tests/test_slice0_cleaning.py - Unit tests for Slice 0 data cleaning and normalization.
"""

import csv
from pathlib import Path
import pytest
from scripts.clean_seed_data import clean_and_merge, classify_level, extract_slug

def test_extract_slug():
    assert extract_slug("https://www.myscheme.gov.in/schemes/kbyuk") == "kbyuk"
    assert extract_slug("https://www.myscheme.gov.in/schemes/rcmrf-mh/") == "rcmrf-mh"
    assert extract_slug("") == ""

def test_classify_level():
    assert classify_level("Ministry Of Health & Family Welfare") == "Central"
    assert classify_level("Minitry of Jal Shakti") == "Central"
    assert classify_level("Uttarakhand") == "State"
    assert classify_level("Delhi") == "UT"
    assert classify_level("Puducherry") == "UT"
    assert classify_level("Chandigarh") == "UT"
    assert classify_level("") == "Unknown"

def test_seed_cleaning_output():
    excel_file = "Docs/Final data 1.xlsx"
    out_csv = "data/clean/schemes_seed.csv"
    
    assert Path(excel_file).exists(), "Input Excel file must exist"
    
    records, stats = clean_and_merge(excel_file, out_csv)
    
    assert Path(out_csv).exists()
    assert stats["sheet1_count"] == 129
    assert stats["sheet2_count"] == 16
    assert stats["merged_count"] == 145
    assert len(stats["duplicates"]) == 0
    
    # Check CSV content
    with open(out_csv, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 145
        for row in reader:
            assert row["scheme_id"] != ""
            assert row["url"].startswith("https://www.myscheme.gov.in/schemes/")
            assert row["source_sheet"] in ["Sheet1", "Sheet2"]
            assert row["level"] in ["Central", "State", "UT", "Unknown"]
            
    # Verify Uttarakhand schemes present
    uk_schemes = [r for r in records if r["state_or_ministry"] == "Uttarakhand"]
    assert len(uk_schemes) == 16

