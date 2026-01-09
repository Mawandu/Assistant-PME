# schemas.py
import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from datetime import datetime
from typing import Dict, Any, List, Optional 
from models import UserRole, DataSourceType, DataSourceStatus, SubscriptionTier 

# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None

class TenantBase(BaseModel):
    company_name: str

class DataSourceBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    type: DataSourceType
    connection_config: Dict[str, Any] | None = None
    sync_enabled: bool = False
    sync_frequency_minutes: int | None = None

    @field_validator('sync_frequency_minutes')
    @classmethod
    def validate_sync_frequency(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        if info.data.get('sync_enabled') and (v is None or v <= 0):
            raise ValueError('sync_frequency_minutes must be positive if sync is enabled')
        return v

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    parent_id: uuid.UUID | None = None

class WarehouseBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    address: str | None = None
    is_active: bool = True

class SupplierBase(BaseModel):
    name: str = Field(..., max_length=255)
    code: str | None = Field(None, max_length=50)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(None, max_length=50)
    address: str | None = None
    lead_time_days: int | None = Field(7, ge=0)
    rating: float | None = Field(None, ge=0, le=5)
    is_active: bool = True

class ProductBase(BaseModel):
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    unit_price: float | None = Field(None, ge=0)
    cost_price: float | None = Field(None, ge=0)
    currency: str | None = Field('EUR', max_length=3)
    unit_of_measure: str | None = Field(None, max_length=20)
    reorder_point: int | None = Field(None, ge=0)
    reorder_quantity: int | None = Field(None, gt=0) 
    lead_time_days: int | None = Field(None, ge=0)
    custom_data: Dict[str, Any] | None = {}
    is_active: bool = True

class StockMovementBase(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID | None = None
    movement_type: str = Field(..., max_length=20) 
    quantity: int 
    unit_cost: float | None = Field(None, ge=0)
    reference_type: str | None = Field(None, max_length=50)
    reference_id: str | None = Field(None, max_length=100)
    user_id: uuid.UUID | None = None
    notes: str | None = None
    movement_metadata: Dict[str, Any] | None = {}
    timestamp: datetime | None = None 

# --- Create Schemas ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class TenantCreate(TenantBase):
    # Could add fields like subscription_tier, etc. during creation later
    pass

class DataSourceCreate(DataSourceBase):
    pass

class CategoryCreate(CategoryBase):
    pass

class WarehouseCreate(WarehouseBase):
    pass

class SupplierCreate(SupplierBase):
    pass

class ProductCreate(ProductBase):
    pass

class StockMovementCreate(StockMovementBase):
    pass

# --- Update Schemas (Allowing partial updates) ---
class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    connection_config: Optional[Dict[str, Any]] = None
    sync_enabled: Optional[bool] = None
    sync_frequency_minutes: Optional[int] = None
    status: Optional[DataSourceStatus] = None

    # Re-using the validator for consistency if sync_enabled/frequency are updated
    @field_validator('sync_frequency_minutes')
    @classmethod
    def validate_sync_frequency_update(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError('sync_frequency_minutes must be positive')
        return v

# --- Output Schemas (What the API returns) ---
class UserOut(UserBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    role: UserRole
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True

class TenantOut(TenantBase):
    id: uuid.UUID
    subscription_tier: SubscriptionTier 
    created_at: datetime
    updated_at: datetime 

    class Config:
        from_attributes = True 

class DataSourceOut(DataSourceBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: DataSourceStatus
    created_at: datetime
    updated_at: datetime
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    

    class Config:
        from_attributes = True 

class CategoryOut(CategoryBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    level: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class WarehouseOut(WarehouseBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SupplierOut(SupplierBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ProductOut(ProductBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Optionally include nested Category/Supplier info here if needed for specific endpoints
    # category: Optional[CategoryOut] = None
    # supplier: Optional[SupplierOut] = None

    class Config:
        from_attributes = True

class StockMovementOut(StockMovementBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    timestamp: datetime # Ensure timestamp is always present on output
    created_at: datetime
    # Optionally include nested Product/Warehouse info
    # product_sku: Optional[str] = None # Example: Add SKU for easier identification
    # warehouse_code: Optional[str] = None # Example: Add Warehouse Code

    class Config:
        from_attributes = True

# --- Special Schemas (e.g., for nested structures) ---
class CategoryWithChildren(CategoryOut):
    children: List['CategoryWithChildren'] = []

# Update forward refs if needed after all schemas defined (Pydantic v2 might handle this better)
CategoryWithChildren.model_rebuild()