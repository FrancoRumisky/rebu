"""
Trips Router - Endpoints for trip management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import require_user, require_driver, get_current_user
from app.schemas.trip_request import (
    CreateOnDemandTripRequest,
    CreateScheduledTripRequest,
    TripRequestResponse
)
from app.services.trip_service import TripService
from app.services.matching_service import MatchingService


router = APIRouter()


@router.post("/request/on-demand", response_model=TripRequestResponse)
async def create_on_demand_trip(
    request: CreateOnDemandTripRequest,
    current_user = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Create an ON_DEMAND trip request
    Immediately starts searching for nearby drivers
    """
    trip_service = TripService(db)
    matching_service = MatchingService(db)
    
    # Create trip request
    trip_request = trip_service.create_on_demand_trip(
        user_id=current_user["id"],
        pickup=request.pickup.dict(),
        dropoff=request.dropoff.dict(),
        estimated_fare=request.estimated_fare,
        cargo_description=request.cargo_description,
        cargo_weight_kg=request.cargo_weight_kg
    )
    
    # Start matching process (Wave 1)
    drivers = await matching_service.find_drivers_for_on_demand_trip(trip_request, wave_number=1)
    
    if drivers:
        await matching_service.send_offers_to_drivers(trip_request, drivers)
    
    return trip_request


@router.post("/request/scheduled", response_model=TripRequestResponse)
async def create_scheduled_trip(
    request: CreateScheduledTripRequest,
    current_user = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Create a SCHEDULED trip request
    Allows pre-assignment of driver
    """
    trip_service = TripService(db)
    
    trip_request = trip_service.create_scheduled_trip(
        user_id=current_user["id"],
        pickup=request.pickup.dict(),
        dropoff=request.dropoff.dict(),
        estimated_fare=request.estimated_fare,
        scheduled_start_at=request.scheduled_start_at,
        scheduled_end_at=request.scheduled_end_at,
        cargo_description=request.cargo_description,
        cargo_weight_kg=request.cargo_weight_kg
    )
    
    return trip_request


@router.get("/request/{trip_request_id}", response_model=TripRequestResponse)
async def get_trip_request(
    trip_request_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trip request details"""
    trip_service = TripService(db)
    
    trip_request = trip_service.get_trip_request(trip_request_id)
    
    if not trip_request:
        raise HTTPException(status_code=404, detail="Trip request not found")
    
    # Check authorization
    role = current_user["role"]
    user_id = current_user["id"]
    
    if role == "USER" and trip_request.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if role == "DRIVER":
        # Driver can view if they have an offer or are pre-assigned
        from app.repositories.trip_offer_repository import TripOfferRepository
        offer_repo = TripOfferRepository(db)
        
        has_offer = offer_repo.has_offer_for_driver(trip_request_id, user_id)
        is_pre_assigned = trip_request.pre_assigned_driver_id == user_id
        
        if not has_offer and not is_pre_assigned:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return trip_request


@router.post("/offer/{offer_id}/accept")
async def accept_offer(
    offer_id: int,
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """
    Driver accepts a trip offer
    Uses distributed lock to prevent double acceptance
    """
    matching_service = MatchingService(db)
    trip_service = TripService(db)
    
    driver_id = current_user["id"]
    
    # Accept offer
    offer = await matching_service.accept_offer(offer_id, driver_id)
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer not available (expired or already accepted by another driver)"
        )
    
    # Create trip
    trip = trip_service.create_trip_from_request(
        trip_request_id=offer.trip_request_id,
        driver_id=driver_id
    )
    
    return {
        "message": "Offer accepted successfully",
        "trip_id": trip.id,
        "trip_request_id": trip.trip_request_id
    }


@router.post("/offer/{offer_id}/reject")
async def reject_offer(
    offer_id: int,
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Driver rejects a trip offer"""
    from app.repositories.trip_offer_repository import TripOfferRepository
    
    offer_repo = TripOfferRepository(db)
    driver_id = current_user["id"]
    
    offer = offer_repo.get_by_id(offer_id)
    
    if not offer or offer.driver_id != driver_id:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    if offer.is_expired:
        raise HTTPException(status_code=400, detail="Offer already expired")
    
    offer_repo.update_status(offer_id, "REJECTED")
    
    return {"message": "Offer rejected"}


@router.get("/my-requests")
async def get_my_trip_requests(
    status: Optional[str] = None,
    current_user = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get user's trip requests"""
    from app.repositories.trip_request_repository import TripRequestRepository
    
    trip_request_repo = TripRequestRepository(db)
    user_id = current_user["id"]
    
    trip_requests = trip_request_repo.get_by_user_id(user_id, status=status)
    
    return {"total": len(trip_requests), "items": trip_requests}


@router.get("/my-offers")
async def get_my_offers(
    status: Optional[str] = None,
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Get driver's trip offers"""
    from app.repositories.trip_offer_repository import TripOfferRepository
    
    offer_repo = TripOfferRepository(db)
    driver_id = current_user["id"]
    
    offers = offer_repo.get_by_driver_id(driver_id, status=status)
    
    return {"total": len(offers), "items": offers}


@router.post("/{trip_id}/start")
async def start_trip(
    trip_id: int,
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Driver starts trip (picked up cargo)"""
    trip_service = TripService(db)
    driver_id = current_user["id"]
    
    trip = trip_service.start_trip(trip_id, driver_id)
    
    return {"message": "Trip started", "trip": trip}


@router.post("/{trip_id}/complete")
async def complete_trip(
    trip_id: int,
    final_fare: float,
    current_user = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """
    Driver completes trip
    Automatically charges commission to driver's wallet
    """
    trip_service = TripService(db)
    driver_id = current_user["id"]
    
    trip = trip_service.complete_trip(trip_id, driver_id, final_fare)
    
    return {
        "message": "Trip completed",
        "trip_id": trip.id,
        "commission_charged": trip.commission_amount
    }


@router.get("/{trip_id}")
async def get_trip(
    trip_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trip details"""
    trip_service = TripService(db)
    
    trip = trip_service.get_trip(trip_id)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check authorization
    role = current_user["role"]
    user_id = current_user["id"]
    
    if role == "USER" and trip.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if role == "DRIVER" and trip.driver_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return trip
