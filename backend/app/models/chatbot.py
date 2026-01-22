from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from app.db.base import Base

class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # This looks for the 'users' table
    name = Column(String, index=True)
    
    # The "Brain" Configuration
    system_prompt = Column(Text, default="You are a helpful assistant.")
    temperature = Column(Float, default=0.7)
    
    # Facebook Integration
    fb_page_id = Column(String, unique=True, index=True, nullable=True)
    fb_page_access_token = Column(String, nullable=True) 
    is_active = Column(Boolean, default=True)

    # Relationship to the User model
    owner = relationship("User", back_populates="chatbots")