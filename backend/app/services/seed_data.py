"""
Pre-seeding logic for Plant BOM 31162814SD05076 and default Parts Catalog.
"""
import openpyxl
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.app.models.parts import PartsCatalog
from backend.app.models.recipe import BomRecipe, BomRecipeItem
from backend.app.config import SAMPLE_DATA_DIR

SAMPLE_MASTER_CODE = "31162814SD05076"
SAMPLE_DESCRIPTION = "HRD PKT FOR MAIN BODY 900W/1200W 560D KREATION"

SAMPLE_LINE_ITEMS = [
    {
        "sr_no": 1,
        "item_name": "WOOD SCREW CSK PHILLIPS HEAD 3.5X15 C1018 ST YP",
        "drawing_no": "HOM196273",
        "part_uid": "HOM196273",
        "target_qty": 8,
        "is_vision_inspected": True
    },
    {
        "sr_no": 2,
        "item_name": "WOOD SCREW PAN PHILLIPS HEAD 3.5X15 C1018 ST YP",
        "drawing_no": "HOM196276",
        "part_uid": "HOM196276",
        "target_qty": 10,
        "is_vision_inspected": True
    },
    {
        "sr_no": 3,
        "item_name": "WOOD SCREW PAN PHILLIPS HEAD 3.5X20 C1018 ST YP",
        "drawing_no": "HOM196277",
        "part_uid": "HOM196277",
        "target_qty": 2,
        "is_vision_inspected": True
    },
    {
        "sr_no": 4,
        "item_name": "WOOD SCREW PAN PHILLIPS HEAD 4.0X35 C1018 ST YP",
        "drawing_no": "HOM196280",
        "part_uid": "HOM196280",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 5,
        "item_name": "WOOD SCREW CSK PHILLIPS HEAD 4.0X45 C1018 ST YP",
        "drawing_no": "HOM196281",
        "part_uid": "HOM196281",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 6,
        "item_name": "DUST PLUG D8 BEIGE PA6",
        "drawing_no": "HOM196328",
        "part_uid": "HOM196328",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 7,
        "item_name": "DUST PLUG D5 WHITE PA6",
        "drawing_no": "HOM196329",
        "part_uid": "HOM196329",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 8,
        "item_name": "DUST PLUG D10 WHITE PA6",
        "drawing_no": "HOM196330",
        "part_uid": "HOM196330",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 9,
        "item_name": "DUST PLUG D10 BEIGE PA6",
        "drawing_no": "HOM196331",
        "part_uid": "HOM196331",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 10,
        "item_name": "HINGE EXPANSION DOWEL WITH M4 SCREW - CNS11",
        "drawing_no": "HRD104875",
        "part_uid": "HRD104875",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 11,
        "item_name": "SHELF SUPPORT PLUG D5 BRASS NICKLE PLATED CNS23",
        "drawing_no": "HRD104880",
        "part_uid": "HRD104880",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 12,
        "item_name": "METAL SHELF SUPPORT CNS20",
        "drawing_no": "HRD104885",
        "part_uid": "HRD104885",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 13,
        "item_name": "WOOD SCREW PAN PHILLIPS HEAD 4.0X25 C1018 ST YP",
        "drawing_no": "HOM196279",
        "part_uid": "HOM196279",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 14,
        "item_name": "CORNER CONNECTOR CNS30",
        "drawing_no": "HOM196306",
        "part_uid": "HOM196306",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 15,
        "item_name": "M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S",
        "drawing_no": "—",
        "part_uid": "NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 16,
        "item_name": "CARTON (470L × 140W × 55H)",
        "drawing_no": "—",
        "part_uid": "NO_DWG_CARTON_470L_140W_55H",
        "target_qty": 1,
        "is_vision_inspected": False
    }
]

def seed_database_sync(db: Session):
    """
    Synchronously pre-seeds the parts catalog and the sample recipe into SQLite.
    """
    # 1. Upsert Parts Catalog items with contiguous class IDs
    max_id = db.query(func.max(PartsCatalog.yolo_class_id)).scalar()
    next_class_id = 0 if max_id is None else max_id + 1

    for item in SAMPLE_LINE_ITEMS:
        part = db.query(PartsCatalog).filter_by(part_uid=item["part_uid"]).first()
        if not part:
            part = PartsCatalog(
                part_uid=item["part_uid"],
                item_name=item["item_name"],
                drawing_no=item["drawing_no"] if item["drawing_no"] != "—" else None,
                yolo_class_id=next_class_id,
                training_status="TRAINED" if item["is_vision_inspected"] else "UNTRAINED",
                sample_count=25 if item["is_vision_inspected"] else 0
            )
            db.add(part)
            db.flush()
            next_class_id += 1
    db.commit()

    # 2. Seed Sample BOM Recipe
    recipe = db.query(BomRecipe).filter_by(master_item_code=SAMPLE_MASTER_CODE).first()
    if not recipe:
        vision_count = sum(1 for it in SAMPLE_LINE_ITEMS if it["is_vision_inspected"])
        recipe = BomRecipe(
            master_item_code=SAMPLE_MASTER_CODE,
            description=SAMPLE_DESCRIPTION,
            total_items=len(SAMPLE_LINE_ITEMS),
            vision_items_count=vision_count
        )
        db.add(recipe)
        db.flush()

        for it in SAMPLE_LINE_ITEMS:
            recipe_item = BomRecipeItem(
                recipe_id=recipe.id,
                sr_no=it["sr_no"],
                part_uid=it["part_uid"],
                item_name=it["item_name"],
                drawing_no=it["drawing_no"],
                target_qty=it["target_qty"],
                is_vision_inspected=it["is_vision_inspected"]
            )
            db.add(recipe_item)
        db.commit()

    # 3. Create Sample Excel Spreadsheet file if not present
    create_sample_excel_file()

def create_sample_excel_file():
    """Generates a realistic plant BOM Excel spreadsheet with merged cells and headers."""
    excel_path = SAMPLE_DATA_DIR / f"BOM_{SAMPLE_MASTER_CODE}.xlsx"
    if excel_path.exists():
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOM Details"

    # Row 1: Title
    ws.merge_cells("A1:D1")
    ws["A1"] = "KHALAPUR PLANT - PACKING BILL OF MATERIALS"

    # Row 2: Master Item Code
    ws["A2"] = "Item Code(Master)"
    ws["B2"] = SAMPLE_MASTER_CODE
    ws["C2"] = "Description"
    ws["D2"] = SAMPLE_DESCRIPTION

    # Row 4: Headers
    headers = ["Sr No", "Item Name", "Drawing No", "Qty"]
    for col_idx, h in enumerate(headers, start=1):
        ws.cell(row=4, column=col_idx, value=h)

    # Line items
    for row_idx, item in enumerate(SAMPLE_LINE_ITEMS, start=5):
        ws.cell(row=row_idx, column=1, value=item["sr_no"])
        ws.cell(row=row_idx, column=2, value=item["item_name"])
        ws.cell(row=row_idx, column=3, value=item["drawing_no"])
        ws.cell(row=row_idx, column=4, value=item["target_qty"])

    wb.save(str(excel_path))
