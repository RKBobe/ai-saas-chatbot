from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, index=True) # e.g. "voice", "sms", "web", "facebook"
    session_id = Column(String, index=True) # phone number or user browser uuid
    messages = Column(Text, default="[]") # JSON list of messages representing conversation history
