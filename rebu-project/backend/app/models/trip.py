"""
Trip model - Viajes activos y completados
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TripStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"          # Driver confirmed, waiting to start
    DRIVER_ARRIVING = "DRIVER_ARRIVING"  # Driver on the way to pickup
    ARRIVED = "ARRIVED"              # Driver arrived at pickup
    IN_PROGRESS = "IN_PROGRESS"      # Trip in progress (cargo loaded)
    COMPLETED = "COMPLETED"          # Trip completed
    CANCELLED = "CANCELLED"          # Trip cancelled


class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_request_id = Column(Integer, ForeignKey("trip_requests.id"), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    
    # Locations (same as trip_request, but denormalized for quick access)
    pickup_address = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    
    dropoff_address = Column(String, nullable=False)
    dropoff_lat = Column(Float, nullable=False)
    dropoff_lon = Column(Float, nullable=False)
    
    # Actual trip data
    actual_distance_km = Column(Float, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    
    # Fare
    estimated_fare = Column(Float, nullable=False)
    final_fare = Column(Float, nullable=True)  # May differ from estimate
    
    # Payment
    payment_method = Column(String, default="CASH")  # CASH, TRANSFER, etc.
    is_paid = Column(Boolean, default=False)
    
    # Commission
    commission_rate = Column(Float, nullable=False)  # e.g., 0.15 for 15%
    commission_amount = Column(Float, nullable=True)
    commission_charged = Column(Boolean, default=False)
    
    # Status
    status = Column(SQLEnum(TripStatus), default=TripStatus.CONFIRMED, index=True)
    
    # Ratings and feedback
    user_rating = Column(Float, nullable=True)  # User rates driver
    driver_rating = Column(Float, nullable=True)  # Driver rates user
    user_feedback = Column(Text, nullable=True)
    driver_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    arrived_at_pickup_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Cancellation info
    cancelled_by = Column(String, nullable=True)  # USER, DRIVER, SYSTEM
    cancellation_reason = Column(Text, nullable=True)
    
    # Relationships
    trip_request = relationship("TripRequest", back_populates="trip")
    user = relationship("User", back_populates="trips_as_user", foreign_keys=[user_id])
    driver = relationship("Driver", back_populates="trips_as_driver", foreign_keys=[driver_id])
    vehicle = relationship("Vehicle", back_populates="trips")
    
    def __repr__(self):
        return f"<Trip {self.id}: User {self.user_id} - Driver {self.driver_id} - {self.status.value}>"
    
    @property
    def is_active(self) -> bool:
        return self.status in [
            TripStatus.CONFIRMED,
            TripStatus.DRIVER_ARRIVING,
            TripStatus.ARRIVED,
            TripStatus.IN_PROGRESS
        ]
    
    @property
    def is_finished(self) -> bool:
        return self.status in [TripStatus.COMPLETED, TripStatus.CANCELLED]
