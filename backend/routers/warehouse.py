# routers/warehouse.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from routers.data_source import get_current_user

router = APIRouter(
    prefix="/api/v1/warehouses",
    tags=['Warehouses'],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=schemas.WarehouseOut, status_code=status.HTTP_201_CREATED)
async def create_warehouse(warehouse: schemas.WarehouseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_warehouse = models.Warehouse(**warehouse.dict(), tenant_id=current_user.tenant_id)
    try:
        db.add(new_warehouse)
        db.commit()
        db.refresh(new_warehouse)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_warehouse

@router.get("/", response_model=List[schemas.WarehouseOut])
async def list_warehouses(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Warehouse).filter(models.Warehouse.tenant_id == current_user.tenant_id).all()
