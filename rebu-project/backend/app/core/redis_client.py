"""
Redis client for geospatial queries, locks, and caching
"""
import redis
from typing import Optional
from app.core.config import settings


class RedisClient:
    """Redis client wrapper for Rebu operations"""
    
    def __init__(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    
    # Geospatial operations for driver location
    def add_driver_location(self, driver_id: int, lat: float, lon: float) -> int:
        """Add driver to geospatial index"""
        return self.client.geoadd("drivers:online", (lon, lat, str(driver_id)))
    
    def remove_driver_location(self, driver_id: int) -> int:
        """Remove driver from geospatial index"""
        return self.client.zrem("drivers:online", str(driver_id))
    
    def get_nearby_drivers(self, lat: float, lon: float, radius_km: float, count: Optional[int] = None) -> list[dict]:
        """
        Find drivers within radius
        Returns: [{"driver_id": "123", "distance": 1.5}, ...]
        """
        results = self.client.georadius(
            "drivers:online",
            lon, lat,
            radius_km,
            unit="km",
            withdist=True,
            count=count,
            sort="ASC"  # Nearest first
        )
        
        return [
            {"driver_id": int(driver_id), "distance_km": float(distance)}
            for driver_id, distance in results
        ]
    
    def get_driver_location(self, driver_id: int) -> Optional[tuple[float, float]]:
        """Get driver's current location (lon, lat)"""
        result = self.client.geopos("drivers:online", str(driver_id))
        if result and result[0]:
            lon, lat = result[0]
            return (float(lon), float(lat))
        return None
    
    # Locks for preventing double acceptance
    def acquire_trip_lock(self, trip_request_id: int, timeout_seconds: int = 10) -> bool:
        """
        Try to acquire lock for trip request
        Returns True if lock acquired, False if already locked
        """
        lock_key = f"lock:trip_request:{trip_request_id}"
        return self.client.set(lock_key, "1", ex=timeout_seconds, nx=True)
    
    def release_trip_lock(self, trip_request_id: int):
        """Release lock for trip request"""
        lock_key = f"lock:trip_request:{trip_request_id}"
        self.client.delete(lock_key)
    
    # Offer tracking
    def add_pending_offer(self, trip_request_id: int, driver_id: int, expiry_seconds: int = 60):
        """Track that an offer was sent to a driver"""
        key = f"offers:trip:{trip_request_id}"
        self.client.sadd(key, str(driver_id))
        self.client.expire(key, expiry_seconds + 60)  # Keep a bit longer than offer expiry
    
    def get_pending_offers(self, trip_request_id: int) -> set[int]:
        """Get all drivers who have pending offers for this trip"""
        key = f"offers:trip:{trip_request_id}"
        driver_ids = self.client.smembers(key)
        return {int(did) for did in driver_ids}
    
    def clear_pending_offers(self, trip_request_id: int):
        """Clear all pending offers for a trip"""
        key = f"offers:trip:{trip_request_id}"
        self.client.delete(key)
    
    # Driver status cache
    def set_driver_status(self, driver_id: int, status: str, ttl_seconds: int = 300):
        """Cache driver status (ONLINE, OFFLINE, BUSY)"""
        key = f"driver:status:{driver_id}"
        self.client.set(key, status, ex=ttl_seconds)
    
    def get_driver_status(self, driver_id: int) -> Optional[str]:
        """Get cached driver status"""
        key = f"driver:status:{driver_id}"
        return self.client.get(key)
    
    # Trip state cache
    def set_trip_state(self, trip_id: int, state: dict, ttl_seconds: int = 3600):
        """Cache trip state for quick access"""
        import json
        key = f"trip:state:{trip_id}"
        self.client.set(key, json.dumps(state), ex=ttl_seconds)
    
    def get_trip_state(self, trip_id: int) -> Optional[dict]:
        """Get cached trip state"""
        import json
        key = f"trip:state:{trip_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    # General cache operations
    def set_cache(self, key: str, value: str, ttl_seconds: int = 300):
        """Set cache value"""
        self.client.set(key, value, ex=ttl_seconds)
    
    def get_cache(self, key: str) -> Optional[str]:
        """Get cache value"""
        return self.client.get(key)
    
    def delete_cache(self, key: str):
        """Delete cache value"""
        self.client.delete(key)
    
    def ping(self) -> bool:
        """Check if Redis is connected"""
        try:
            return self.client.ping()
        except:
            return False


# Singleton instance
redis_client = RedisClient()
