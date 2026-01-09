# routers/category.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from routers.data_source import get_current_user

router = APIRouter(
    prefix="/api/v1/categories",
    tags=['Categories'],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_category = models.Category(**category.dict(), tenant_id=current_user.tenant_id)
    try:
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_category

@router.get("/", response_model=List[schemas.CategoryOut])
async def list_categories(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Category).filter(models.Category.tenant_id == current_user.tenant_id).all()
