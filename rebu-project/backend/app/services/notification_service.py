"""
Notification Service - Firebase Cloud Messaging
"""
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional
from app.core.config import settings


class NotificationService:
    """Service for sending push notifications via FCM"""
    
    def __init__(self):
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not settings.FIREBASE_CREDENTIALS_PATH:
                print("⚠️  Firebase credentials not configured")
                return
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            
            self.initialized = True
            print("✅ Firebase initialized")
        
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
    
    async def send_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """
        Send a push notification to a device
        """
        if not self.initialized:
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=fcm_token
            )
            
            response = messaging.send(message)
            print(f"✅ Notification sent: {response}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
            return False
    
    async def send_trip_offer_notification(self, fcm_token: str, trip_request, offer):
        """Send notification when driver receives trip offer"""
        return await self.send_notification(
            fcm_token,
            title="🚚 Nueva solicitud de flete",
            body=f"De {trip_request.pickup_address} a {trip_request.dropoff_address}. Tarifa estimada: ${trip_request.estimated_fare}",
            data={
                "type": "TRIP_OFFER",
                "trip_request_id": str(trip_request.id),
                "offer_id": str(offer.id)
            }
        )
    
    async def send_scheduled_trip_assignment(self, fcm_token: str, trip_request):
        """Send notification when driver is pre-assigned to scheduled trip"""
        return await self.send_notification(
            fcm_token,
            title="📅 Viaje programado asignado",
            body=f"Tienes un viaje programado para {trip_request.scheduled_start_at.strftime('%d/%m/%Y %H:%M')}",
            data={
                "type": "SCHEDULED_ASSIGNMENT",
                "trip_request_id": str(trip_request.id)
            }
        )
    
    async def send_trip_reminder(self, fcm_token: str, trip, minutes_before: int):
        """Send reminder before scheduled trip"""
        return await self.send_notification(
            fcm_token,
            title=f"⏰ Recordatorio: Viaje en {minutes_before} minutos",
            body=f"Tu viaje a {trip.dropoff_address} comienza pronto",
            data={
                "type": "TRIP_REMINDER",
                "trip_id": str(trip.id),
                "minutes_before": str(minutes_before)
            }
        )
    
    async def send_trip_reminder_to_user(self, fcm_token: str, trip, minutes_before: int):
        """Send reminder to user before scheduled trip"""
        return await self.send_notification(
            fcm_token,
            title=f"⏰ Tu flete llega en {minutes_before} minutos",
            body=f"El conductor llegará pronto a {trip.pickup_address}",
            data={
                "type": "TRIP_REMINDER",
                "trip_id": str(trip.id)
            }
        )
    
    async def send_trip_expired_notification(self, fcm_token: str, trip_request):
        """Send notification when trip request expires"""
        return await self.send_notification(
            fcm_token,
            title="❌ No se encontró conductor",
            body="Tu solicitud de flete expiró. Por favor intenta nuevamente.",
            data={
                "type": "TRIP_EXPIRED",
                "trip_request_id": str(trip_request.id)
            }
        )
    
    async def send_trip_status_update(self, fcm_token: str, trip, new_status: str):
        """Send notification on trip status change"""
        status_messages = {
            "DRIVER_ARRIVING": "🚗 El conductor va en camino",
            "ARRIVED": "📍 El conductor llegó al punto de recogida",
            "IN_PROGRESS": "🚚 Tu flete está en camino",
            "COMPLETED": "✅ Viaje completado. ¡Gracias por usar Rebu!",
            "CANCELLED": "❌ Viaje cancelado"
        }
        
        return await self.send_notification(
            fcm_token,
            title="Actualización de viaje",
            body=status_messages.get(new_status, f"Estado: {new_status}"),
            data={
                "type": "TRIP_STATUS_UPDATE",
                "trip_id": str(trip.id),
                "status": new_status
            }
        )
