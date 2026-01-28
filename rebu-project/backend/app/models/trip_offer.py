"""
TripOffer model - Ofertas enviadas a conductores
"""
from sqlalchemy import Column, Integer, DateTime, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"      # Waiting for driver response
    ACCEPTED = "ACCEPTED"    # Driver accepted
    REJECTED = "REJECTED"    # Driver rejected
    EXPIRED = "EXPIRED"      # Offer expired


class TripOffer(Base):
    __tablename__ = "trip_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_request_id = Column(Integer, ForeignKey("trip_requests.id"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    
    # Offer details
    offered_fare = Column(Float, nullable=False)
    estimated_arrival_minutes = Column(Integer, nullable=True)  # Time to reach pickup
    
    # Status
    status = Column(SQLEnum(OfferStatus), default=OfferStatus.PENDING, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    trip_request = relationship("TripRequest", back_populates="trip_offers")
    driver = relationship("Driver", back_populates="trip_offers")
    
    def __repr__(self):
        return f"<TripOffer {self.id}: Driver {self.driver_id} for TripRequest {self.trip_request_id} - {self.status.value}>"
    
    @property
    def is_expired(self) -> bool:
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
