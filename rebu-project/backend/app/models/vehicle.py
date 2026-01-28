"""
Vehicle model - Vehículos de los conductores
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class VehicleType(str, enum.Enum):
    PICKUP = "PICKUP"          # Camioneta pequeña
    VAN = "VAN"                # Furgoneta
    SMALL_TRUCK = "SMALL_TRUCK"  # Camión pequeño
    MEDIUM_TRUCK = "MEDIUM_TRUCK"  # Camión mediano
    LARGE_TRUCK = "LARGE_TRUCK"  # Camión grande


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False, index=True)
    
    # Vehicle details
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String, nullable=False)
    
    # License plate
    license_plate = Column(String, unique=True, nullable=False, index=True)
    
    # Capacity
    max_weight_kg = Column(Float, nullable=False)  # e.g., 1000 kg
    max_volume_m3 = Column(Float, nullable=True)   # e.g., 15 m³
    
    # Images
    front_image_url = Column(String, nullable=True)
    side_image_url = Column(String, nullable=True)
    license_plate_image_url = Column(String, nullable=True)
    
    # Insurance
    insurance_policy_number = Column(String, nullable=True)
    insurance_expiry_date = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    driver = relationship("Driver", back_populates="vehicles")
    trips = relationship("Trip", back_populates="vehicle")
    
    def __repr__(self):
        return f"<Vehicle {self.id}: {self.license_plate} ({self.vehicle_type.value})>"
