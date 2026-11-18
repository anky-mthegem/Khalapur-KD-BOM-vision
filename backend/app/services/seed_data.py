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

SAMPLE_RECIPE_2_CODE = "31162814SD06001"
SAMPLE_RECIPE_2_DESC = "HARDWARE PACK - KREATION 600W BASE UNIT"

SAMPLE_RECIPE_2_ITEMS = [
    {
        "sr_no": 1,
        "item_name": "LEVELER FOR LEG KREATION X3",
        "drawing_no": "HOM196273",
        "part_uid": "HOM196273",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 2,
        "item_name": "SHELF SUPPORT",
        "drawing_no": "DOS210915",
        "part_uid": "DOS210915",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 3,
        "item_name": 'HEX NUT (3/16" BSW)',
        "drawing_no": "HRD100314",
        "part_uid": "HRD100314",
        "target_qty": 4,
        "is_vision_inspected": True
    },
    {
        "sr_no": 4,
        "item_name": "M4x12L PH HD CSK SCREW ZN PLATED",
        "drawing_no": "HRD163160",
        "part_uid": "HRD163160",
        "target_qty": 8,
        "is_vision_inspected": True
    },
    {
        "sr_no": 5,
        "item_name": "CARTON (470L × 140W × 55H)",
        "drawing_no": "—",
        "part_uid": "NO_DWG_CARTON_470L_140W_55H",
        "target_qty": 1,
        "is_vision_inspected": False
    }
]

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
                training_status="UNTRAINED",
                sample_count=0
            )
            db.add(part)
            db.flush()
            next_class_id += 1
        else:
            # Update attributes if needed
            part.item_name = item["item_name"]
            part.drawing_no = item["drawing_no"] if item["drawing_no"] != "—" else None

    # Sync sample counts and training status to reflect real dataset labels on disk
    from backend.app.config import DATASETS_DIR
    labels_dir = DATASETS_DIR / "labels" / "train"
    real_counts = {}
    if labels_dir.exists():
        for f in labels_dir.glob("*.txt"):
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    tokens = line.strip().split()
                    if tokens:
                        cls_idx = int(tokens[0])
                        real_counts[cls_idx] = real_counts.get(cls_idx, 0) + 1
            except Exception:
                pass

    for part in db.query(PartsCatalog).all():
        real_n = real_counts.get(part.yolo_class_id, 0)
        part.sample_count = real_n
        part.training_status = "LABELED" if real_n > 0 else "UNTRAINED"

    db.commit()

    # 2. Seed Sample BOM Recipes (Multiple Recipes Supported)
    recipes_to_seed = [
        (SAMPLE_MASTER_CODE, SAMPLE_DESCRIPTION, SAMPLE_LINE_ITEMS),
        (SAMPLE_RECIPE_2_CODE, SAMPLE_RECIPE_2_DESC, SAMPLE_RECIPE_2_ITEMS)
    ]

    for m_code, m_desc, m_items in recipes_to_seed:
        recipe = db.query(BomRecipe).filter_by(master_item_code=m_code).first()
        vision_count = sum(1 for it in m_items if it["is_vision_inspected"])

        if not recipe:
            recipe = BomRecipe(
                master_item_code=m_code,
                description=m_desc,
                total_items=len(m_items),
                vision_items_count=vision_count
            )
            db.add(recipe)
            db.flush()
        else:
            recipe.description = m_desc
            recipe.total_items = len(m_items)
            recipe.vision_items_count = vision_count
            for old_it in db.query(BomRecipeItem).filter_by(recipe_id=recipe.id).all():
                db.delete(old_it)
            db.flush()

        for it in m_items:
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
    for m_code, m_desc, m_items in [
        (SAMPLE_MASTER_CODE, SAMPLE_DESCRIPTION, SAMPLE_LINE_ITEMS),
        (SAMPLE_RECIPE_2_CODE, SAMPLE_RECIPE_2_DESC, SAMPLE_RECIPE_2_ITEMS)
    ]:
        excel_path = SAMPLE_DATA_DIR / f"BOM_{m_code}.xlsx"
        csv_path = SAMPLE_DATA_DIR / f"BOM_{m_code}.csv"

        # 1. Create standard CSV
        lines = [
            f",Item Code(Master),{m_code},",
            f",Description,{m_desc},",
            "Sr No,Item Name,Drawing No,Qty"
        ]
        for it in m_items:
            lines.append(f'{it["sr_no"]},"{it["item_name"]}",{it["drawing_no"]},{it["target_qty"]}')

        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        # 2. Create standard Excel (.xlsx) matching exact plant layout
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BOM Details"

        ws.cell(row=1, column=2, value="Item Code(Master)")
        ws.cell(row=1, column=3, value=m_code)

        ws.cell(row=2, column=2, value="Description")
        ws.cell(row=2, column=3, value=m_desc)

        headers = ["Sr No", "Item Name", "Drawing No", "Qty"]
        for col_idx, h in enumerate(headers, start=1):
            ws.cell(row=3, column=col_idx, value=h)

        for row_idx, item in enumerate(m_items, start=4):
            ws.cell(row=row_idx, column=1, value=item["sr_no"])
            ws.cell(row=row_idx, column=2, value=item["item_name"])
            ws.cell(row=row_idx, column=3, value=item["drawing_no"])
            ws.cell(row=row_idx, column=4, value=item["target_qty"])

        wb.save(str(excel_path))
