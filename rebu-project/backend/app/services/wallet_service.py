"""
Wallet Service - Manage driver wallet and commissions
"""
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Driver, WalletTransaction, TransactionType, Trip, DriverStatus
from app.repositories.wallet_repository import WalletTransactionRepository
from app.repositories.driver_repository import DriverRepository
from app.core.config import settings


class WalletService:
    """Service for wallet operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.wallet_repo = WalletTransactionRepository(db)
        self.driver_repo = DriverRepository(db)
    
    def charge_trip_commission(self, trip: Trip) -> WalletTransaction:
        """
        Charge commission when trip is completed
        Returns the created transaction
        """
        if trip.commission_charged:
            raise ValueError("Commission already charged for this trip")
        
        driver = trip.driver
        
        # Get commission rate from driver's subscription
        commission_rate = self._get_commission_rate(driver)
        commission_amount = trip.final_fare * commission_rate
        
        # Create negative transaction (debit)
        transaction = self.wallet_repo.create(
            driver_id=driver.id,
            type=TransactionType.TRIP_COMMISSION,
            amount=-commission_amount,
            trip_id=trip.id,
            description=f"Commission for trip #{trip.id}"
        )
        
        # Update driver wallet balance
        driver.wallet_balance -= commission_amount
        
        # Check if driver exceeded credit limit
        if not driver.is_within_credit_limit:
            driver.status = DriverStatus.LIMITED
            print(f"⚠️  Driver {driver.id} exceeded credit limit. Status set to LIMITED")
        
        # Mark commission as charged
        trip.commission_charged = True
        trip.commission_rate = commission_rate
        trip.commission_amount = commission_amount
        
        self.db.commit()
        
        return transaction
    
    def add_payment(
        self,
        driver_id: int,
        amount: float,
        reference: str,
        description: str = None
    ) -> WalletTransaction:
        """
        Add payment from driver (credit to wallet)
        """
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise ValueError("Driver not found")
        
        # Create positive transaction (credit)
        transaction = self.wallet_repo.create(
            driver_id=driver_id,
            type=TransactionType.PAYMENT,
            amount=amount,
            reference=reference,
            description=description or f"Payment: {reference}"
        )
        
        # Update balance
        driver.wallet_balance += amount
        
        # If driver was LIMITED and now within limit, reactivate
        if driver.status == DriverStatus.LIMITED and driver.is_within_credit_limit:
            driver.status = DriverStatus.ACTIVE
            print(f"✅ Driver {driver_id} reactivated after payment")
        
        self.db.commit()
        
        return transaction
    
    def add_bonus(
        self,
        driver_id: int,
        amount: float,
        description: str
    ) -> WalletTransaction:
        """Add bonus to driver wallet"""
        if amount <= 0:
            raise ValueError("Bonus amount must be positive")
        
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise ValueError("Driver not found")
        
        transaction = self.wallet_repo.create(
            driver_id=driver_id,
            type=TransactionType.BONUS,
            amount=amount,
            description=description
        )
        
        driver.wallet_balance += amount
        self.db.commit()
        
        return transaction
    
    def add_penalty(
        self,
        driver_id: int,
        amount: float,
        description: str
    ) -> WalletTransaction:
        """Add penalty to driver wallet"""
        if amount <= 0:
            raise ValueError("Penalty amount must be positive")
        
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise ValueError("Driver not found")
        
        transaction = self.wallet_repo.create(
            driver_id=driver_id,
            type=TransactionType.PENALTY,
            amount=-amount,  # Negative
            description=description
        )
        
        driver.wallet_balance -= amount
        
        # Check credit limit
        if not driver.is_within_credit_limit:
            driver.status = DriverStatus.LIMITED
        
        self.db.commit()
        
        return transaction
    
    def get_wallet_balance(self, driver_id: int) -> float:
        """Get current wallet balance"""
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise ValueError("Driver not found")
        return driver.wallet_balance
    
    def get_transaction_history(
        self,
        driver_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[WalletTransaction]:
        """Get transaction history for driver"""
        return self.wallet_repo.get_by_driver_id(
            driver_id,
            limit=limit,
            offset=offset
        )
    
    def _get_commission_rate(self, driver: Driver) -> float:
        """Get commission rate based on driver's subscription"""
        if not driver.current_subscription:
            return settings.COMMISSION_FREE
        
        subscription = driver.current_subscription
        
        if not subscription.is_active:
            return settings.COMMISSION_FREE
        
        tier = subscription.tier
        
        if tier == "PREMIUM":
            return settings.COMMISSION_PREMIUM
        elif tier == "PRO":
            return settings.COMMISSION_PRO
        else:
            return settings.COMMISSION_FREE
