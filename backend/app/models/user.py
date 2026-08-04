from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
# Add this import at the top if you don't have it
from sqlalchemy.orm import relationship

# Inside your User class, add this line:
policies = relationship("Policy", back_populates="owner")
class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User Details
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Authorization Role (e.g., 'admin' or 'employee')
    role = Column(String(50), default="employee")
    
    # Account Status
    is_active = Column(Boolean, default=True)
    policies = relationship("Policy", back_populates="user", cascade="all, delete-orphan")
    # Timestamps (Equivalent to Mongoose { timestamps: true })
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())