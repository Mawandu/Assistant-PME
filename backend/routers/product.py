# routers/product.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional # Ensure List and Optional are imported

import models, schemas
from database import get_db
from routers.data_source import get_current_user

router = APIRouter(
    prefix="/api/v1/products",
    tags=['Products'],
    dependencies=[Depends(get_current_user)] # Secure all routes in this router
)

@router.post("/", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_request: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crée un nouveau produit pour le tenant de l'utilisateur courant.
    """
    # Vérifier si le SKU existe déjà pour ce tenant
    existing_product = db.query(models.Product).filter(
        models.Product.tenant_id == current_user.tenant_id,
        models.Product.sku == product_request.sku
    ).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product_request.sku}' already exists for this tenant."
        )

    # Vérifier si category_id et supplier_id appartiennent au bon tenant (si fournis)
    if product_request.category_id:
        category = db.query(models.Category).filter(
            models.Category.id == product_request.category_id,
            models.Category.tenant_id == current_user.tenant_id).first()
        if not category:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {product_request.category_id} not found for this tenant.")
    if product_request.supplier_id:
        supplier = db.query(models.Supplier).filter(
            models.Supplier.id == product_request.supplier_id,
            models.Supplier.tenant_id == current_user.tenant_id).first()
        if not supplier:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier {product_request.supplier_id} not found for this tenant.")


    new_product = models.Product(
        **product_request.dict(),
        tenant_id=current_user.tenant_id
    )
    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create product: {e}"
        )
    return new_product

@router.get("/", response_model=List[schemas.ProductOut])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search term for product name or description"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    supplier_id: Optional[uuid.UUID] = Query(None, description="Filter by supplier ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Liste les produits pour le tenant de l'utilisateur courant, avec pagination et filtres optionnels.
    """
    query = db.query(models.Product).filter(models.Product.tenant_id == current_user.tenant_id)

    # Apply filters
    if search:
         # Basic search on name/description (adjust for full-text search if index exists)
         search_term = f"%{search}%"
         query = query.filter(
             (models.Product.name.ilike(search_term)) |
             (models.Product.description.ilike(search_term)) |
             (models.Product.sku.ilike(search_term)) # Also search SKU
        )
    if category_id:
         query = query.filter(models.Product.category_id == category_id)
    if supplier_id:
         query = query.filter(models.Product.supplier_id == supplier_id)
    if is_active is not None:
         query = query.filter(models.Product.is_active == is_active)


    products = query.order_by(models.Product.name).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=schemas.ProductOut)
async def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère les détails d'un produit spécifique par son ID.
    Vérifie que le produit appartient bien au tenant de l'utilisateur.
    """
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.tenant_id == current_user.tenant_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found."
        )
    return product

# TODO: Ajouter endpoints PUT pour la mise à jour et DELETE pour la suppression
# TODO: Considérer l'ajout de relations imbriquées (category, supplier) dans ProductOut si nécessaire
