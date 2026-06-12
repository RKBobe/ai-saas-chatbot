from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True, default="default")
    sku = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=0)
