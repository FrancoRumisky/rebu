"""
User model - Clientes de la plataforma
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    
    full_name = Column(String, nullable=False)
    profile_image_url = Column(String, nullable=True)

    # Nuevos campos para social login
    auth_provider = Column(String, nullable=False, default="local")  # local | google
    google_sub = Column(String, unique=True, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # FCM token for push notifications
    fcm_token = Column(String, nullable=True)
    
    # Rating
    rating = Column(Float, default=5.0)
    total_trips = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    trip_requests = relationship("TripRequest", back_populates="user", cascade="all, delete-orphan")
    trips_as_user = relationship("Trip", back_populates="user", foreign_keys="Trip.user_id")
    
    def __repr__(self):
        return f"<User {self.id}: {self.email}>"
