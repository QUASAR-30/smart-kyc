from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base

class GenukaOrder(Base):
    __tablename__ = "genuka_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False)
    genuka_order_id = Column(String(100), nullable=False) # ID from Genuka
    
    total = Column(Float, default=0.0)
    status = Column(String(50))
    created_at = Column(DateTime) # Order date from Genuka
    
    customer_id = Column(String(100), nullable=True) # Genuka Customer ID
    items = Column(JSON, nullable=True) # Store items as JSON blob for simplicity
    
    synced_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("Merchant", backref="genuka_orders")

class GenukaCustomer(Base):
    __tablename__ = "genuka_customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False)
    genuka_customer_id = Column(String(100), nullable=False)
    
    name = Column(String(255))
    orders_count = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    synced_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("Merchant", backref="genuka_customers")
