from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.csv_import import import_csv

router = APIRouter(prefix="/upload", tags=["upload"])


class ImportResult(BaseModel):
    success: bool
    inserted: int
    skipped: int
    errors: Optional[List[str]] = None
    message: str


@router.post("/csv", response_model=ImportResult)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    result = import_csv(db, contents, file.filename)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result.get("error", "Import failed"))

    return ImportResult(
        success=True,
        inserted=result["inserted"],
        skipped=result["skipped"],
        errors=result.get("errors", []),
        message=f"Import complete: {result['inserted']} records inserted, {result['skipped']} skipped.",
    )
