"""
Additional API Routers - Users, Drivers, Admin
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_user, require_driver, require_admin

# ========== USERS ROUTER ==========
users = APIRouter()

@users.get("/me")
async def get_current_user_profile(
    current_user = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    return current_user["entity"]


@users.get("/trips")
async def get_user_trips(
    current_user = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get user's trip history"""
    from app.repositories import TripRequestRepository
    
    trip_request_repo = TripRequestRepository(db)
    trips = trip_request_repo.get_by_user_id(current_user["id"])
    
    return {"trips": trips}


# ========== DRIVERS ROUTER ==========
drivers = APIRouter()

@drivers.get("/me")
async def get_current_driver_profile(
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Get current driver profile"""
    return current_user["entity"]


@drivers.post("/location")
async def update_driver_location(
    lat: float,
    lon: float,
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Update driver's current location"""
    from app.core.redis_client import redis_client
    from datetime import datetime
    
    driver_id = current_user["id"]
    driver = current_user["entity"]
    
    # Update in Redis for real-time queries
    redis_client.add_driver_location(driver_id, lat, lon)
    redis_client.set_driver_status(driver_id, driver.status.value)
    
    # Update in DB (backup)
    driver.last_known_lat = lat
    driver.last_known_lon = lon
    driver.last_location_update = datetime.utcnow()
    db.commit()
    
    return {"message": "Location updated"}


@drivers.get("/wallet")
async def get_wallet_info(
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Get driver wallet balance and transactions"""
    from app.services.wallet_service import WalletService
    
    driver_id = current_user["id"]
    driver = current_user["entity"]
    wallet_service = WalletService(db)
    
    transactions = wallet_service.get_transaction_history(driver_id, limit=50)
    
    return {
        "balance": driver.wallet_balance,
        "credit_limit": driver.credit_limit,
        "is_within_limit": driver.is_within_credit_limit,
        "transactions": transactions
    }


# ========== ADMIN ROUTER ==========
admin = APIRouter()

@admin.get("/dashboard")
async def get_dashboard_stats(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    from app.models import User, Driver, Trip, TripStatus
    
    total_users = db.query(User).count()
    total_drivers = db.query(Driver).count()
    total_trips = db.query(Trip).count()
    completed_trips = db.query(Trip).filter(
        Trip.status == TripStatus.COMPLETED
    ).count()
    
    return {
        "total_users": total_users,
        "total_drivers": total_drivers,
        "total_trips": total_trips,
        "completed_trips": completed_trips
    }


@admin.post("/drivers/{driver_id}/approve")
async def approve_driver(
    driver_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approve pending driver"""
    from app.repositories import DriverRepository
    from app.models import DriverStatus
    
    driver_repo = DriverRepository(db)
    driver = driver_repo.get_by_id(driver_id)
    
    if not driver:
        return {"error": "Driver not found"}
    
    driver.status = DriverStatus.ACTIVE
    driver.is_verified = True
    db.commit()
    
    return {"message": f"Driver {driver_id} approved"}


@admin.post("/wallet/payment")
async def register_driver_payment(
    driver_id: int,
    amount: float,
    reference: str,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Register a payment from driver to platform"""
    from app.services.wallet_service import WalletService
    
    wallet_service = WalletService(db)
    
    try:
        transaction = wallet_service.add_payment(
            driver_id=driver_id,
            amount=amount,
            reference=reference,
            description=f"Payment registered by admin"
        )
        
        return {
            "message": "Payment registered",
            "transaction_id": transaction.id,
            "new_balance": transaction.balance_after
        }
    except ValueError as e:
        return {"error": str(e)}


# Export routers
__all__ = ['users', 'drivers', 'admin']

# Create router alias for imports
router = users  # For users.py
