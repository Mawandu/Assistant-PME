# routers/tenant.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(
    prefix="/api/v1/tenants",
    tags=['Tenants']
)

@router.post("/", response_model=schemas.TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_request: schemas.TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau tenant (entreprise cliente).
    """
    new_tenant = models.Tenant(company_name=tenant_request.company_name)
    try:
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create tenant: {e}"
        )
    return new_tenant

# Ajoutez d'autres endpoints pour les tenants ici (GET, PUT, DELETE...)
