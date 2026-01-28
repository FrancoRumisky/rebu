"""
Repository implementations for all models
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import (
    User, Driver, Vehicle, TripRequest, TripOffer, 
    Trip, WalletTransaction, Subscription, DriverAvailabilityBlock,
    TripRequestStatus, OfferStatus, TripStatus, DriverStatus
)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()
    
    def create(self, email: str, phone: str, password_hash: str, full_name: str) -> User:
        user = User(
            email=email,
            phone=phone,
            password_hash=password_hash,
            full_name=full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class DriverRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, driver_id: int) -> Optional[Driver]:
        return self.db.query(Driver).filter(Driver.id == driver_id).first()
    
    def get_by_ids(self, driver_ids: List[int]) -> List[Driver]:
        return self.db.query(Driver).filter(Driver.id.in_(driver_ids)).all()
    
    def get_by_email(self, email: str) -> Optional[Driver]:
        return self.db.query(Driver).filter(Driver.email == email).first()
    
    def get_active_drivers(self) -> List[Driver]:
        return self.db.query(Driver).filter(
            Driver.status == DriverStatus.ACTIVE
        ).all()
    
    def create(self, email: str, phone: str, password_hash: str, 
               full_name: str, license_number: str, license_expiry_date: datetime) -> Driver:
        driver = Driver(
            email=email,
            phone=phone,
            password_hash=password_hash,
            full_name=full_name,
            license_number=license_number,
            license_expiry_date=license_expiry_date
        )
        self.db.add(driver)
        self.db.commit()
        self.db.refresh(driver)
        return driver
    
    def update_wallet_balance(self, driver_id: int, new_balance: float):
        driver = self.get_by_id(driver_id)
        if driver:
            driver.wallet_balance = new_balance
            self.db.commit()


class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    def get_by_driver_id(self, driver_id: int) -> List[Vehicle]:
        return self.db.query(Vehicle).filter(Vehicle.driver_id == driver_id).all()

    def get_active_by_driver_id(self, driver_id: int) -> Optional[Vehicle]:
        # Si tu modelo no tiene is_active, cambiamos esta lógica
        if hasattr(Vehicle, "is_active"):
            return (
                self.db.query(Vehicle)
                .filter(Vehicle.driver_id == driver_id, Vehicle.is_active == True)
                .order_by(Vehicle.id.desc())
                .first()
            )
        return (
            self.db.query(Vehicle)
            .filter(Vehicle.driver_id == driver_id)
            .order_by(Vehicle.id.desc())
            .first()
        )

    def create(self, driver_id: int, **kwargs) -> Vehicle:
        vehicle = Vehicle(driver_id=driver_id, **kwargs)
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle
        

class TripRequestRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, trip_request_id: int) -> Optional[TripRequest]:
        return self.db.query(TripRequest).filter(TripRequest.id == trip_request_id).first()
    
    def get_by_user_id(self, user_id: int, status: Optional[str] = None) -> List[TripRequest]:
        query = self.db.query(TripRequest).filter(TripRequest.user_id == user_id)
        if status:
            query = query.filter(TripRequest.status == status)
        return query.order_by(TripRequest.created_at.desc()).all()
    
    def create(self, user_id: int, mode: str, pickup_data: dict, 
               dropoff_data: dict, estimated_fare: float, **kwargs) -> TripRequest:
        trip_request = TripRequest(
            user_id=user_id,
            mode=mode,
            pickup_address=pickup_data['address'],
            pickup_lat=pickup_data['lat'],
            pickup_lon=pickup_data['lon'],
            dropoff_address=dropoff_data['address'],
            dropoff_lat=dropoff_data['lat'],
            dropoff_lon=dropoff_data['lon'],
            estimated_fare=estimated_fare,
            **kwargs
        )
        self.db.add(trip_request)
        self.db.commit()
        self.db.refresh(trip_request)
        return trip_request


class TripOfferRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, offer_id: int) -> Optional[TripOffer]:
        return self.db.query(TripOffer).filter(TripOffer.id == offer_id).first()
    
    def get_by_driver_id(self, driver_id: int, status: Optional[str] = None) -> List[TripOffer]:
        query = self.db.query(TripOffer).filter(TripOffer.driver_id == driver_id)
        if status:
            query = query.filter(TripOffer.status == status)
        return query.order_by(TripOffer.created_at.desc()).all()
    
    def has_offer_for_driver(self, trip_request_id: int, driver_id: int) -> bool:
        return self.db.query(TripOffer).filter(
            TripOffer.trip_request_id == trip_request_id,
            TripOffer.driver_id == driver_id
        ).first() is not None
    
    def create(self, trip_request_id: int, driver_id: int, 
               offered_fare: float, expires_at: datetime) -> TripOffer:
        offer = TripOffer(
            trip_request_id=trip_request_id,
            driver_id=driver_id,
            offered_fare=offered_fare,
            expires_at=expires_at
        )
        self.db.add(offer)
        self.db.commit()
        self.db.refresh(offer)
        return offer
    
    def update_status(self, offer_id: int, status: str) -> Optional[TripOffer]:
        offer = self.get_by_id(offer_id)
        if offer:
            offer.status = status
            offer.responded_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(offer)
        return offer


class TripRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, trip_id: int) -> Optional[Trip]:
        return self.db.query(Trip).filter(Trip.id == trip_id).first()
    
    def get_by_driver_id(self, driver_id: int) -> List[Trip]:
        return self.db.query(Trip).filter(
            Trip.driver_id == driver_id
        ).order_by(Trip.created_at.desc()).all()
    
    def create(self, trip_request: TripRequest, driver_id: int, 
               vehicle_id: int, commission_rate: float) -> Trip:
        trip = Trip(
            trip_request_id=trip_request.id,
            user_id=trip_request.user_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            pickup_address=trip_request.pickup_address,
            pickup_lat=trip_request.pickup_lat,
            pickup_lon=trip_request.pickup_lon,
            dropoff_address=trip_request.dropoff_address,
            dropoff_lat=trip_request.dropoff_lat,
            dropoff_lon=trip_request.dropoff_lon,
            estimated_fare=trip_request.estimated_fare,
            commission_rate=commission_rate
        )
        self.db.add(trip)
        self.db.commit()
        self.db.refresh(trip)
        return trip


class WalletTransactionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, driver_id: int, type: str, amount: float, 
               trip_id: Optional[int] = None, description: Optional[str] = None,
               reference: Optional[str] = None) -> WalletTransaction:
        
        # Get current balance
        from app.repositories import DriverRepository
        driver_repo = DriverRepository(self.db)
        driver = driver_repo.get_by_id(driver_id)
        balance_after = driver.wallet_balance + amount
        
        transaction = WalletTransaction(
            driver_id=driver_id,
            type=type,
            amount=amount,
            balance_after=balance_after,
            trip_id=trip_id,
            description=description,
            reference=reference
        )
        self.db.add(transaction)
        
        # Update driver balance
        driver.wallet_balance = balance_after
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_by_driver_id(self, driver_id: int, limit: int = 50, offset: int = 0) -> List[WalletTransaction]:
        return self.db.query(WalletTransaction).filter(
            WalletTransaction.driver_id == driver_id
        ).order_by(
            WalletTransaction.created_at.desc()
        ).limit(limit).offset(offset).all()


class DriverAvailabilityRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def has_conflict(self, driver_id: int, start_time: datetime, end_time: datetime) -> bool:
        """Check if driver has conflicting availability blocks"""
        conflicts = self.db.query(DriverAvailabilityBlock).filter(
            DriverAvailabilityBlock.driver_id == driver_id,
            DriverAvailabilityBlock.start_time < end_time,
            DriverAvailabilityBlock.end_time > start_time
        ).first()
        return conflicts is not None
    
    def create(self, driver_id: int, trip_request_id: int, 
               start_time: datetime, end_time: datetime, reason: str) -> DriverAvailabilityBlock:
        block = DriverAvailabilityBlock(
            driver_id=driver_id,
            trip_request_id=trip_request_id,
            start_time=start_time,
            end_time=end_time,
            reason=reason
        )
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block
    
    def delete_by_trip_request(self, trip_request_id: int):
        self.db.query(DriverAvailabilityBlock).filter(
            DriverAvailabilityBlock.trip_request_id == trip_request_id
        ).delete()
        self.db.commit()
