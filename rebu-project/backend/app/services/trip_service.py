"""
Trip Service - Business logic for trip management
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.models import TripRequest, Trip, TripMode, TripStatus
from app.repositories import (
    TripRequestRepository, TripRepository, DriverRepository,
    VehicleRepository, WalletTransactionRepository
)
from app.services.wallet_service import WalletService
from app.services.notification_service import NotificationService


class TripService:
    """Service for trip operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.trip_request_repo = TripRequestRepository(db)
        self.trip_repo = TripRepository(db)
        self.driver_repo = DriverRepository(db)
        self.wallet_service = WalletService(db)
        self.notification_service = NotificationService()
    
    def create_on_demand_trip(
        self,
        user_id: int,
        pickup: dict,
        dropoff: dict,
        estimated_fare: float,
        **kwargs
    ) -> TripRequest:
        """Create an ON_DEMAND trip request"""
        
        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.TRIP_REQUEST_EXPIRY_MINUTES
        )
        
        trip_request = self.trip_request_repo.create(
            user_id=user_id,
            mode=TripMode.ON_DEMAND,
            pickup_data=pickup,
            dropoff_data=dropoff,
            estimated_fare=estimated_fare,
            expires_at=expires_at,
            **kwargs
        )
        
        return trip_request
    
    def create_scheduled_trip(
        self,
        user_id: int,
        pickup: dict,
        dropoff: dict,
        estimated_fare: float,
        scheduled_start_at: datetime,
        scheduled_end_at: datetime,
        **kwargs
    ) -> TripRequest:
        """Create a SCHEDULED trip request"""
        
        trip_request = self.trip_request_repo.create(
            user_id=user_id,
            mode=TripMode.SCHEDULED,
            pickup_data=pickup,
            dropoff_data=dropoff,
            estimated_fare=estimated_fare,
            scheduled_start_at=scheduled_start_at,
            scheduled_end_at=scheduled_end_at,
            **kwargs
        )
        
        return trip_request
    
    def get_trip_request(self, trip_request_id: int) -> Optional[TripRequest]:
        """Get trip request by ID"""
        return self.trip_request_repo.get_by_id(trip_request_id)
    
    def create_trip_from_request(
        self,
        trip_request_id: int,
        driver_id: int
    ) -> Trip:
        """
        Create Trip from accepted TripRequest
        Determines commission rate based on driver's subscription
        """
        trip_request = self.trip_request_repo.get_by_id(trip_request_id)
        if not trip_request:
            raise ValueError("Trip request not found")
        
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver:
            raise ValueError("Driver not found")
        
        # Get driver's active vehicle
        # TODO: Implement VehicleRepository
        vehicle_id = 1  # Placeholder
        
        # Determine commission rate
        commission_rate = self._get_commission_rate(driver)
        
        # Create trip
        trip = self.trip_repo.create(
            trip_request=trip_request,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            commission_rate=commission_rate
        )
        
        # Update driver status
        driver.status = "BUSY"
        self.db.commit()
        
        # Send notification to user
        user = trip_request.user
        if user.fcm_token:
            self.notification_service.send_trip_status_update(
                user.fcm_token,
                trip,
                "MATCHED"
            )
        
        return trip
    
    def start_trip(self, trip_id: int, driver_id: int) -> Trip:
        """Driver starts trip (cargo loaded)"""
        trip = self.trip_repo.get_by_id(trip_id)
        
        if not trip or trip.driver_id != driver_id:
            raise ValueError("Trip not found or unauthorized")
        
        if trip.status != TripStatus.ARRIVED:
            raise ValueError("Trip must be in ARRIVED status to start")
        
        trip.status = TripStatus.IN_PROGRESS
        trip.picked_up_at = datetime.utcnow()
        self.db.commit()
        
        # Notify user
        if trip.user.fcm_token:
            self.notification_service.send_trip_status_update(
                trip.user.fcm_token,
                trip,
                "IN_PROGRESS"
            )
        
        return trip
    
    def complete_trip(
        self,
        trip_id: int,
        driver_id: int,
        final_fare: float
    ) -> Trip:
        """
        Complete trip and charge commission
        """
        trip = self.trip_repo.get_by_id(trip_id)
        
        if not trip or trip.driver_id != driver_id:
            raise ValueError("Trip not found or unauthorized")
        
        if trip.status != TripStatus.IN_PROGRESS:
            raise ValueError("Trip must be in progress to complete")
        
        # Update trip
        trip.status = TripStatus.COMPLETED
        trip.final_fare = final_fare
        trip.completed_at = datetime.utcnow()
        
        # Charge commission
        self.wallet_service.charge_trip_commission(trip)
        
        # Update driver status back to ACTIVE
        trip.driver.status = "ACTIVE"
        
        self.db.commit()
        
        # Notify user
        if trip.user.fcm_token:
            self.notification_service.send_trip_status_update(
                trip.user.fcm_token,
                trip,
                "COMPLETED"
            )
        
        return trip
    
    def get_trip(self, trip_id: int) -> Optional[Trip]:
        """Get trip by ID"""
        return self.trip_repo.get_by_id(trip_id)
    
    def _get_commission_rate(self, driver) -> float:
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


class VehicleRepository:
    """Placeholder - implement as needed"""
    def __init__(self, db: Session):
        self.db = db
