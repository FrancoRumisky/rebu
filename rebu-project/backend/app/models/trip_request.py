"""
TripRequest model - Solicitudes de viaje (inmediato o programado)
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TripMode(str, enum.Enum):
    ON_DEMAND = "ON_DEMAND"    # Immediate trip
    SCHEDULED = "SCHEDULED"    # Scheduled trip


class TripRequestStatus(str, enum.Enum):
    PENDING = "PENDING"        # Looking for driver
    MATCHED = "MATCHED"        # Driver accepted, trip created
    EXPIRED = "EXPIRED"        # No driver accepted in time
    CANCELLED = "CANCELLED"    # User cancelled


class TripRequest(Base):
    __tablename__ = "trip_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Trip mode
    mode = Column(SQLEnum(TripMode), nullable=False, index=True)
    
    # Pickup location
    pickup_address = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    
    # Dropoff location
    dropoff_address = Column(String, nullable=False)
    dropoff_lat = Column(Float, nullable=False)
    dropoff_lon = Column(Float, nullable=False)
    
    # Estimated distance and duration (from Google Maps API)
    estimated_distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Estimated fare
    estimated_fare = Column(Float, nullable=False)
    
    # Vehicle requirements
    required_vehicle_type = Column(String, nullable=True)  # JSON array or specific type
    
    # Cargo details
    cargo_description = Column(Text, nullable=True)
    cargo_weight_kg = Column(Float, nullable=True)
    cargo_images_urls = Column(Text, nullable=True)  # JSON array of URLs
    
    # Scheduled trip fields (only for SCHEDULED mode)
    scheduled_start_at = Column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_end_at = Column(DateTime(timezone=True), nullable=True)
    
    # Pre-assigned driver for scheduled trips
    pre_assigned_driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, index=True)
    
    # Reminders sent (for scheduled trips)
    reminder_60min_sent = Column(Boolean, default=False)
    reminder_15min_sent = Column(Boolean, default=False)
    
    # Status
    status = Column(SQLEnum(TripRequestStatus), default=TripRequestStatus.PENDING, index=True)
    
    # Expiry
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    matched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trip_requests")
    pre_assigned_driver = relationship("Driver", foreign_keys=[pre_assigned_driver_id])
    trip_offers = relationship("TripOffer", back_populates="trip_request", cascade="all, delete-orphan")
    trip = relationship("Trip", back_populates="trip_request", uselist=False)
    
    def __repr__(self):
        return f"<TripRequest {self.id}: {self.mode.value} - {self.status.value}>"
    
    @property
    def is_scheduled(self) -> bool:
        return self.mode == TripMode.SCHEDULED
    
    @property
    def is_on_demand(self) -> bool:
        return self.mode == TripMode.ON_DEMAND
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
