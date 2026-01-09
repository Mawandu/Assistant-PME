# routers/stock_movement.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from routers.data_source import get_current_user

router = APIRouter(
    prefix="/api/v1/movements",
    tags=['Stock Movements'],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=schemas.StockMovementOut, status_code=status.HTTP_201_CREATED)
async def create_movement(movement: schemas.StockMovementCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Vérifier que le produit appartient bien au tenant
    product = db.query(models.Product).filter(models.Product.id == movement.product_id, models.Product.tenant_id == current_user.tenant_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_movement = models.StockMovement(
        **movement.dict(),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id # On lie le mouvement à l'utilisateur qui fait l'action
    )
    try:
        db.add(new_movement)
        db.commit()
        db.refresh(new_movement)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_movement

@router.get("/", response_model=List[schemas.StockMovementOut])
async def list_movements(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.StockMovement).filter(models.StockMovement.tenant_id == current_user.tenant_id).limit(100).all()
