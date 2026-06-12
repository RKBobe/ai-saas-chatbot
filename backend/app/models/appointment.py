from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True, default="default")
    customer_name = Column(String, index=True, nullable=False)
    customer_phone = Column(String, index=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    notes = Column(String, nullable=True)
    status = Column(String, default="scheduled") # scheduled, cancelled, completed
