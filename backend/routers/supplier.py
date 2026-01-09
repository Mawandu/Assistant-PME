# routers/supplier.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from routers.data_source import get_current_user

router = APIRouter(
    prefix="/api/v1/suppliers",
    tags=['Suppliers'],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=schemas.SupplierOut, status_code=status.HTTP_201_CREATED)
async def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_supplier = models.Supplier(**supplier.dict(), tenant_id=current_user.tenant_id)
    try:
        db.add(new_supplier)
        db.commit()
        db.refresh(new_supplier)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_supplier

@router.get("/", response_model=List[schemas.SupplierOut])
async def list_suppliers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Supplier).filter(models.Supplier.tenant_id == current_user.tenant_id).all()
