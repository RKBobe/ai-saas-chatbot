from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import SessionLocal
from app.models.appointment import Appointment

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class AppointmentBase(BaseModel):
    customer_name: str
    customer_phone: str
    start_time: datetime
    notes: Optional[str] = None
    status: str = "scheduled"

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    id: int
    client_id: str
    end_time: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(
    client_id: str = "default",
    date_filter: Optional[str] = Query(None, alias="date"), # format: YYYY-MM-DD
    db: Session = Depends(get_db)
):
    db_query = db.query(Appointment).filter(Appointment.client_id == client_id)
    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            db_query = db_query.filter(
                Appointment.start_time >= start_of_day,
                Appointment.start_time <= end_of_day
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD")
            
    return db_query.order_by(Appointment.start_time.asc()).all()

@router.post("/", response_model=AppointmentResponse)
def create_appointment(
    apt: AppointmentCreate,
    client_id: str = "default",
    db: Session = Depends(get_db)
):
    # End time is 1 hour after start
    end_time = apt.start_time + timedelta(hours=1)
    
    # Check for overlapping bookings
    overlapping = db.query(Appointment).filter(
        Appointment.client_id == client_id,
        Appointment.start_time == apt.start_time,
        Appointment.status != "cancelled"
    ).first()
    
    if overlapping:
        raise HTTPException(
            status_code=400, 
            detail=f"Time slot {apt.start_time.strftime('%I:%M %p')} is already booked."
        )
        
    db_apt = Appointment(
        client_id=client_id,
        customer_name=apt.customer_name,
        customer_phone=apt.customer_phone,
        start_time=apt.start_time,
        end_time=end_time,
        notes=apt.notes,
        status=apt.status
    )
    db.add(db_apt)
    db.commit()
    db.refresh(db_apt)
    return db_apt

@router.delete("/{apt_id}")
def cancel_appointment(
    apt_id: int,
    client_id: str = "default",
    db: Session = Depends(get_db)
):
    db_apt = db.query(Appointment).filter(
        Appointment.id == apt_id,
        Appointment.client_id == client_id
    ).first()
    if not db_apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # We can perform soft delete by marking as cancelled
    db_apt.status = "cancelled"
    db.commit()
    return {"status": "success", "message": f"Appointment {apt_id} cancelled."}

from datetime import timedelta
