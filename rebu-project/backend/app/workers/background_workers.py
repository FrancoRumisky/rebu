"""
Background Workers - Scheduled jobs for reminders, expiry, and cleanup
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.redis_client import redis_client
from app.models import TripRequest, TripRequestStatus, Trip, TripStatus, DriverStatus
from app.services.notification_service import NotificationService


class BackgroundWorkers:
    """Background workers for Rebu platform"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notification_service = NotificationService()
    
    def start(self):
        """Start all background jobs"""
        if not settings.ENABLE_BACKGROUND_WORKERS:
            return
        
        # Reminder job: every 5 minutes
        self.scheduler.add_job(
            self.reminder_job,
            'interval',
            minutes=5,
            id='reminder_job'
        )
        
        # Auto-rematch job: every 10 minutes
        self.scheduler.add_job(
            self.auto_rematch_job,
            'interval',
            minutes=10,
            id='auto_rematch_job'
        )
        
        # Expiry job: every 2 minutes
        self.scheduler.add_job(
            self.expiry_job,
            'interval',
            minutes=2,
            id='expiry_job'
        )
        
        # Availability cleanup: every hour
        self.scheduler.add_job(
            self.availability_cleanup_job,
            'interval',
            hours=1,
            id='availability_cleanup_job'
        )
        
        self.scheduler.start()
        print("✅ Background workers started")
    
    def stop(self):
        """Stop all background jobs"""
        self.scheduler.shutdown()
        print("🛑 Background workers stopped")
    
    def reminder_job(self):
        """
        Send reminders for scheduled trips
        T-60min and T-15min before scheduled_start_at
        """
        db: Session = SessionLocal()
        
        try:
            now = datetime.utcnow()
            
            # Find scheduled trips that need reminders
            for reminder_minutes in settings.SCHEDULED_REMINDER_MINUTES:
                target_time = now + timedelta(minutes=reminder_minutes)
                
                # Query trips that start around target_time
                trips = db.query(TripRequest).filter(
                    TripRequest.mode == "SCHEDULED",
                    TripRequest.status == TripRequestStatus.MATCHED,
                    TripRequest.scheduled_start_at.between(
                        target_time - timedelta(minutes=2),
                        target_time + timedelta(minutes=2)
                    )
                ).all()
                
                for trip_request in trips:
                    # Check if reminder already sent
                    if reminder_minutes == 60 and trip_request.reminder_60min_sent:
                        continue
                    if reminder_minutes == 15 and trip_request.reminder_15min_sent:
                        continue
                    
                    # Get associated trip
                    trip = db.query(Trip).filter(
                        Trip.trip_request_id == trip_request.id
                    ).first()
                    
                    if not trip:
                        continue
                    
                    # Send reminder to driver
                    driver = trip.driver
                    if driver.fcm_token:
                        self.notification_service.send_trip_reminder(
                            driver.fcm_token,
                            trip,
                            minutes_before=reminder_minutes
                        )
                    
                    # Send reminder to user
                    user = trip.user
                    if user.fcm_token:
                        self.notification_service.send_trip_reminder_to_user(
                            user.fcm_token,
                            trip,
                            minutes_before=reminder_minutes
                        )
                    
                    # Mark reminder as sent
                    if reminder_minutes == 60:
                        trip_request.reminder_60min_sent = True
                    elif reminder_minutes == 15:
                        trip_request.reminder_15min_sent = True
                    
                    db.commit()
            
            print(f"✅ Reminder job completed at {now}")
        
        except Exception as e:
            print(f"❌ Error in reminder_job: {e}")
            db.rollback()
        
        finally:
            db.close()
    
    def auto_rematch_job(self):
        """
        Auto-rematch scheduled trips if driver doesn't confirm
        Checks trips within SCHEDULED_CONFIRM_WINDOW_MINUTES
        """
        db: Session = SessionLocal()
        
        try:
            now = datetime.utcnow()
            confirm_window = timedelta(minutes=settings.SCHEDULED_CONFIRM_WINDOW_MINUTES)
            
            # Find scheduled trips that start soon but driver hasn't confirmed
            trips = db.query(Trip).join(TripRequest).filter(
                TripRequest.mode == "SCHEDULED",
                Trip.status == TripStatus.CONFIRMED,
                TripRequest.scheduled_start_at.between(
                    now,
                    now + confirm_window
                )
            ).all()
            
            for trip in trips:
                driver = trip.driver
                
                # Check if driver is online
                driver_status = redis_client.get_driver_status(driver.id)
                
                if driver_status != "ONLINE":
                    # Driver is offline, try to rematch
                    print(f"🔄 Auto-rematching trip {trip.id} - driver {driver.id} is offline")
                    
                    # Cancel current trip
                    trip.status = TripStatus.CANCELLED
                    trip.cancelled_by = "SYSTEM"
                    trip.cancellation_reason = "Driver unavailable, auto-rematched"
                    trip.cancelled_at = now
                    
                    # Reset trip request to PENDING
                    trip.trip_request.status = TripRequestStatus.PENDING
                    trip.trip_request.pre_assigned_driver_id = None
                    
                    # Clear availability block
                    from app.repositories.driver_availability_repository import DriverAvailabilityRepository
                    availability_repo = DriverAvailabilityRepository(db)
                    availability_repo.delete_by_trip_request(trip.trip_request_id)
                    
                    db.commit()
                    
                    # TODO: Trigger new matching process
                    # This could be done via API call or message queue
            
            print(f"✅ Auto-rematch job completed at {now}")
        
        except Exception as e:
            print(f"❌ Error in auto_rematch_job: {e}")
            db.rollback()
        
        finally:
            db.close()
    
    def expiry_job(self):
        """
        Mark expired ON_DEMAND trip requests and release locks
        """
        db: Session = SessionLocal()
        
        try:
            now = datetime.utcnow()
            
            # Find expired trip requests
            expired_trips = db.query(TripRequest).filter(
                TripRequest.status == TripRequestStatus.PENDING,
                TripRequest.expires_at <= now
            ).all()
            
            for trip_request in expired_trips:
                trip_request.status = TripRequestStatus.EXPIRED
                
                # Release Redis lock if exists
                redis_client.release_trip_lock(trip_request.id)
                redis_client.clear_pending_offers(trip_request.id)
                
                # Notify user
                user = trip_request.user
                if user.fcm_token:
                    self.notification_service.send_trip_expired_notification(
                        user.fcm_token,
                        trip_request
                    )
            
            db.commit()
            
            if expired_trips:
                print(f"✅ Expired {len(expired_trips)} trip requests")
        
        except Exception as e:
            print(f"❌ Error in expiry_job: {e}")
            db.rollback()
        
        finally:
            db.close()
    
    def availability_cleanup_job(self):
        """
        Remove past availability blocks to keep table clean
        """
        db: Session = SessionLocal()
        
        try:
            from app.models import DriverAvailabilityBlock
            
            now = datetime.utcnow()
            
            # Delete blocks that ended more than 24 hours ago
            cutoff = now - timedelta(hours=24)
            
            deleted = db.query(DriverAvailabilityBlock).filter(
                DriverAvailabilityBlock.end_time < cutoff
            ).delete()
            
            db.commit()
            
            if deleted > 0:
                print(f"✅ Cleaned up {deleted} old availability blocks")
        
        except Exception as e:
            print(f"❌ Error in availability_cleanup_job: {e}")
            db.rollback()
        
        finally:
            db.close()


# Singleton instance
workers = BackgroundWorkers()
