from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from database import get_db
from routers.auth import get_current_user_or_default
import models

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_default)
) -> Dict[str, Any]:
    """
    Retourne les statistiques clés pour le tableau de bord principal.
    """
    tenant_id = current_user.tenant_id
    
    # 1. Global Counts
    product_count = db.query(models.Product).filter_by(tenant_id=tenant_id).count()
    supplier_count = db.query(models.Supplier).filter_by(tenant_id=tenant_id).count()
    
    # 2. Stock Value (approx)
    # Sum of (quantity * unit_price) for all stock movements (snapshot) or just active products?
    # Better to use the query logic: sum(stock_level * unit_price)
    # But for speed, let's just sum (product.unit_price) for now or just return count.
    # Let's do a proper calculation if possible, or just "N/A" if expensive.
    # Simple calculation: Sum of Products priced * quantity (if we had a materialized view).
    # For now, let's mock the value or do a simple count.
    
    # 3. Data Sources
    data_sources = db.query(models.DataSource).filter_by(tenant_id=tenant_id).all()
    
    sources_data = []
    for ds in data_sources:
        sources_data.append({
            "id": str(ds.id),
            "name": ds.name,
            "type": ds.type.value if hasattr(ds.type, 'value') else str(ds.type),
            "status": ds.status.value if hasattr(ds.status, 'value') else str(ds.status),
            "updated_at": ds.updated_at
        })
        
    # 4. Warehouse/Categories
    category_count = db.query(models.Category).filter_by(tenant_id=tenant_id).count()

    return {
        "global_stats": {
            "total_products": product_count,
            "total_suppliers": supplier_count,
            "total_categories": category_count,
            "connected_sources": len(data_sources)
        },
        "data_sources": sources_data,
        "recent_alerts": [] # Placeholder
    }
