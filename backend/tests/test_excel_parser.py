"""
Unit tests for Plant BOM Excel Parser.
"""
import openpyxl
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from backend.app.services.excel_parser import PlantExcelBomParser, generate_part_uid_slug, is_packaging_item

def test_slug_generation():
    name = "M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S"
    slug = generate_part_uid_slug(name)
    assert slug == "NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S"
    assert slug.startswith("NO_DWG_")

def test_packaging_detection():
    assert is_packaging_item("CARTON (470L X 140W X 55H)") is True
    assert is_packaging_item("CORRUGATED BOX TYPE-A") is True
    assert is_packaging_item("MASTER BAG PLASTIC") is True
    assert is_packaging_item("WOOD SCREW CSK 3.5X15") is False
    assert is_packaging_item("HINGE EXPANSION DOWEL") is False

def test_excel_parser_merged_headers_and_items():
    # Create temporary workbook simulating plant layout
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOM Details"

    # Merged title
    ws.merge_cells("A1:D1")
    ws["A1"] = "KHALAPUR PLANT - PACKING BILL OF MATERIALS"

    # Row 2: Master Code and Description
    ws["A2"] = "Item Code(Master)"
    ws["B2"] = "31162814SD05076"
    ws["C2"] = "Description"
    ws["D2"] = "HRD PKT FOR MAIN BODY 900W/1200W 560D KREATION"

    # Row 4: Headers
    headers = ["Sr No", "Item Name", "Drawing No", "Qty"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=4, column=c, value=h)

    # Line items
    test_items = [
        (1, "WOOD SCREW CSK 3.5X15", "HOM196273", 8),
        (2, "DUST PLUG D8 BEIGE", "HOM196328", 4),
        (3, "M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S", "—", 4),
        (4, "CARTON (470L X 140W X 55H)", "—", 1),
    ]

    for r_idx, (sr, name, dwg, qty) in enumerate(test_items, 5):
        ws.cell(row=r_idx, column=1, value=sr)
        ws.cell(row=r_idx, column=2, value=name)
        ws.cell(row=r_idx, column=3, value=dwg)
        ws.cell(row=r_idx, column=4, value=qty)

    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        wb.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        parsed = PlantExcelBomParser.parse_workbook(tmp_path)
        assert parsed["master_item_code"] == "31162814SD05076"
        assert "HRD PKT" in parsed["description"]
        assert parsed["total_items"] == 4
        assert parsed["vision_items_count"] == 3  # Carton excluded

        items = parsed["items"]
        # Item 1: Valid drawing
        assert items[0]["part_uid"] == "HOM196273"
        assert items[0]["is_vision_inspected"] is True

        # Item 3: Missing drawing -> slugged
        assert items[2]["part_uid"] == "NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S"
        assert items[2]["drawing_no"] == "—"
        assert items[2]["is_vision_inspected"] is True

        # Item 4: Carton -> excluded
        assert items[3]["is_vision_inspected"] is False
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
