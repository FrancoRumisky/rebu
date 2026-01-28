"""
Matching Service - Handles driver-trip matching logic
"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis_client import redis_client
from app.models import TripRequest, Driver, TripOffer, DriverStatus
from app.repositories.driver_repository import DriverRepository
from app.repositories.trip_offer_repository import TripOfferRepository
from app.services.notification_service import NotificationService


class MatchingService:
    """Service for matching drivers with trip requests"""
    
    def __init__(self, db: Session):
        self.db = db
        self.driver_repo = DriverRepository(db)
        self.offer_repo = TripOfferRepository(db)
        self.notification_service = NotificationService()
    
    async def find_drivers_for_on_demand_trip(
        self,
        trip_request: TripRequest,
        wave_number: int = 1
    ) -> list[Driver]:
        """
        Find nearby online drivers for ON_DEMAND trip
        Uses wave-based matching: Wave 1 = 3km, Wave 2 = 5km, Wave 3 = 10km
        """
        # Determine radius based on wave
        radius_map = {
            1: settings.MATCHING_WAVE_1_RADIUS_KM,
            2: settings.MATCHING_WAVE_2_RADIUS_KM,
            3: settings.MATCHING_WAVE_3_RADIUS_KM,
        }
        radius_km = radius_map.get(wave_number, settings.MATCHING_RADIUS_KM)
        
        # Get nearby drivers from Redis
        nearby = redis_client.get_nearby_drivers(
            trip_request.pickup_lat,
            trip_request.pickup_lon,
            radius_km,
            count=10  # Limit to 10 drivers per wave
        )
        
        if not nearby:
            return []
        
        # Get driver IDs that already have pending offers
        pending_offer_driver_ids = redis_client.get_pending_offers(trip_request.id)
        
        # Fetch driver details from DB and filter
        driver_ids = [n["driver_id"] for n in nearby]
        drivers = self.driver_repo.get_by_ids(driver_ids)
        
        # Filter: must be ACTIVE, not already sent offer, within credit limit
        available_drivers = []
        for driver in drivers:
            if (
                driver.status == DriverStatus.ACTIVE
                and driver.id not in pending_offer_driver_ids
                and driver.is_within_credit_limit
            ):
                available_drivers.append(driver)
        
        return available_drivers
    
    async def send_offers_to_drivers(
        self,
        trip_request: TripRequest,
        drivers: list[Driver]
    ) -> list[TripOffer]:
        """
        Send trip offers to drivers
        Creates TripOffer records and sends FCM notifications
        """
        if not drivers:
            return []
        
        offers = []
        expires_at = datetime.utcnow() + timedelta(seconds=settings.OFFER_EXPIRY_SECONDS)
        
        for driver in drivers:
            # Create offer
            offer = self.offer_repo.create(
                trip_request_id=trip_request.id,
                driver_id=driver.id,
                offered_fare=trip_request.estimated_fare,
                expires_at=expires_at
            )
            offers.append(offer)
            
            # Track in Redis
            redis_client.add_pending_offer(
                trip_request.id,
                driver.id,
                settings.OFFER_EXPIRY_SECONDS
            )
            
            # Send FCM notification
            if driver.fcm_token:
                await self.notification_service.send_trip_offer_notification(
                    driver.fcm_token,
                    trip_request,
                    offer
                )
        
        return offers
    
    async def accept_offer(
        self,
        offer_id: int,
        driver_id: int
    ) -> Optional[TripOffer]:
        """
        Driver accepts an offer
        Uses Redis lock to prevent double acceptance
        """
        offer = self.offer_repo.get_by_id(offer_id)
        
        if not offer or offer.driver_id != driver_id:
            return None
        
        if offer.is_expired:
            return None
        
        # Try to acquire lock
        lock_acquired = redis_client.acquire_trip_lock(
            offer.trip_request_id,
            timeout_seconds=10
        )
        
        if not lock_acquired:
            # Another driver already accepted
            return None
        
        try:
            # Update offer status
            offer = self.offer_repo.update_status(offer.id, "ACCEPTED")
            
            # Update trip request status
            trip_request = offer.trip_request
            trip_request.status = "MATCHED"
            trip_request.matched_at = datetime.utcnow()
            self.db.commit()
            
            # Clear pending offers from Redis
            redis_client.clear_pending_offers(offer.trip_request_id)
            
            return offer
        
        except Exception as e:
            redis_client.release_trip_lock(offer.trip_request_id)
            raise e
    
    async def find_available_drivers_for_scheduled_trip(
        self,
        trip_request: TripRequest,
        radius_km: float = 50.0
    ) -> list[Driver]:
        """
        Find drivers available for scheduled trip
        Checks driver_availability_blocks to avoid conflicts
        """
        from app.repositories.driver_availability_repository import DriverAvailabilityRepository
        
        availability_repo = DriverAvailabilityRepository(self.db)
        
        # Get all active drivers
        all_drivers = self.driver_repo.get_active_drivers()
        
        available_drivers = []
        for driver in all_drivers:
            # Check if driver has conflicting availability blocks
            has_conflict = availability_repo.has_conflict(
                driver.id,
                trip_request.scheduled_start_at,
                trip_request.scheduled_end_at
            )
            
            if not has_conflict and driver.is_within_credit_limit:
                available_drivers.append(driver)
        
        return available_drivers
    
    async def pre_assign_driver_to_scheduled_trip(
        self,
        trip_request: TripRequest,
        driver_id: int
    ) -> bool:
        """
        Pre-assign a driver to a scheduled trip
        Creates availability block to prevent conflicts
        """
        from app.repositories.driver_availability_repository import DriverAvailabilityRepository
        
        driver = self.driver_repo.get_by_id(driver_id)
        if not driver or not driver.is_online:
            return False
        
        availability_repo = DriverAvailabilityRepository(self.db)
        
        # Check for conflicts
        has_conflict = availability_repo.has_conflict(
            driver_id,
            trip_request.scheduled_start_at,
            trip_request.scheduled_end_at
        )
        
        if has_conflict:
            return False
        
        # Create availability block
        availability_repo.create(
            driver_id=driver_id,
            trip_request_id=trip_request.id,
            start_time=trip_request.scheduled_start_at,
            end_time=trip_request.scheduled_end_at,
            reason="SCHEDULED_TRIP"
        )
        
        # Update trip request
        trip_request.pre_assigned_driver_id = driver_id
        self.db.commit()
        
        # Send notification
        if driver.fcm_token:
            await self.notification_service.send_scheduled_trip_assignment(
                driver.fcm_token,
                trip_request
            )
        
        return True
