"""
Subscription model - Planes de suscripción para conductores
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    PREMIUM = "PREMIUM"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    
    # Subscription details
    tier = Column(SQLEnum(SubscriptionTier), nullable=False, index=True)
    
    # Pricing
    monthly_price = Column(Float, nullable=False)  # 0 for FREE
    commission_rate = Column(Float, nullable=False)  # e.g., 0.15 for 15%
    
    # Status
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, index=True)
    
    # Validity period
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL for FREE (never expires)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=False)
    
    # Payment info
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    next_payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Subscription {self.id}: Driver {self.driver_id} - {self.tier.value} - {self.status.value}>"
    
    @property
    def is_active(self) -> bool:
        from datetime import datetime
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
