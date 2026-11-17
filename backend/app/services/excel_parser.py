"""
Dedicated Plant BOM Excel Parser.
Uses openpyxl to parse plant BOMs with merged cells, extract master metadata,
enforce canonical part_uid slugging for items lacking drawing numbers,
and automatically flag packaging materials as excluded from vision inspection.
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from backend.app.config import PACKAGING_KEYWORDS

def generate_part_uid_slug(item_name: str) -> str:
    """
    Generates a deterministic canonical slug for line items with missing or dash drawing numbers.
    e.g., 'M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S'
       -> 'NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S'
    """
    clean_name = re.sub(r'[^A-Za-z0-9]+', '_', item_name.strip()).strip('_').upper()
    return f"NO_DWG_{clean_name}"

def is_packaging_item(item_name: str) -> bool:
    """
    Checks if item name contains packaging keywords (Carton, Box, Master Bag, etc.).
    """
    name_upper = item_name.upper()
    return any(keyword in name_upper for keyword in PACKAGING_KEYWORDS)

def normalize_drawing_no(dwg: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    Checks if a drawing number is valid or an indicator of no drawing (—, -, NA, blank).
    Returns (normalized_dwg, is_valid).
    """
    if not dwg:
        return None, False
    dwg_clean = str(dwg).strip()
    invalid_tokens = ["—", "–", "-", "NA", "N/A", "NONE", "BLANK", "N.A.", "N.A", "."]
    if dwg_clean.upper() in invalid_tokens or not dwg_clean:
        return None, False
    return dwg_clean.upper(), True

def get_merged_cell_value(sheet: Worksheet, row: int, col: int) -> Any:
    """
    Returns the value of a cell, resolving merged ranges if necessary.
    """
    cell = sheet.cell(row=row, column=col)
    if cell.value is not None:
        return cell.value
    
    # Check if cell is within any merged cell range
    for merged_range in sheet.merged_cells.ranges:
        if cell.coordinate in merged_range:
            top_left_cell = sheet.cell(row=merged_range.min_row, column=merged_range.min_col)
            return top_left_cell.value
    return None

class PlantExcelBomParser:
    """
    Parser for Plant Manufacturing BOM spreadsheets.
    """

    @classmethod
    def parse_workbook(cls, file_path: Path) -> Dict[str, Any]:
        wb = openpyxl.load_workbook(str(file_path), data_only=True)
        # Select best sheet (prioritizing sheet with 'BOM' or 'KD' or first sheet)
        sheet_names = wb.sheetnames
        selected_sheet = wb.active
        for name in sheet_names:
            if "BOM" in name.upper() or "HRD" in name.upper() or "KD" in name.upper():
                selected_sheet = wb[name]
                break

        return cls.parse_sheet(selected_sheet)

    @classmethod
    def parse_sheet(cls, sheet: Worksheet) -> Dict[str, Any]:
        max_rows = min(sheet.max_row, 300)
        max_cols = min(sheet.max_column, 25)

        master_item_code = ""
        description = ""
        header_row_idx = -1
        col_indices: Dict[str, int] = {}

        # 1. Scan top 15 rows for Master Item Code and Description
        for r in range(1, min(16, max_rows + 1)):
            for c in range(1, max_cols + 1):
                val = get_merged_cell_value(sheet, r, c)
                if not val:
                    continue
                val_str = str(val).strip()

                # Look for Master Code
                if "ITEM CODE" in val_str.upper() or "MASTER CODE" in val_str.upper():
                    # Check next cells in same row or row below
                    for next_c in range(c + 1, min(c + 5, max_cols + 1)):
                        next_val = get_merged_cell_value(sheet, r, next_c)
                        if next_val and str(next_val).strip() and not ("ITEM CODE" in str(next_val).upper()):
                            master_item_code = str(next_val).strip()
                            break

                # Look for Description
                if "DESCRIPTION" in val_str.upper() and not description:
                    for next_c in range(c + 1, min(c + 5, max_cols + 1)):
                        next_val = get_merged_cell_value(sheet, r, next_c)
                        if next_val and str(next_val).strip() and len(str(next_val).strip()) > 5:
                            description = str(next_val).strip()
                            break

        # Fallback if master item code was formatted directly without label
        if not master_item_code:
            for r in range(1, 10):
                for c in range(1, 6):
                    val = get_merged_cell_value(sheet, r, c)
                    if val:
                        s = str(val).strip()
                        # Typical code pattern e.g. 31162814SD05076 (alphanumeric 12-18 chars)
                        if re.match(r'^\d{6,12}[A-Z0-9]{3,8}$', s):
                            master_item_code = s
                            break
                if master_item_code:
                    break

        if not master_item_code:
            master_item_code = "MANUAL_BOM_" + str(sheet.title).replace(" ", "_")

        if not description:
            description = f"Plant BOM for {master_item_code}"

        # 2. Locate Table Header Row
        for r in range(1, min(35, max_rows + 1)):
            row_vals = [str(get_merged_cell_value(sheet, r, c) or "").strip().upper() for c in range(1, max_cols + 1)]
            
            sr_col = -1
            name_col = -1
            dwg_col = -1
            qty_col = -1

            for c_idx, text in enumerate(row_vals, start=1):
                if any(k in text for k in ["SR NO", "SR. NO", "S.NO", "SL NO", "ITEM NO", "SR"]):
                    if sr_col == -1:
                        sr_col = c_idx
                elif any(k in text for k in ["ITEM NAME", "DESCRIPTION", "PART NAME", "MATERIAL DESCRIPTION"]):
                    if name_col == -1:
                        name_col = c_idx
                elif any(k in text for k in ["DRAWING NO", "DRG NO", "DRAWING NUMBER", "DRG. NO", "DWG NO"]):
                    if dwg_col == -1:
                        dwg_col = c_idx
                elif any(k in text for k in ["QTY", "QUANTITY", "TARGET QTY", "BOM QTY", "REQ QTY"]):
                    if qty_col == -1:
                        qty_col = c_idx

            matched_count = sum(1 for col in [sr_col, name_col, dwg_col, qty_col] if col != -1)
            if matched_count >= 3:
                header_row_idx = r
                col_indices = {
                    "sr": sr_col if sr_col != -1 else 1,
                    "name": name_col if name_col != -1 else 2,
                    "dwg": dwg_col if dwg_col != -1 else 3,
                    "qty": qty_col if qty_col != -1 else 4
                }
                break

        if header_row_idx == -1:
            # Fallback assumption: standard 4-column layout starting at row 3 or 4
            header_row_idx = 3
            col_indices = {"sr": 1, "name": 2, "dwg": 3, "qty": 4}

        # 3. Extract Line Items
        items: List[Dict[str, Any]] = []
        consecutive_empty = 0

        for r in range(header_row_idx + 1, max_rows + 1):
            sr_val = get_merged_cell_value(sheet, r, col_indices["sr"])
            name_val = get_merged_cell_value(sheet, r, col_indices["name"])
            dwg_val = get_merged_cell_value(sheet, r, col_indices["dwg"])
            qty_val = get_merged_cell_value(sheet, r, col_indices["qty"])

            if not name_val and not sr_val and not dwg_val:
                consecutive_empty += 1
                if consecutive_empty > 4:
                    break
                continue
            consecutive_empty = 0

            # Stop on total/summary row
            name_str = str(name_val or "").strip()
            if any(term in name_str.upper() for term in ["TOTAL", "GRAND TOTAL", "PREPARED BY", "APPROVED BY"]):
                break

            if not name_str:
                continue

            # Parse Sr No
            sr_no = len(items) + 1
            if sr_val is not None:
                try:
                    sr_no = int(float(str(sr_val).strip()))
                except (ValueError, TypeError):
                    pass

            # Parse Qty
            target_qty = 1
            if qty_val is not None:
                try:
                    target_qty = int(float(str(qty_val).strip()))
                except (ValueError, TypeError):
                    target_qty = 1

            # Determine Drawing No and canonical part_uid
            dwg_clean, is_valid_dwg = normalize_drawing_no(dwg_val)
            if is_valid_dwg and dwg_clean:
                part_uid = dwg_clean
                drawing_no = dwg_clean
            else:
                part_uid = generate_part_uid_slug(name_str)
                drawing_no = "—"

            # Determine packaging exclusion
            is_packaging = is_packaging_item(name_str)
            is_vision_inspected = not is_packaging

            items.append({
                "sr_no": sr_no,
                "part_uid": part_uid,
                "item_name": name_str,
                "drawing_no": drawing_no,
                "target_qty": target_qty,
                "is_vision_inspected": is_vision_inspected
            })

        total_items = len(items)
        vision_count = sum(1 for it in items if it["is_vision_inspected"])

        return {
            "master_item_code": master_item_code,
            "description": description,
            "sheet_name": sheet.title,
            "total_items": total_items,
            "vision_items_count": vision_count,
            "items": items
        }
