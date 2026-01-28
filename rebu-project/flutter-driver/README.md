# Rebu Conductor - Flutter App

Aplicación móvil para conductores de Rebu.

## Estructura

```
lib/
├── core/
│   ├── config/       # Configuración (API, Theme)
│   ├── services/     # Servicios (API, Auth, Location, FCM)
│   └── models/       # Modelos de datos
├── features/
│   ├── auth/         # Login, Register ✅
│   ├── home/         # Pantalla principal ✅
│   ├── offers/       # Ver y aceptar ofertas
│   ├── scheduled/    # Viajes programados
│   ├── wallet/       # Wallet y transacciones
│   ├── trip_tracking/# Tracking activo
│   └── profile/      # Perfil de conductor
└── shared/           # Widgets compartidos
```

## Instalación

```bash
flutter pub get
flutter run
```

Ver FLUTTER_GUIDE.md para implementación completa.
