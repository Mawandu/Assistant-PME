# models.py
import uuid
from sqlalchemy import (
    Column, String, DateTime, func, ForeignKey, JSON, Enum as SQLAlchemyEnum,
    Boolean, Integer, Text, Index, UniqueConstraint, DECIMAL, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import LtreeType
from sqlalchemy.orm import relationship, declarative_base
# from database import Base <--- REMOVED

Base = declarative_base()
import enum

# --- Enums ---
class SubscriptionTier(str, enum.Enum):
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    READER = "READER"

class DataSourceType(str, enum.Enum):
    FILE_UPLOAD = "FILE_UPLOAD"
    SQL_CONNECTOR = "SQL_CONNECTOR"
    API = "API"
    FTP = "FTP"
    EMAIL = "EMAIL"

class DataSourceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    PENDING = "PENDING"

# --- Models ---
class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    subscription_tier = Column(SQLAlchemyEnum(SubscriptionTier), default=SubscriptionTier.STARTER)
    subscription_expires_at = Column(DateTime(timezone=True))
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- Relationships ---
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="tenant", cascade="all, delete-orphan")
    # Added stock management relationships:
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="tenant", cascade="all, delete-orphan")
    warehouses = relationship("Warehouse", back_populates="tenant", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="tenant", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER)
    preferences = Column(JSON, default={})
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="users")
    stock_movements = relationship("StockMovement", back_populates="user")


# --- Stock Management Models ---

class Category(Base):
    __tablename__ = "categories"
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', 'parent_id', name='uq_category_name_parent'),
        {'extend_existing': True}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    level = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    path = Column(LtreeType, index=True)

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")



class Warehouse(Base):
    __tablename__ = "warehouses"

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_warehouse_code'),
        {'extend_existing': True}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="warehouses")
    stock_movements = relationship("StockMovement", back_populates="warehouse")



class Supplier(Base):
    __tablename__ = "suppliers"

    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_supplier_code'),
        {'extend_existing': True}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), index=True) 
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    address = Column(Text)
    lead_time_days = Column(Integer, default=7)
    rating = Column(DECIMAL(3, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="suppliers")
    products = relationship("Product", back_populates="supplier")




class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True) 
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    unit_price = Column(DECIMAL(10, 2))
    cost_price = Column(DECIMAL(10, 2))
    currency = Column(String(3), default='EUR')
    unit_of_measure = Column(String(20))
    reorder_point = Column(Integer)
    reorder_quantity = Column(Integer)
    lead_time_days = Column(Integer)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True, index=True)
    custom_data = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=True, index=True)

    # --- Relationships ---
    tenant = relationship("Tenant")
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")
    data_source = relationship("DataSource", backref="products")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'sku', name='uq_product_sku'),
        Index(
            'ix_products_name_description_tsv', 
            func.to_tsvector(text("'french'"), name + ' ' + description), 
            postgresql_using='gin'
        ),
        {'extend_existing': True}
    )



class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True) 
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True, index=True)
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(10, 2))
    reference_type = Column(String(50))
    reference_id = Column(String(100), index=True) 
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    movement_metadata = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="stock_movements")
    product = relationship("Product", back_populates="stock_movements")
    warehouse = relationship("Warehouse", back_populates="stock_movements")
    user = relationship("User", back_populates="stock_movements")

    __table_args__ = (
        Index('ix_stock_movements_tenant_timestamp_desc', tenant_id, timestamp.desc()),
        Index('ix_stock_movements_product_timestamp_desc', product_id, timestamp.desc()),
        {'extend_existing': True}
    )




# --- DataSource Model (Existing) ---

class DataSource(Base):
    __tablename__ = "data_sources"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SQLAlchemyEnum(DataSourceType), nullable=False)
    connection_config = Column(JSON)
    sync_enabled = Column(Boolean, default=False)
    sync_frequency_minutes = Column(Integer)
    last_sync_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String(50))
    last_sync_error = Column(Text) 
    status = Column(SQLAlchemyEnum(DataSourceStatus), default=DataSourceStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="data_sources")