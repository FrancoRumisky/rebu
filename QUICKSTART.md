# 🚀 Rebu - Guía de Inicio Rápido

## ⚡ Quick Start (5 minutos)

### 1. Iniciar servicios locales

```bash
cd rebu-project

# Iniciar PostgreSQL y Redis con Docker Compose
docker-compose up -d

# Verificar que están corriendo
docker-compose ps
```

### 2. Configurar Backend

```bash
cd backend

# Crear entorno virtual Python
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
cat > .env << EOF
POSTGRES_USER=rebu
POSTGRES_PASSWORD=rebu_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rebu_db

REDIS_HOST=localhost
REDIS_PORT=6379

SECRET_KEY=$(openssl rand -hex 32)
ENABLE_BACKGROUND_WORKERS=true
EOF

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend corriendo en: http://localhost:8000

Documentación API: http://localhost:8000/api/v1/docs

### 3. Probar API con cURL

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/v1/auth/register/user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@test.com",
    "phone": "+5493511234567",
    "password": "password123",
    "full_name": "Usuario Test"
  }'

# Guardar el access_token de la respuesta

# Registrar conductor
curl -X POST http://localhost:8000/api/v1/auth/register/driver \
  -H "Content-Type: application/json" \
  -d '{
    "email": "conductor@test.com",
    "phone": "+5493517654321",
    "password": "password123",
    "full_name": "Conductor Test",
    "license_number": "ABC123456",
    "license_expiry_date": "2026-12-31T00:00:00"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@test.com",
    "password": "password123"
  }'

# Crear viaje ON_DEMAND
curl -X POST http://localhost:8000/api/v1/trips/request/on-demand \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "pickup": {
      "address": "Av. Colón 123, Córdoba",
      "lat": -31.4201,
      "lon": -64.1888
    },
    "dropoff": {
      "address": "Nueva Córdoba, Córdoba",
      "lat": -31.4273,
      "lon": -64.1886
    },
    "estimated_fare": 1500.0,
    "cargo_description": "Caja pequeña"
  }'
```

### 4. Configurar Flutter (Cliente)

```bash
cd flutter-client

# Instalar dependencias
flutter pub get

# Crear archivo de configuración
mkdir -p lib/core/config
cat > lib/core/config/api_config.dart << 'EOF'
class ApiConfig {
  // Para Android Emulator
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';
  
  // Para iOS Simulator
  // static const String baseUrl = 'http://localhost:8000/api/v1';
  
  // Para dispositivo físico (usar IP local)
  // static const String baseUrl = 'http://192.168.1.XXX:8000/api/v1';
}
EOF

# Ejecutar app
flutter run
```

### 5. Configurar Flutter (Conductor)

```bash
cd flutter-driver

# Mismo proceso que flutter-client
flutter pub get
flutter run
```

## 📱 Flujo de Prueba Completo

### Escenario 1: Viaje Inmediato (ON_DEMAND)

1. **App Cliente**: Usuario crea solicitud de flete
2. **Backend**: Sistema busca conductores cercanos en Redis
3. **App Conductor**: Conductor recibe notificación push
4. **App Conductor**: Conductor acepta oferta
5. **Backend**: Crea Trip y notifica al usuario
6. **App Cliente**: Usuario ve que conductor fue asignado
7. **App Conductor**: Conductor actualiza estado (En camino → Llegó → En progreso)
8. **App Conductor**: Conductor completa viaje
9. **Backend**: Cobra comisión automáticamente

### Escenario 2: Viaje Programado (SCHEDULED)

1. **App Cliente**: Usuario programa flete para mañana 10am
2. **Admin Panel**: Admin pre-asigna conductor disponible
3. **Backend**: Crea bloque de disponibilidad
4. **Backend**: ReminderJob envía notificación T-60min
5. **Backend**: ReminderJob envía notificación T-15min
6. **Resto igual que ON_DEMAND**

## 🔧 Comandos Útiles

```bash
# Ver logs de Docker
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Detener todo
docker-compose down

# Ver base de datos
docker exec -it rebu_postgres psql -U rebu -d rebu_db

# Ver Redis
docker exec -it rebu_redis redis-cli

# Crear nueva migración
cd backend
alembic revision --autogenerate -m "Add new field"
alembic upgrade head

# Ejecutar tests
cd backend
pytest tests/ -v

# Flutter hot reload
# Presionar 'r' en la terminal donde corre flutter run
```

## 🐛 Troubleshooting

### Backend no inicia

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps

# Verificar logs
docker-compose logs postgres

# Recrear base de datos
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

### Flutter no conecta al backend

```bash
# Android Emulator: Usar 10.0.2.2
# iOS Simulator: Usar localhost
# Dispositivo físico: Usar IP local de tu computadora

# Obtener IP local (Linux/Mac)
ifconfig | grep "inet "

# Verificar que backend está escuchando en 0.0.0.0
# No en 127.0.0.1 (solo localhost)
```

### Redis connection failed

```bash
# Verificar que Redis está corriendo
docker exec -it rebu_redis redis-cli ping
# Debe responder: PONG

# Si no responde, reiniciar
docker-compose restart redis
```

### Migraciones fallan

```bash
# Resetear migraciones (⚠️ Elimina datos)
cd backend
alembic downgrade base
alembic upgrade head

# O recrear base de datos
docker-compose down -v
docker-compose up -d postgres
sleep 5
alembic upgrade head
```

## 📚 Próximos Pasos

1. **Configurar Firebase**: 
   - Crear proyecto en Firebase Console
   - Descargar google-services.json (Android) y GoogleService-Info.plist (iOS)
   - Configurar FCM para notificaciones push

2. **Implementar Chat**:
   - Usar Firestore para mensajes en tiempo real
   - Ver FLUTTER_GUIDE.md para detalles

3. **Agregar Mapas**:
   - Obtener API Key de Google Maps
   - Configurar en Android/iOS

4. **Deploy a Producción**:
   - Ver DEPLOYMENT_GUIDE.md
   - Configurar Cloud Run, Cloud SQL, Memorystore

5. **Admin Panel**:
   - Crear app Next.js
   - Conectar con backend API
   - Implementar dashboard, aprobación de conductores, gestión de pagos

## 🎯 Checklist de Implementación

- [x] Backend FastAPI con FastAPI
- [x] Modelos SQLAlchemy (Users, Drivers, Trips, etc.)
- [x] Sistema de matching ON_DEMAND y SCHEDULED
- [x] Wallet virtual con comisiones
- [x] Background workers (reminders, expiry)
- [x] Redis para geolocalización y locks
- [x] Migraciones Alembic
- [x] Documentación OpenAPI
- [ ] Flutter Client app (estructura y ejemplos)
- [ ] Flutter Driver app (estructura y ejemplos)
- [ ] Firebase FCM configurado
- [ ] Google Maps integrado
- [ ] Chat con Firestore
- [ ] Admin Panel Next.js
- [ ] Tests unitarios e integración
- [ ] Deploy a Cloud Run
- [ ] CI/CD pipeline
- [ ] Monitoring y alertas

## 💡 Tips de Desarrollo

1. **Usa Swagger UI** (`/api/v1/docs`) para probar endpoints fácilmente
2. **Redis Desktop Manager** para ver datos en Redis visualmente
3. **Postman** para guardar colecciones de requests
4. **Flutter DevTools** para debugging de apps móviles
5. **pgAdmin** para gestión visual de PostgreSQL

## 📞 Soporte

¿Preguntas? ¿Problemas? 

- 📖 Leer documentación completa en README.md
- 🐛 Revisar Troubleshooting en esta guía
- 💬 Contactar: dev@rebu.com

¡Feliz desarrollo! 🚀
