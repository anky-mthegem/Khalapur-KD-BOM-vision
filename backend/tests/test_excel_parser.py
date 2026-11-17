"""
Unit tests for Plant BOM Excel & CSV Parser.
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
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOM Details"

    ws.merge_cells("A1:D1")
    ws["A1"] = "KHALAPUR PLANT - PACKING BILL OF MATERIALS"

    ws["A2"] = "Item Code(Master)"
    ws["B2"] = "31162814SD05076"
    ws["C2"] = "Description"
    ws["D2"] = "HRD PKT FOR MAIN BODY 900W/1200W 560D KREATION"

    headers = ["Sr No", "Item Name", "Drawing No", "Qty"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=4, column=c, value=h)

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
        parsed = PlantExcelBomParser.parse_file(tmp_path)
        assert parsed["master_item_code"] == "31162814SD05076"
        assert "HRD PKT" in parsed["description"]
        assert parsed["total_items"] == 4
        assert parsed["vision_items_count"] == 3

        items = parsed["items"]
        assert items[0]["part_uid"] == "HOM196273"
        assert items[0]["is_vision_inspected"] is True
        assert items[2]["part_uid"] == "NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S"
        assert items[3]["is_vision_inspected"] is False
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def test_standard_csv_bom_parser():
    """Tests the exact user-attached plant BOM CSV format."""
    csv_content = ''',Item Code(Master),31162814SD05076,
,Description,HRD PKT FOR MAIN BODY 900W/1200W 560D KREATION X3 (HRD199065),
Sr No,Item Name,Drawing No,Qty
1,LEVELER FOR LEG KREATION X3,HOM196273,2
2,SHELF SUPPORT,DOS210915,8
3,"HEX NUT (3/16"" BSW)",HRD100314,8
4,RD. HD COMBI SLOT SCREW 3/16 X 3/8,HRD131022,8
5,M4x12L PH HD CSK SCREW ZN PLATED,HRD163160,12
6,COMBI PAN HD INT WASH M4x12 SCREW,HRD104875,50
7,"Sensys Hinge - 24 mm - 0 Crank, Order No. 9214915, Mounting Plate 9310304",EOM146525,6
8,PLASTIC HOLDER FOR HANGING ROD KREATION X3,HOM200187,2
9,HEX HEAD BOLT M4 X 6MM ZN BLUE PLATING,HRD204111,2
10,PLATE FOR HANGING ROD FIXING KREATION X3,HOM164412,2
11,CSK ST SCREW NO 6 X 25,HRD100690,8
12,PH CW SELF TAP SCR NO 6 x 13L,HRD100804,6
13,STUD,HOM144640,6
14,CAP FOR BACK PANEL OF WALL UNIT STEEL KITCHEN,HOM195865,2
15,M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S,—,6
16,CARTON (470L × 140W × 55H),—,1
'''
    with NamedTemporaryFile(suffix=".csv", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        parsed = PlantExcelBomParser.parse_file(tmp_path)
        assert parsed["master_item_code"] == "31162814SD05076"
        assert "KREATION X3" in parsed["description"]
        assert parsed["total_items"] == 16
        assert parsed["vision_items_count"] == 15  # Carton excluded

        items = parsed["items"]
        # Line 1: LEVELER FOR LEG KREATION X3
        assert items[0]["part_uid"] == "HOM196273"
        assert items[0]["target_qty"] == 2
        assert items[0]["is_vision_inspected"] is True

        # Line 6: COMBI PAN HD INT WASH M4x12 SCREW (50 qty)
        assert items[5]["drawing_no"] == "HRD104875"
        assert items[5]["target_qty"] == 50

        # Line 15: M4 SLEEVE -> slugged
        assert items[14]["part_uid"] == "NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S"
        assert items[14]["target_qty"] == 6
        assert items[14]["is_vision_inspected"] is True

        # Line 16: CARTON -> excluded
        assert items[15]["is_vision_inspected"] is False
        assert items[15]["target_qty"] == 1
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def test_pasted_bom_parser():
    pasted_text = (
        "Item Code(Master)\t31162814SD05076\n"
        "Description\tHRD PKT FOR MAIN BODY 900W/1200W 560D KREATION X3\n"
        "Sr No\tItem Name\tDrawing No\tQty\n"
        "1\tWOOD SCREW CSK 3.5X15\tHOM196273\t8\n"
        "2\tM4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S\t—\t4\n"
        "3\tCARTON (470L X 140W X 55H)\t—\t1\n"
    )
    parsed = PlantExcelBomParser.parse_raw_text(pasted_text)
    assert parsed["master_item_code"] == "31162814SD05076"
    assert parsed["total_items"] == 3
    assert parsed["vision_items_count"] == 2
    assert parsed["items"][1]["drawing_no"] == "—"
    assert parsed["items"][1]["part_uid"].startswith("NO_DWG_")
    assert parsed["items"][2]["is_vision_inspected"] is False
