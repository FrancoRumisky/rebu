# Rebu - Guía de Deploy y Arquitectura

## 🏗️ Arquitectura Detallada

### Flujo de Matching ON_DEMAND

```
1. Usuario crea TripRequest (mode=ON_DEMAND)
   └─> Backend crea registro en DB
       └─> Se define expires_at (ahora + 15 min)
       └─> Status = PENDING

2. Sistema inicia matching:
   ONDA 1 (0-30s): Buscar conductores dentro de 3km
   ├─> Redis GEORADIUS "drivers:online" 3km
   ├─> Filtrar: status=ACTIVE, within_credit_limit
   ├─> Crear TripOffer para cada driver
   ├─> Redis: track pending offers
   └─> FCM: enviar notificación a drivers

   Si ningún driver acepta en 30s:
   ONDA 2 (30-60s): Buscar dentro de 5km
   └─> Repetir proceso

   Si aún no hay respuesta:
   ONDA 3 (60-90s): Buscar dentro de 10km
   └─> Repetir proceso

3. Driver acepta oferta:
   ├─> Backend intenta acquire_lock en Redis
   ├─> Si lock exitoso:
   │   ├─> TripOffer.status = ACCEPTED
   │   ├─> TripRequest.status = MATCHED
   │   ├─> Crear Trip con status=CONFIRMED
   │   ├─> Clear pending offers en Redis
   │   └─> Notificar a usuario
   └─> Si lock falla:
       └─> Otro driver ya aceptó, devolver error

4. Si nadie acepta antes de expires_at:
   └─> ExpiryJob marca TripRequest como EXPIRED
       └─> Notificar usuario
```

### Flujo de Matching SCHEDULED

```
1. Usuario crea TripRequest (mode=SCHEDULED)
   ├─> Define scheduled_start_at y scheduled_end_at
   └─> Status = PENDING

2. Sistema busca drivers disponibles:
   ├─> Query drivers con status=ACTIVE
   ├─> Para cada driver:
   │   └─> Verificar driver_availability_blocks
   │       └─> Si no hay conflicto → Driver disponible
   └─> Presentar lista a usuario o admin

3. Pre-asignar conductor:
   ├─> Crear DriverAvailabilityBlock
   │   ├─> driver_id
   │   ├─> trip_request_id
   │   ├─> start_time = scheduled_start_at
   │   └─> end_time = scheduled_end_at
   ├─> TripRequest.pre_assigned_driver_id = driver_id
   ├─> Crear Trip con status=CONFIRMED
   └─> Notificar driver

4. Recordatorios automáticos:
   ReminderJob ejecuta cada 5 minutos:
   ├─> T-60min: Enviar notificación FCM a driver y usuario
   └─> T-15min: Enviar segunda notificación

5. Verificación pre-inicio (T-30min):
   AutoRematchJob:
   ├─> Verificar si driver está online
   ├─> Si offline:
   │   ├─> Cancelar Trip actual
   │   ├─> Eliminar DriverAvailabilityBlock
   │   ├─> TripRequest.status = PENDING
   │   └─> Buscar nuevo driver
   └─> Si online: Continuar
```

## 🚀 Deploy a Google Cloud Run

### Prerequisites

```bash
# Instalar Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Configurar proyecto
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
```

### 1. Crear Cloud SQL (PostgreSQL)

```bash
# Crear instancia Cloud SQL
gcloud sql instances create rebu-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Crear base de datos
gcloud sql databases create rebu_db --instance=rebu-db

# Crear usuario
gcloud sql users create rebu \
  --instance=rebu-db \
  --password=YOUR_SECURE_PASSWORD

# Habilitar extensión PostGIS
gcloud sql connect rebu-db --user=postgres
# En psql:
\c rebu_db
CREATE EXTENSION postgis;
\q
```

### 2. Crear Redis en Memorystore

```bash
gcloud redis instances create rebu-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

### 3. Configurar Firestore

```bash
# Habilitar Firestore
gcloud firestore databases create --region=us-central1
```

### 4. Build y Deploy Backend

```bash
# Navegar a backend
cd backend

# Build imagen Docker
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rebu-backend

# Deploy a Cloud Run
gcloud run deploy rebu-backend \
  --image gcr.io/YOUR_PROJECT_ID/rebu-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "POSTGRES_HOST=/cloudsql/YOUR_PROJECT_ID:us-central1:rebu-db" \
  --set-env-vars "POSTGRES_USER=rebu" \
  --set-env-vars "POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD" \
  --set-env-vars "POSTGRES_DB=rebu_db" \
  --set-env-vars "REDIS_HOST=REDIS_IP" \
  --set-env-vars "REDIS_PORT=6379" \
  --add-cloudsql-instances YOUR_PROJECT_ID:us-central1:rebu-db

# Obtener URL
gcloud run services describe rebu-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

### 5. Configurar Firebase (FCM)

```bash
# En Firebase Console:
1. Crear proyecto Firebase
2. Agregar apps Android y iOS
3. Descargar google-services.json y GoogleService-Info.plist
4. Descargar service account key (para backend)
5. Habilitar Cloud Messaging
```

### 6. Variables de Entorno (.env para local)

```bash
# Backend .env
POSTGRES_USER=rebu
POSTGRES_PASSWORD=rebu_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rebu_db

REDIS_HOST=localhost
REDIS_PORT=6379

FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json

SECRET_KEY=your-secret-key-here
```

## 📊 Modelo de Monetización - Detalles

### Comisiones por Tier

```python
FREE tier (default):
- Comisión: 15%
- Límite crédito: $500
- Sin costo mensual

PRO tier:
- Comisión: 10%
- Límite crédito: $1,000
- Costo: $29.99/mes

PREMIUM tier:
- Comisión: 5%
- Límite crédito: $2,000
- Costo: $59.99/mes
- Prioridad en matching
```

### Flujo de Cobro

```
1. Trip completado:
   ├─> Cliente paga al conductor directamente (efectivo/transferencia)
   ├─> Driver.wallet_balance -= (final_fare * commission_rate)
   ├─> WalletTransaction creada (tipo: TRIP_COMMISSION)
   └─> Si balance < -credit_limit:
       └─> Driver.status = LIMITED

2. Driver hace pago a plataforma:
   ├─> Payment gateway o transferencia manual
   ├─> Admin registra pago en sistema
   ├─> Driver.wallet_balance += payment_amount
   ├─> WalletTransaction (tipo: PAYMENT)
   └─> Si balance > -credit_limit:
       └─> Driver.status = ACTIVE (si estaba LIMITED)

3. Reporte mensual:
   ├─> Calcular total commissions adeudadas
   ├─> Enviar invoice por email
   └─> Recordatorio si balance negativo alto
```

## 🔒 Security Best Practices

### Backend

```python
# 1. Rate Limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/trips/request")
@limiter.limit("5/minute")  # Max 5 requests per minute
async def create_trip(...):
    pass

# 2. Input Validation
from pydantic import validator

class TripRequest(BaseModel):
    estimated_fare: float
    
    @validator('estimated_fare')
    def validate_fare(cls, v):
        if v < 0 or v > 1_000_000:
            raise ValueError('Invalid fare amount')
        return v

# 3. SQL Injection Prevention
# ✓ Use SQLAlchemy ORM (parameterized queries)
# ✗ Never use raw SQL with f-strings

# 4. HTTPS Only
app.add_middleware(
    HTTPSRedirectMiddleware
)

# 5. CORS Proper Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.rebu.com"],  # Specific domains
    allow_credentials=True,
)
```

### Flutter

```dart
// 1. Secure Storage
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final storage = FlutterSecureStorage();
await storage.write(key: 'access_token', value: token);

// 2. Certificate Pinning
// pubspec.yaml:
// dependencies:
//   http_certificate_pinning: ^2.0.0

// 3. Obfuscate Code
flutter build apk --obfuscate --split-debug-info=build/debug-info

// 4. Input Sanitization
String sanitizeInput(String input) {
  return input.replaceAll(RegExp(r'[^\w\s@.-]'), '');
}
```

## 📈 Monitoring & Observability

### Metrics to Track

```
Backend:
- API response times (p50, p95, p99)
- Error rates by endpoint
- Active trips count
- Drivers online count
- Match success rate
- Average matching time
- Redis latency
- Database connection pool usage

Business:
- Trips per day/week/month
- Revenue (commissions)
- Driver retention rate
- User retention rate
- Average trip distance
- Average trip fare
- Cancellation rate
```

### Logging

```python
import logging
import json

logger = logging.getLogger(__name__)

# Structured logging
logger.info(json.dumps({
    "event": "trip_matched",
    "trip_request_id": trip_request.id,
    "driver_id": driver.id,
    "matching_time_seconds": (datetime.utcnow() - trip_request.created_at).total_seconds(),
    "wave_number": 1
}))
```

## 🧪 Testing Strategy

### Backend Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Coverage
pytest --cov=app tests/
```

### Flutter Tests

```bash
# Unit tests
flutter test

# Widget tests
flutter test test/widget_test.dart

# Integration tests
flutter drive --target=test_driver/app.dart
```

## 📱 App Store Submission

### Android (Google Play)

```bash
# Build release APK
flutter build apk --release

# Build App Bundle (preferred)
flutter build appbundle --release

# Sign with keystore
keytool -genkey -v -keystore rebu-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias rebu
```

### iOS (App Store)

```bash
# Build release
flutter build ios --release

# Archive in Xcode
# Product > Archive > Distribute App
```

## 🆘 Troubleshooting

### Common Issues

```bash
# Redis connection failed
# Fix: Check REDIS_HOST and firewall rules

# Database migration failed
# Fix: Run manually:
alembic upgrade head

# FCM notifications not working
# Fix: Verify firebase credentials path and permissions

# Location not updating
# Fix: Check Android/iOS permissions in manifest
```

## 📞 Support & Contact

- Documentación API: https://api.rebu.com/docs
- Status page: https://status.rebu.com
- Support: support@rebu.com
