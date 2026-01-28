"""
Trip request schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.trip_request import TripMode, TripRequestStatus


class LocationData(BaseModel):
    address: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class CreateTripRequestBase(BaseModel):
    mode: TripMode
    pickup: LocationData
    dropoff: LocationData
    estimated_fare: float = Field(..., gt=0)
    required_vehicle_type: Optional[str] = None
    cargo_description: Optional[str] = None
    cargo_weight_kg: Optional[float] = None


class CreateOnDemandTripRequest(CreateTripRequestBase):
    mode: TripMode = TripMode.ON_DEMAND


class CreateScheduledTripRequest(CreateTripRequestBase):
    mode: TripMode = TripMode.SCHEDULED
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    
    @validator('scheduled_start_at')
    def validate_start_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('scheduled_start_at must be in the future')
        return v
    
    @validator('scheduled_end_at')
    def validate_end_time(cls, v, values):
        if 'scheduled_start_at' in values and v <= values['scheduled_start_at']:
            raise ValueError('scheduled_end_at must be after scheduled_start_at')
        return v


class TripRequestResponse(BaseModel):
    id: int
    user_id: int
    mode: TripMode
    status: TripRequestStatus
    
    pickup_address: str
    pickup_lat: float
    pickup_lon: float
    
    dropoff_address: str
    dropoff_lat: float
    dropoff_lon: float
    
    estimated_fare: float
    estimated_distance_km: Optional[float]
    estimated_duration_minutes: Optional[int]
    
    # Scheduled fields
    scheduled_start_at: Optional[datetime]
    scheduled_end_at: Optional[datetime]
    pre_assigned_driver_id: Optional[int]
    
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TripRequestListResponse(BaseModel):
    total: int
    items: list[TripRequestResponse]
