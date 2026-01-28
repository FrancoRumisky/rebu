# Rebu Cliente - Flutter App

Aplicación móvil para clientes de Rebu.

## Estructura

```
lib/
├── core/
│   ├── config/       # Configuración (API, Theme)
│   ├── services/     # Servicios (API, Auth, Location, FCM)
│   └── models/       # Modelos de datos
├── features/
│   ├── auth/         # Login, Register
│   ├── home/         # Pantalla principal ✅
│   ├── trip_create/  # Crear viaje (ON_DEMAND/SCHEDULED)
│   ├── trip_tracking/# Rastreo en tiempo real
│   ├── chat/         # Chat con conductor
│   └── profile/      # Perfil de usuario
└── shared/           # Widgets y utilidades compartidas
```

## Instalación

```bash
flutter pub get
flutter run
```

## Configurar URL del Backend

Editar `lib/core/config/api_config.dart`:
- Android Emulator: `http://10.0.2.2:8000/api/v1`
- iOS Simulator: `http://localhost:8000/api/v1`
- Dispositivo físico: `http://TU_IP_LOCAL:8000/api/v1`

## Firebase

1. Agregar `google-services.json` en `android/app/`
2. Agregar `GoogleService-Info.plist` en `ios/Runner/`

Ver FLUTTER_GUIDE.md para más detalles.
