# Rebu - Plataforma de Fletes On-Demand y Programados

## 🚀 Descripción del Proyecto

Rebu es una plataforma tipo Uber pero especializada en servicios de fletes y mudanzas, con soporte para:
- **Viajes inmediatos (ON_DEMAND)**: Matching en tiempo real con conductores cercanos
- **Viajes programados (SCHEDULED)**: Reserva con anticipación y pre-asignación de conductores

## 📋 Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Flutter Client │────▶│  FastAPI Backend│────▶│   PostgreSQL     │
└─────────────────┘     │   (Cloud Run)   │     │   + PostGIS      │
                        └─────────────────┘     └──────────────────┘
                               │    │
                               │    └──────────▶ ┌──────────────────┐
                               │                 │      Redis       │
                               │                 │ (Geo + Locks)    │
                               │                 └──────────────────┘
                               │
┌─────────────────┐           │                 ┌──────────────────┐
│Flutter Conductor│◀──────────┴────────────────▶│    Firestore     │
└─────────────────┘                             │  (Chat + Real-   │
                                                │   time data)     │
                                                └──────────────────┘
        │
        └──────────────────────────────────────▶ ┌──────────────────┐
                                                 │       FCM        │
                                                 │ (Push Notifications)│
                                                 └──────────────────┘

┌─────────────────┐
│  Next.js Admin  │────▶ Backend API
└─────────────────┘
```

## 🛠️ Stack Tecnológico

### Backend
- **Framework**: FastAPI 0.109+
- **Base de datos**: PostgreSQL 15+ con PostGIS
- **Cache/Geo**: Redis 7+
- **Real-time**: Firestore (chat)
- **Notificaciones**: Firebase Cloud Messaging (FCM)
- **Deploy**: Google Cloud Run
- **Workers**: APScheduler para jobs programados

### Frontend
- **Mobile**: Flutter 3.16+ (Client y Driver apps)
- **Admin**: Next.js 14+ con TypeScript

### DevOps
- Docker / Docker Compose
- Google Cloud Platform (Cloud Run, Cloud SQL, Memorystore)

## 🏗️ Estructura del Proyecto

```
rebu-project/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # Routers REST
│   │   ├── core/              # Config, seguridad
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Lógica de negocio
│   │   ├── repositories/      # Acceso a datos
│   │   ├── workers/           # Background jobs
│   │   └── utils/             # Helpers
│   ├── alembic/               # Migraciones DB
│   ├── tests/
│   └── Dockerfile
│
├── flutter-client/            # App Cliente
│   ├── lib/
│   │   ├── features/
│   │   ├── core/
│   │   ├── shared/
│   │   └── main.dart
│
├── flutter-driver/            # App Conductor
│   ├── lib/
│   │   ├── features/
│   │   ├── core/
│   │   ├── shared/
│   │   └── main.dart
│
├── admin-web/                 # Panel Admin Next.js
│   ├── app/
│   ├── components/
│   └── lib/
│
├── docker-compose.yml
└── README.md
```

## 🔑 Características Principales

### 1. Sistema de Pedidos Dual

#### ON_DEMAND (Inmediato)
- Cliente crea solicitud → Sistema busca conductores online cercanos
- Envío de ofertas por "olas" (ej: primero 3km, luego 5km, luego 10km)
- Lock distribuido en Redis para evitar doble aceptación
- Expiración automática si nadie acepta en X minutos

#### SCHEDULED (Programado)
- Cliente define ventana horaria (scheduled_start_at, scheduled_end_at)
- Pre-asignación de conductor
- Sistema de disponibilidad para evitar doble reserva
- Recordatorios automáticos (T-60min, T-15min)
- Auto-rematch si conductor no confirma

### 2. Matching Inteligente

```python
# ON_DEMAND: Búsqueda geoespacial
redis.georadius("drivers:online", lat, lon, radius_km)

# SCHEDULED: Pre-asignación con bloqueo
driver_availability_blocks → Evita conflictos de horario
```

### 3. Background Workers

- **ReminderJob**: Envía notificaciones FCM antes del viaje programado
- **AutoRematchJob**: Reasigna viajes si conductor no responde
- **ExpiryJob**: Limpia pedidos expirados y libera locks
- **AvailabilityCleanupJob**: Elimina bloques de disponibilidad pasados

### 4. Modelo de Monetización Híbrido

```
Cliente ──(pago directo)──▶ Conductor
                              │
                              │ (comisión)
                              ▼
                         Wallet Virtual
                              │
                    ┌─────────┴─────────┐
                    │ Balance negativo   │
                    │ → Límite alcanzado │
                    │ → Estado LIMITED   │
                    └────────────────────┘
```

#### Suscripciones
- **FREE**: 15% comisión, viajes ilimitados
- **PRO**: 10% comisión, $X/mes
- **PREMIUM**: 5% comisión, $XX/mes, prioridad en matching

#### Wallet Transactions
```sql
-- Al completar viaje
INSERT INTO wallet_transactions (
  driver_id, 
  type = 'TRIP_COMMISSION',
  amount = -fare * commission_rate
)

-- Verificar límite
IF wallet_balance < -credit_limit THEN
  driver.status = 'LIMITED'
```

## 🗄️ Esquema de Base de Datos

### Tablas Principales

1. **users** (clientes)
2. **drivers** (conductores + wallet_balance)
3. **vehicles** (vehículos de conductores)
4. **trip_requests** (solicitudes con mode: ON_DEMAND/SCHEDULED)
5. **trip_offers** (ofertas enviadas a conductores)
6. **trips** (viajes activos/completados)
7. **wallet_transactions** (movimientos wallet)
8. **subscriptions** (planes FREE/PRO/PREMIUM)
9. **driver_availability_blocks** (reservas de horario)

## 🔐 Seguridad

- JWT tokens (Access + Refresh)
- Role-based access control (USER, DRIVER, ADMIN)
- Rate limiting
- Input validation con Pydantic
- HTTPS only en producción

## 🚀 Deploy

### Local Development
```bash
docker-compose up -d
cd backend && uvicorn app.main:app --reload
cd flutter-client && flutter run
```

### Production (Cloud Run)
```bash
# Backend
gcloud run deploy rebu-backend \
  --source . \
  --platform managed \
  --region us-central1

# Configurar Cloud SQL, Redis (Memorystore), Firestore
```

## 📱 Apps Flutter

### Cliente
- Crear pedido (inmediato/programado)
- Ver ofertas recibidas
- Tracking en tiempo real
- Chat con conductor
- Historial de viajes
- Pagos y valoraciones

### Conductor
- Ver pedidos disponibles (on-demand)
- Ver pedidos reservados (scheduled)
- Aceptar/rechazar ofertas
- Navegación GPS
- Chat con cliente
- Wallet y suscripciones

## 🧪 Testing

```bash
# Backend
pytest tests/ --cov=app

# Flutter
flutter test

# E2E
flutter drive --target=test_driver/app.dart
```

## 📄 Licencia

MIT

## 👥 Contribución

Pull requests son bienvenidos. Para cambios mayores, por favor abrir un issue primero.

## 📞 Contacto

- Email: dev@rebu.com
- Website: https://rebu.com
