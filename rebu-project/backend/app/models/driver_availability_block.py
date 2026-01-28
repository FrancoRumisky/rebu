"""
DriverAvailabilityBlock model - Bloques de disponibilidad para evitar doble reserva
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DriverAvailabilityBlock(Base):
    """
    Represents a time block when a driver is unavailable.
    Used to prevent double-booking of scheduled trips.
    """
    __tablename__ = "driver_availability_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    trip_request_id = Column(Integer, ForeignKey("trip_requests.id"), nullable=True, index=True)
    
    # Time block
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Reason (optional)
    reason = Column(String, nullable=True)  # e.g., "SCHEDULED_TRIP", "PERSONAL", "MAINTENANCE"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    driver = relationship("Driver", back_populates="availability_blocks")
    
    def __repr__(self):
        return f"<DriverAvailabilityBlock {self.id}: Driver {self.driver_id} - {self.start_time} to {self.end_time}>"
    
    @property
    def is_active(self) -> bool:
        """Check if block is currently active"""
        from datetime import datetime
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time
    
    def overlaps_with(self, start_time, end_time) -> bool:
        """Check if this block overlaps with given time range"""
        return not (end_time <= self.start_time or start_time >= self.end_time)
