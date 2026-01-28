"""
WalletTransaction model - Transacciones de wallet del conductor
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TransactionType(str, enum.Enum):
    TRIP_COMMISSION = "TRIP_COMMISSION"  # Commission charged for completed trip (negative)
    PAYMENT = "PAYMENT"                  # Driver payment to platform (positive)
    REFUND = "REFUND"                    # Refund to driver (positive)
    ADJUSTMENT = "ADJUSTMENT"            # Manual adjustment by admin
    BONUS = "BONUS"                      # Bonus or incentive (positive)
    PENALTY = "PENALTY"                  # Penalty (negative)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    
    # Transaction details
    type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Positive = credit, Negative = debit
    
    # Balance after transaction
    balance_after = Column(Float, nullable=False)
    
    # Related trip (if applicable)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True, index=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Reference (e.g., payment reference, admin ID)
    reference = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    driver = relationship("Driver", back_populates="wallet_transactions")
    
    def __repr__(self):
        return f"<WalletTransaction {self.id}: Driver {self.driver_id} - {self.type.value} - {self.amount}>"
