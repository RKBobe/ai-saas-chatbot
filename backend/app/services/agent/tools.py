import contextvars
from datetime import datetime, timedelta
from app.services.llm.vector_store import VectorStoreService
from app.db.session import SessionLocal
from app.models.inventory import Inventory
from app.models.appointment import Appointment
from sqlalchemy import or_

# ContextVar to handle thread/async isolation of tenant client ID
current_client_id = contextvars.ContextVar("current_client_id", default="default")

async def search_knowledge_base(query: str) -> str:
    """
    Search the business's general knowledge base (business hours, address, services, FAQs, guidelines).
    Use this tool to answer general questions about the organization.
    """
    client_id = current_client_id.get()
    vector_service = VectorStoreService(client_id=client_id)
    try:
        results = await vector_service.search(query, n_results=4)
        documents = results.get('documents', [])
        if documents and documents[0]:
            return "\n---\n".join(documents[0])
        return "No matching records found in the knowledge base."
    except Exception as e:
        return f"Error searching knowledge base: {e}"

def check_inventory(sku_or_name: str) -> str:
    """
    Check stock availability, SKU, description, and price of products/items in the inventory.
    Accepts an item's SKU or name as the search query.
    """
    client_id = current_client_id.get()
    db = SessionLocal()
    try:
        query_pattern = f"%{sku_or_name}%"
        items = db.query(Inventory).filter(
            Inventory.client_id == client_id,
            or_(
                Inventory.sku.ilike(query_pattern),
                Inventory.name.ilike(query_pattern)
            )
        ).all()
        
        if not items:
            return f"No items found matching '{sku_or_name}' in inventory."
            
        result_str = []
        for item in items:
            status = "In Stock" if item.stock_quantity > 0 else "Out of Stock"
            result_str.append(
                f"- SKU: {item.sku}\n"
                f"  Name: {item.name}\n"
                f"  Price: ${item.price:.2f}\n"
                f"  Stock: {item.stock_quantity} units ({status})\n"
                f"  Description: {item.description or 'N/A'}"
            )
        return "\n\n".join(result_str)
    except Exception as e:
        return f"Error checking inventory: {e}"
    finally:
        db.close()

def update_inventory(sku: str, quantity_change: int) -> str:
    """
    Update stock levels for a specific SKU. Use quantity_change as a positive number to add stock,
    or a negative number to subtract stock (e.g. when an item is purchased/allocated).
    """
    client_id = current_client_id.get()
    db = SessionLocal()
    try:
        item = db.query(Inventory).filter(
            Inventory.client_id == client_id,
            Inventory.sku == sku
        ).first()
        
        if not item:
            return f"Error: SKU '{sku}' not found in inventory."
            
        new_quantity = item.stock_quantity + quantity_change
        if new_quantity < 0:
            return f"Error: Cannot reduce stock below 0. Current stock: {item.stock_quantity}."
            
        item.stock_quantity = new_quantity
        db.commit()
        return f"Success: Updated '{item.name}' ({sku}). New stock level: {new_quantity}."
    except Exception as e:
        db.rollback()
        return f"Error updating inventory: {e}"
    finally:
        db.close()

def check_availability(date_str: str) -> str:
    """
    Check booking availability for a specific date (format: YYYY-MM-DD).
    Returns list of free 1-hour appointment slots between 9:00 AM and 5:00 PM.
    """
    client_id = current_client_id.get()
    db = SessionLocal()
    try:
        # Validate date format
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Get all appointments for that day
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        appointments = db.query(Appointment).filter(
            Appointment.client_id == client_id,
            Appointment.start_time >= start_of_day,
            Appointment.start_time <= end_of_day,
            Appointment.status != "cancelled"
        ).all()
        
        # Define business hour slots (9:00 to 17:00)
        booked_hours = [apt.start_time.hour for apt in appointments]
        
        slots = []
        for hour in range(9, 17): # 9 AM to 5 PM
            if hour not in booked_hours:
                time_12hr = f"{hour if hour <= 12 else hour - 12}:00 {'AM' if hour < 12 else 'PM'}"
                slots.append(time_12hr)
                
        if not slots:
            return f"No appointments available on {date_str}. All slots are booked."
            
        return f"Available appointment times for {date_str}:\n" + "\n".join([f"- {slot}" for slot in slots])
    except ValueError:
        return "Error: Date must be in YYYY-MM-DD format."
    except Exception as e:
        return f"Error checking availability: {e}"
    finally:
        db.close()

def book_appointment(customer_name: str, customer_phone: str, date_str: str, time_str: str) -> str:
    """
    Book an appointment.
    Parameters:
      - customer_name: Full name of the customer
      - customer_phone: Contact phone number
      - date_str: Date (format: YYYY-MM-DD)
      - time_str: Time slot in 24hr or 12hr format (e.g. '14:00', '2:00 PM', or '9:00 AM')
    """
    client_id = current_client_id.get()
    db = SessionLocal()
    try:
        # 1. Parse date
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # 2. Parse time (support 14:00, 2:00 PM, 2 PM, etc.)
        time_str_clean = time_str.strip().upper()
        parsed_time = None
        for fmt in ("%H:%M", "%I:%M %p", "%I %p", "%I:%M%p"):
            try:
                parsed_time = datetime.strptime(time_str_clean, fmt).time()
                break
            except ValueError:
                continue
                
        if parsed_time is None:
            return f"Error: Time format '{time_str}' not recognized. Please use HH:MM (24-hour) or H:MM AM/PM."
            
        # 3. Create start/end datetime
        start_dt = datetime.combine(target_date, parsed_time)
        end_dt = start_dt + timedelta(hours=1)
        
        # 4. Check business hours (9 AM to 5 PM)
        if start_dt.hour < 9 or start_dt.hour >= 17:
            return "Error: Appointments must be booked within business hours (9:00 AM - 5:00 PM)."
            
        # 5. Check if slot is already booked
        overlapping = db.query(Appointment).filter(
            Appointment.client_id == client_id,
            Appointment.start_time == start_dt,
            Appointment.status != "cancelled"
        ).first()
        
        if overlapping:
            return f"Error: The time slot {start_dt.strftime('%I:%M %p')} on {date_str} is already booked. Please choose another time."
            
        # 6. Create booking
        booking = Appointment(
            client_id=client_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            start_time=start_dt,
            end_time=end_dt,
            notes=f"Booked via AI Assistant on channel.",
            status="scheduled"
        )
        db.add(booking)
        db.commit()
        
        return (
            f"Success! Appointment successfully booked for {customer_name}.\n"
            f"Date: {date_str}\n"
            f"Time: {start_dt.strftime('%I:%M %p')}\n"
            f"Contact Phone: {customer_phone}"
        )
    except ValueError:
        return "Error: Date must be in YYYY-MM-DD format."
    except Exception as e:
        db.rollback()
        return f"Error booking appointment: {e}"
    finally:
        db.close()
