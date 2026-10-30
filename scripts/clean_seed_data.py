"""
clean_seed_data.py - Data cleaning and merging script for Scheme Finder (Slice 0).

Reads 'Docs/Final data 1.xlsx', parses Sheet1 (aligning misaligned columns)
and Sheet2 (parsing offset 2-column layout), normalizes jurisdictions and levels
(Central, State, UT), deduplicates by scheme slug, and writes 'data/clean/schemes_seed.csv'.
"""

import re
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple
import openpyxl

UT_SET = {
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra & Nagar Haveli and Daman & Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
}

def classify_level(state_or_ministry: str) -> str:
    """Classify jurisdiction into Central, State, or UT."""
    if not state_or_ministry:
        return "Unknown"
    norm = state_or_ministry.strip()
    if norm.lower().startswith("ministry") or "minitry" in norm.lower():
        return "Central"
    if norm in UT_SET:
        return "UT"
    return "State"

def extract_slug(url: str) -> str:
    """Extract slug from myscheme URL (e.g., https://www.myscheme.gov.in/schemes/kbyuk -> kbyuk)."""
    if not url:
        return ""
    clean_url = url.strip().rstrip("/")
    return clean_url.split("/")[-1]

def parse_sheet1(wb: openpyxl.Workbook) -> List[Dict[str, Any]]:
    sheet = wb["Sheet1"]
    schemes = []
    
    # Rows 2 to 130 are actual data rows
    for r in range(2, 131):
        sr_no = sheet.cell(r, 1).value
        url = sheet.cell(r, 2).value
        state_or_ministry = sheet.cell(r, 4).value
        title = sheet.cell(r, 5).value
        desc = sheet.cell(r, 6).value
        
        tags = []
        for c in range(7, 12):
            tag_val = sheet.cell(r, c).value
            if tag_val and str(tag_val).strip():
                tags.append(str(tag_val).strip())
                
        if not url:
            continue
            
        url_str = str(url).strip()
        slug = extract_slug(url_str)
        state_min_str = str(state_or_ministry).strip() if state_or_ministry else ""
        title_str = str(title).strip() if title else slug
        desc_str = str(desc).strip() if desc else ""
        
        schemes.append({
            "scheme_id": slug,
            "name": title_str,
            "level": classify_level(state_min_str),
            "state_or_ministry": state_min_str,
            "short_description": desc_str,
            "tags": ";".join(tags),
            "url": url_str,
            "source_sheet": "Sheet1",
        })
        
    return schemes

def parse_sheet2(wb: openpyxl.Workbook) -> List[Dict[str, Any]]:
    sheet = wb["Sheet2"]
    schemes = []
    
    # In Sheet2, scheme items are in columns (1, 2) and (9, 10)
    for r in range(1, sheet.max_row + 1):
        for c_name, c_url in [(1, 2), (9, 10)]:
            name_val = sheet.cell(r, c_name).value
            url_val = sheet.cell(r, c_url).value
            
            if not url_val and not name_val:
                continue
                
            name_str = str(name_val).strip() if name_val else ""
            url_str = str(url_val).strip() if url_val else ""
            slug = extract_slug(url_str)
            
            # Infer state/ministry from name if indicated (e.g. "Tamil Nadu", "Madhya Pradesh")
            state_min_str = ""
            if "Tamil Nadu" in name_str:
                state_min_str = "Tamil Nadu"
            elif "Madhya Pradesh" in name_str:
                state_min_str = "Madhya Pradesh"
            elif "DNH&DD" in name_str:
                state_min_str = "Dadra & Nagar Haveli and Daman & Diu"
            elif any(k in name_str for k in ["National", "Atal Mission", "Ayurswasthya", "NAMASTE", "Fund of Funds", "Indian Community"]):
                state_min_str = "Central"
            
            level = classify_level(state_min_str) if state_min_str else "Unknown"
            
            schemes.append({
                "scheme_id": slug,
                "name": name_str,
                "level": level,
                "state_or_ministry": state_min_str,
                "short_description": "",
                "tags": "",
                "url": url_str,
                "source_sheet": "Sheet2",
            })
            
    return schemes

def clean_and_merge(input_path: str, output_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    wb = openpyxl.load_workbook(input_path, data_only=True)
    
    s1_schemes = parse_sheet1(wb)
    s2_schemes = parse_sheet2(wb)
    
    seen_slugs = set()
    merged = []
    duplicates = []
    
    for item in s1_schemes:
        slug = item["scheme_id"]
        if slug in seen_slugs:
            duplicates.append(slug)
        else:
            seen_slugs.add(slug)
            merged.append(item)
            
    for item in s2_schemes:
        slug = item["scheme_id"]
        if slug in seen_slugs:
            duplicates.append(slug)
        else:
            seen_slugs.add(slug)
            merged.append(item)
            
    # Write to CSV
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "scheme_id",
        "name",
        "level",
        "state_or_ministry",
        "short_description",
        "tags",
        "url",
        "source_sheet"
    ]
    
    with open(out_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)
        
    stats = {
        "sheet1_count": len(s1_schemes),
        "sheet2_count": len(s2_schemes),
        "merged_count": len(merged),
        "duplicates": duplicates,
    }
    return merged, stats

if __name__ == "__main__":
    excel_file = "Docs/Final data 1.xlsx"
    out_csv = "data/clean/schemes_seed.csv"
    records, stats = clean_and_merge(excel_file, out_csv)
    print(f"Successfully processed {excel_file} -> {out_csv}")
    print(f"Stats: Sheet1={stats['sheet1_count']}, Sheet2={stats['sheet2_count']}, Merged={stats['merged_count']}, Duplicates={stats['duplicates']}")

