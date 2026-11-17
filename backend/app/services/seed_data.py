"""
Pre-seeding logic for Standard Plant BOM 31162814SD05076 and Parts Catalog.
"""
import openpyxl
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.app.models.parts import PartsCatalog
from backend.app.models.recipe import BomRecipe, BomRecipeItem
from backend.app.config import SAMPLE_DATA_DIR

SAMPLE_MASTER_CODE = "31162814SD05076"
SAMPLE_DESCRIPTION = "HRD PKT FOR MAIN BODY 900W/1200W 560D KREATION X3 (HRD199065)"

SAMPLE_LINE_ITEMS = [
    {
        "sr_no": 1,
        "item_name": "LEVELER FOR LEG KREATION X3",
        "drawing_no": "HOM196273",
        "part_uid": "HOM196273",
        "target_qty": 2,
        "is_vision_inspected": True
    },
    {
        "sr_no": 2,
        "item_name": "SHELF SUPPORT",
        "drawing_no": "DOS210915",
        "part_uid": "DOS210915",
        "target_qty": 8,
        "is_vision_inspected": True
    },
    {
        "sr_no": 3,
        "item_name": 'HEX NUT (3/16" BSW)',
        "drawing_no": "HRD100314",
        "part_uid": "HRD100314",
        "target_qty": 8,
        "is_vision_inspected": True
    },
    {
        "sr_no": 4,
        "item_name": "RD. HD COMBI SLOT SCREW 3/16 X 3/8",
        "drawing_no": "HRD131022",
        "part_uid": "HRD131022",
        "target_qty": 8,
        "is_vision_inspected": True
    },
    {
        "sr_no": 5,
        "item_name": "M4x12L PH HD CSK SCREW ZN PLATED",
        "drawing_no": "HRD163160",
        "part_uid": "HRD163160",
        "target_qty": 12,
        "is_vision_inspected": True
    },
    {
        "sr_no": 6,
        "item_name": "COMBI PAN HD INT WASH M4x12 SCREW",
        "drawing_no": "HRD104875",
        "part_uid": "HRD104875",
        "target_qty": 50,
        "is_vision_inspected": True
    },
    {
        "sr_no": 7,
        "item_name": "Sensys Hinge - 24 mm - 0 Crank, Order No. 9214915, Mounting Plate 9310304",
        "drawing_no": "EOM146525",
        "part_uid": "EOM146525",
        "target_qty": 6,
        "is_vision_inspected": True
    },
    {
        "sr_no": 8,
        "item_name": "PLASTIC HOLDER FOR HANGING ROD KREATION X3",
        "drawing_no": "HOM200187",
        "part_uid": "HOM200187",
        "target_qty": 2,
        "is_vision_inspected": True
    },
    {
        "sr_no": 9,
        "item_name": "HEX HEAD BOLT M4 X 6MM ZN BLUE PLATING",
        "drawing_no": "HRD204111",
        "part_uid": "HRD204111",
        "target_qty": 2,
        "is_vision_inspected": True
    },
    {
        "sr_no": 10,
        "item_name": "PLATE FOR HANGING ROD FIXING KREATION X3",
        "drawing_no": "HOM164412",
        "part_uid": "HOM164412",
        "target_qty": 2,
        "is_vision_inspected": True
    },
    {
        "sr_no": 11,
        "item_name": "CSK ST SCREW NO 6 X 25",
        "drawing_no": "HRD100690",
        "part_uid": "HRD100690",
        "target_qty": 8,
        "is_vision_inspected": True
    },
    {
        "sr_no": 12,
        "item_name": "PH CW SELF TAP SCR NO 6 x 13L",
        "drawing_no": "HRD100804",
        "part_uid": "HRD100804",
        "target_qty": 6,
        "is_vision_inspected": True
    },
    {
        "sr_no": 13,
        "item_name": "STUD",
        "drawing_no": "HOM144640",
        "part_uid": "HOM144640",
        "target_qty": 6,
        "is_vision_inspected": True
    },
    {
        "sr_no": 14,
        "item_name": "CAP FOR BACK PANEL OF WALL UNIT STEEL KITCHEN",
        "drawing_no": "HOM195865",
        "part_uid": "HOM195865",
        "target_qty": 2,
        "is_vision_inspected": True
    },
    {
        "sr_no": 15,
        "item_name": "M4 SLEEVE CONNECTING SCREW MAKE EBCO - CNS35-S",
        "drawing_no": "—",
        "part_uid": "NO_DWG_M4_SLEEVE_CONNECTING_SCREW_MAKE_EBCO_CNS35_S",
        "target_qty": 6,
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
        else:
            # Update attributes if needed
            part.item_name = item["item_name"]
            part.drawing_no = item["drawing_no"] if item["drawing_no"] != "—" else None
    db.commit()

    # 2. Seed Sample BOM Recipe
    recipe = db.query(BomRecipe).filter_by(master_item_code=SAMPLE_MASTER_CODE).first()
    vision_count = sum(1 for it in SAMPLE_LINE_ITEMS if it["is_vision_inspected"])

    if not recipe:
        recipe = BomRecipe(
            master_item_code=SAMPLE_MASTER_CODE,
            description=SAMPLE_DESCRIPTION,
            total_items=len(SAMPLE_LINE_ITEMS),
            vision_items_count=vision_count
        )
        db.add(recipe)
        db.flush()
    else:
        recipe.description = SAMPLE_DESCRIPTION
        recipe.total_items = len(SAMPLE_LINE_ITEMS)
        recipe.vision_items_count = vision_count
        # Remove old items and re-insert
        for old_it in db.query(BomRecipeItem).filter_by(recipe_id=recipe.id).all():
            db.delete(old_it)
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

    # 3. Create Sample Excel Spreadsheet and CSV files
    create_sample_files()

def create_sample_files():
    """Generates the exact standard plant BOM Excel (.xlsx) and CSV files."""
    excel_path = SAMPLE_DATA_DIR / f"BOM_{SAMPLE_MASTER_CODE}.xlsx"
    csv_path = SAMPLE_DATA_DIR / f"BOM_{SAMPLE_MASTER_CODE}.csv"

    # 1. Create standard CSV
    lines = [
        f",Item Code(Master),{SAMPLE_MASTER_CODE},",
        f",Description,{SAMPLE_DESCRIPTION},",
        "Sr No,Item Name,Drawing No,Qty"
    ]
    for it in SAMPLE_LINE_ITEMS:
        lines.append(f'{it["sr_no"]},"{it["item_name"]}",{it["drawing_no"]},{it["target_qty"]}')

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # 2. Create standard Excel (.xlsx) matching exact plant layout
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOM Details"

    # Row 1: ,Item Code(Master),31162814SD05076,
    ws.cell(row=1, column=2, value="Item Code(Master)")
    ws.cell(row=1, column=3, value=SAMPLE_MASTER_CODE)

    # Row 2: ,Description,HRD PKT FOR MAIN BODY...
    ws.cell(row=2, column=2, value="Description")
    ws.cell(row=2, column=3, value=SAMPLE_DESCRIPTION)

    # Row 3: Headers
    headers = ["Sr No", "Item Name", "Drawing No", "Qty"]
    for col_idx, h in enumerate(headers, start=1):
        ws.cell(row=3, column=col_idx, value=h)

    # Line items starting from row 4
    for row_idx, item in enumerate(SAMPLE_LINE_ITEMS, start=4):
        ws.cell(row=row_idx, column=1, value=item["sr_no"])
        ws.cell(row=row_idx, column=2, value=item["item_name"])
        ws.cell(row=row_idx, column=3, value=item["drawing_no"])
        ws.cell(row=row_idx, column=4, value=item["target_qty"])

    wb.save(str(excel_path))
