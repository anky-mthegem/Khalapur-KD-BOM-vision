"""
BOM Recipe Management Routes:
Upload Excel preview, commit confirmed recipes, list and view recipes, toggle vision inspection.
"""
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any

from backend.app.database import get_db
from backend.app.models.recipe import BomRecipe, BomRecipeItem
from backend.app.models.parts import PartsCatalog
from backend.app.schemas.recipe import (
    BomPreviewResponse, BomCommitRequest, RecipeResponse, RecipeItemResponse
)
from backend.app.services.excel_parser import PlantExcelBomParser

router = APIRouter(prefix="/api/bom", tags=["BOM Recipes"])

@router.post("/upload-preview", response_model=BomPreviewResponse)
async def upload_bom_preview(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Parses an uploaded plant Excel BOM (.xlsx or .xls), extracts metadata,
    and returns a preview without saving to the database.
    """
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported.")

    suffix = Path(file.filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        parsed_data = PlantExcelBomParser.parse_workbook(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    # Query existing parts in catalog to flag new vs existing
    result = await db.execute(select(PartsCatalog.part_uid, PartsCatalog.training_status))
    existing_catalog = {row[0]: row[1] for row in result.all()}

    preview_items = []
    new_parts_count = 0
    excluded_count = 0

    for item in parsed_data["items"]:
        p_uid = item["part_uid"]
        is_new = p_uid not in existing_catalog
        if is_new:
            new_parts_count += 1
        if not item["is_vision_inspected"]:
            excluded_count += 1

        training_status = existing_catalog.get(p_uid, "UNTRAINED")

        preview_items.append({
            "sr_no": item["sr_no"],
            "part_uid": p_uid,
            "item_name": item["item_name"],
            "drawing_no": item["drawing_no"],
            "target_qty": item["target_qty"],
            "is_vision_inspected": item["is_vision_inspected"],
            "is_new_part": is_new,
            "training_status": training_status
        })

    return {
        "master_item_code": parsed_data["master_item_code"],
        "description": parsed_data["description"],
        "sheet_name": parsed_data["sheet_name"],
        "total_items": parsed_data["total_items"],
        "vision_items_count": parsed_data["vision_items_count"],
        "excluded_packaging_count": excluded_count,
        "new_parts_count": new_parts_count,
        "items": preview_items
    }

@router.post("/commit")
async def commit_bom_recipe(payload: BomCommitRequest, db: AsyncSession = Depends(get_db)):
    """
    Commits a previewed recipe to SQLite and registers any new parts in parts_catalog.
    """
    # 1. Upsert missing parts in parts_catalog
    for item in payload.items:
        res = await db.execute(select(PartsCatalog).filter_by(part_uid=item.part_uid))
        part = res.scalars().first()
        if not part:
            max_id_res = await db.execute(select(func.max(PartsCatalog.yolo_class_id)))
            max_id = max_id_res.scalar()
            next_class_id = 0 if max_id is None else max_id + 1

            new_part = PartsCatalog(
                part_uid=item.part_uid,
                item_name=item.item_name,
                drawing_no=item.drawing_no if item.drawing_no != "—" else None,
                yolo_class_id=next_class_id,
                training_status="UNTRAINED",
                sample_count=0
            )
            db.add(new_part)
    await db.commit()

    # 2. Upsert Recipe
    res = await db.execute(select(BomRecipe).filter_by(master_item_code=payload.master_item_code))
    recipe = res.scalars().first()

    vision_count = sum(1 for it in payload.items if it.is_vision_inspected)

    if not recipe:
        recipe = BomRecipe(
            master_item_code=payload.master_item_code,
            description=payload.description,
            total_items=len(payload.items),
            vision_items_count=vision_count
        )
        db.add(recipe)
        await db.flush()
    else:
        recipe.description = payload.description
        recipe.total_items = len(payload.items)
        recipe.vision_items_count = vision_count
        # Clear existing items
        await db.execute(select(BomRecipeItem).filter_by(recipe_id=recipe.id))
        for existing_it in (await db.execute(select(BomRecipeItem).filter_by(recipe_id=recipe.id))).scalars().all():
            await db.delete(existing_it)

    # Insert line items
    for it in payload.items:
        line_item = BomRecipeItem(
            recipe_id=recipe.id,
            sr_no=it.sr_no,
            part_uid=it.part_uid,
            item_name=it.item_name,
            drawing_no=it.drawing_no,
            target_qty=it.target_qty,
            is_vision_inspected=it.is_vision_inspected
        )
        db.add(line_item)

    await db.commit()
    return {"status": "SUCCESS", "master_item_code": recipe.master_item_code, "total_items": recipe.total_items}

@router.get("/recipes")
async def list_recipes(db: AsyncSession = Depends(get_db)):
    """Lists all stored BOM recipes."""
    res = await db.execute(select(BomRecipe).order_by(BomRecipe.master_item_code))
    recipes = res.scalars().all()
    return [r.to_dict() for r in recipes]

@router.get("/recipes/{master_code}")
async def get_recipe_detail(master_code: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full recipe items for a Master Item Code."""
    res = await db.execute(select(BomRecipe).filter_by(master_item_code=master_code))
    recipe = res.scalars().first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return recipe.to_dict()

@router.patch("/items/{item_id}/vision-toggle")
async def toggle_vision_inspection(item_id: int, db: AsyncSession = Depends(get_db)):
    """Manually toggles is_vision_inspected boolean for a specific line item."""
    res = await db.execute(select(BomRecipeItem).filter_by(id=item_id))
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Recipe item not found.")

    item.is_vision_inspected = not item.is_vision_inspected
    
    # Update parent recipe vision count
    res_recipe = await db.execute(select(BomRecipe).filter_by(id=item.recipe_id))
    recipe = res_recipe.scalars().first()
    if recipe:
        items_res = await db.execute(select(BomRecipeItem).filter_by(recipe_id=recipe.id))
        all_items = items_res.scalars().all()
        recipe.vision_items_count = sum(1 for it in all_items if it.is_vision_inspected)

    await db.commit()
    return {"id": item.id, "is_vision_inspected": item.is_vision_inspected}
