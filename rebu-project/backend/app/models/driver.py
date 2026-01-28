"""
Driver model - Conductores con wallet virtual y suscripción
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class DriverStatus(str, enum.Enum):
    PENDING = "PENDING"  # Pending approval
    ACTIVE = "ACTIVE"    # Active and can accept trips
    OFFLINE = "OFFLINE"  # Not accepting trips
    BUSY = "BUSY"        # On a trip
    LIMITED = "LIMITED"  # Limited due to negative wallet balance
    SUSPENDED = "SUSPENDED"  # Suspended by admin
    BLOCKED = "BLOCKED"  # Blocked permanently


class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    full_name = Column(String, nullable=False)
    profile_image_url = Column(String, nullable=True)
    
    # License info
    license_number = Column(String, unique=True, nullable=False)
    license_expiry_date = Column(DateTime, nullable=False)
    license_image_url = Column(String, nullable=True)
    
    # Status
    status = Column(SQLEnum(DriverStatus), default=DriverStatus.PENDING, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Current subscription
    current_subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    # Wallet balance (can be negative up to credit limit)
    wallet_balance = Column(Float, default=0.0, nullable=False)
    
    # Location (cached from Redis, for backup)
    last_known_lat = Column(Float, nullable=True)
    last_known_lon = Column(Float, nullable=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    
    # FCM token
    fcm_token = Column(String, nullable=True)
    
    # Rating
    rating = Column(Float, default=5.0)
    total_trips = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    current_subscription = relationship("Subscription", foreign_keys=[current_subscription_id])
    vehicles = relationship("Vehicle", back_populates="driver", cascade="all, delete-orphan")
    trip_offers = relationship("TripOffer", back_populates="driver", cascade="all, delete-orphan")
    trips_as_driver = relationship("Trip", back_populates="driver", foreign_keys="Trip.driver_id")
    wallet_transactions = relationship("WalletTransaction", back_populates="driver", cascade="all, delete-orphan")
    availability_blocks = relationship("DriverAvailabilityBlock", back_populates="driver", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Driver {self.id}: {self.email} ({self.status.value})>"
    
    @property
    def is_online(self) -> bool:
        """Check if driver is online and available"""
        return self.status == DriverStatus.ACTIVE
    
    @property
    def credit_limit(self) -> float:
        """Get credit limit based on subscription"""
        from app.core.config import settings
        
        if not self.current_subscription:
            return settings.WALLET_CREDIT_LIMIT_FREE
        
        if self.current_subscription.tier == "PRO":
            return settings.WALLET_CREDIT_LIMIT_PRO
        elif self.current_subscription.tier == "PREMIUM":
            return settings.WALLET_CREDIT_LIMIT_PREMIUM
        
        return settings.WALLET_CREDIT_LIMIT_FREE
    
    @property
    def is_within_credit_limit(self) -> bool:
        """Check if wallet balance is within credit limit"""
        return self.wallet_balance >= -self.credit_limit
