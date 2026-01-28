# Flutter Apps - Rebu Client & Driver

## 📱 Estructura de Proyecto Flutter

```
flutter-client/                          flutter-driver/
├── lib/                                 ├── lib/
│   ├── main.dart                        │   ├── main.dart
│   ├── core/                            │   ├── core/
│   │   ├── config/                      │   │   ├── config/
│   │   │   ├── api_config.dart          │   │   │   └── api_config.dart
│   │   │   └── theme.dart               │   │   │   └── theme.dart
│   │   ├── services/                    │   │   ├── services/
│   │   │   ├── api_service.dart         │   │   │   ├── api_service.dart
│   │   │   ├── auth_service.dart        │   │   │   ├── auth_service.dart
│   │   │   ├── location_service.dart    │   │   │   ├── location_service.dart
│   │   │   └── fcm_service.dart         │   │   │   ├── fcm_service.dart
│   │   └── models/                      │   │   │   └── wallet_service.dart
│   │       ├── user.dart                │   │   └── models/
│   │       ├── trip_request.dart        │   │       ├── driver.dart
│   │       ├── trip.dart                │   │       ├── offer.dart
│   │       └── location.dart            │   │       ├── trip.dart
│   ├── features/                        │   │       └── wallet.dart
│   │   ├── auth/                        │   ├── features/
│   │   │   ├── login_screen.dart        │   │   ├── auth/
│   │   │   └── register_screen.dart     │   │   │   ├── login_screen.dart
│   │   ├── home/                        │   │   │   └── register_screen.dart
│   │   │   └── home_screen.dart         │   │   ├── home/
│   │   ├── trip_create/                 │   │   │   └── home_screen.dart
│   │   │   ├── on_demand_screen.dart    │   │   ├── offers/
│   │   │   └── scheduled_screen.dart    │   │   │   ├── offers_screen.dart
│   │   ├── trip_tracking/               │   │   │   └── offer_card.dart
│   │   │   └── tracking_screen.dart     │   │   ├── scheduled/
│   │   ├── chat/                        │   │   │   ├── scheduled_trips_screen.dart
│   │   │   └── chat_screen.dart         │   │   │   └── trip_calendar.dart
│   │   └── profile/                     │   │   ├── trip_tracking/
│   │       └── profile_screen.dart      │   │   │   └── tracking_screen.dart
│   └── shared/                          │   │   ├── wallet/
│       ├── widgets/                     │   │   │   ├── wallet_screen.dart
│       │   ├── custom_button.dart       │   │   │   └── transaction_list.dart
│       │   └── loading_indicator.dart   │   │   ├── chat/
│       └── utils/                       │   │   │   └── chat_screen.dart
│           └── constants.dart           │   │   └── profile/
├── pubspec.yaml                         │   │       └── profile_screen.dart
└── android/                             │   └── shared/
    └── ios/                             │       ├── widgets/
                                         │       └── utils/
                                         ├── pubspec.yaml
                                         └── android/
                                             └── ios/
```

## 📦 Dependencies (pubspec.yaml)

```yaml
name: rebu_client  # or rebu_driver
description: Rebu - Plataforma de fletes

dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & API
  dio: ^5.4.0
  http: ^1.2.0
  
  # State Management
  provider: ^6.1.1
  # O usar: riverpod, bloc, get, etc.
  
  # Local Storage
  shared_preferences: ^2.2.2
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # Maps & Location
  google_maps_flutter: ^2.5.3
  geolocator: ^11.0.0
  geocoding: ^2.1.1
  
  # Firebase
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.9
  firebase_auth: ^4.16.0  # Optional
  cloud_firestore: ^4.14.0  # For chat
  
  # Real-time updates
  socket_io_client: ^2.0.3  # Optional WebSocket
  
  # UI Components
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0
  
  # Date & Time
  intl: ^0.19.0
  
  # Permissions
  permission_handler: ^11.2.0
  
  # Image Picker
  image_picker: ^1.0.7
  
  # QR Code (optional)
  qr_flutter: ^4.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1
```

## 🔧 Configuration Files

### API Configuration (lib/core/config/api_config.dart)

```dart
class ApiConfig {
  static const String baseUrl = 'https://api.rebu.com/api/v1';
  // Development
  // static const String baseUrl = 'http://10.0.2.2:8000/api/v1';
  
  static const String loginEndpoint = '/auth/login';
  static const String registerEndpoint = '/auth/register';
  static const String createTripEndpoint = '/trips/request';
  static const String offersEndpoint = '/trips/my-offers';
  
  static const Duration timeout = Duration(seconds: 30);
}
```

### Theme (lib/core/config/theme.dart)

```dart
import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData lightTheme = ThemeData(
    primarySwatch: Colors.blue,
    primaryColor: Color(0xFF2196F3),
    scaffoldBackgroundColor: Colors.white,
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.white,
      elevation: 0,
      iconTheme: IconThemeData(color: Colors.black),
      titleTextStyle: TextStyle(
        color: Colors.black,
        fontSize: 20,
        fontWeight: FontWeight.bold,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: Color(0xFF2196F3),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        padding: EdgeInsets.symmetric(vertical: 16),
      ),
    ),
  );
}
```

## 🌐 API Service (lib/core/services/api_service.dart)

```dart
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  
  late Dio _dio;
  String? _accessToken;
  
  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.timeout,
      receiveTimeout: ApiConfig.timeout,
    ));
    
    // Interceptor for auth token
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Token expired, try refresh
          await _refreshToken();
          return handler.resolve(await _retry(error.requestOptions));
        }
        return handler.next(error);
      },
    ));
    
    _loadToken();
  }
  
  Future<void> _loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString('access_token');
  }
  
  Future<void> setToken(String token) async {
    _accessToken = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }
  
  Future<void> _refreshToken() async {
    // Implement token refresh logic
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString('refresh_token');
    
    if (refreshToken != null) {
      try {
        final response = await _dio.post('/auth/refresh', 
          data: {'refresh_token': refreshToken}
        );
        await setToken(response.data['access_token']);
      } catch (e) {
        // Logout user
        await clearToken();
      }
    }
  }
  
  Future<Response> _retry(RequestOptions requestOptions) async {
    return _dio.request(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: Options(
        method: requestOptions.method,
        headers: requestOptions.headers,
      ),
    );
  }
  
  Future<void> clearToken() async {
    _accessToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
  }
  
  // API Methods
  Future<Response> get(String path, {Map<String, dynamic>? queryParams}) {
    return _dio.get(path, queryParameters: queryParams);
  }
  
  Future<Response> post(String path, {dynamic data}) {
    return _dio.post(path, data: data);
  }
  
  Future<Response> put(String path, {dynamic data}) {
    return _dio.put(path, data: data);
  }
  
  Future<Response> delete(String path) {
    return _dio.delete(path);
  }
}
```

## 📍 Location Service (lib/core/services/location_service.dart)

```dart
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';

class LocationService {
  static Future<bool> requestPermission() async {
    final status = await Permission.location.request();
    return status.isGranted;
  }
  
  static Future<Position?> getCurrentLocation() async {
    bool hasPermission = await requestPermission();
    
    if (!hasPermission) {
      return null;
    }
    
    try {
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
    } catch (e) {
      print('Error getting location: $e');
      return null;
    }
  }
  
  static Stream<Position> getLocationStream() {
    return Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    );
  }
}
```

## 🔔 FCM Service (lib/core/services/fcm_service.dart)

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class FCMService {
  static final FCMService _instance = FCMService._internal();
  factory FCMService() => _instance;
  
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
    FlutterLocalNotificationsPlugin();
  
  FCMService._internal();
  
  Future<void> initialize() async {
    // Request permission
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('FCM permission granted');
      
      // Get token
      String? token = await _fcm.getToken();
      print('FCM Token: $token');
      
      // TODO: Send token to backend
      
      // Listen to messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
    }
    
    // Initialize local notifications
    const initSettings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      iOS: DarwinInitializationSettings(),
    );
    await _localNotifications.initialize(initSettings);
  }
  
  void _handleForegroundMessage(RemoteMessage message) {
    print('Received message: ${message.data}');
    
    // Show local notification
    _showNotification(
      message.notification?.title ?? 'Rebu',
      message.notification?.body ?? '',
    );
  }
  
  void _handleNotificationTap(RemoteMessage message) {
    print('Notification tapped: ${message.data}');
    // Navigate to appropriate screen based on message.data['type']
  }
  
  Future<void> _showNotification(String title, String body) async {
    const androidDetails = AndroidNotificationDetails(
      'rebu_channel',
      'Rebu Notifications',
      importance: Importance.high,
      priority: Priority.high,
    );
    
    const iosDetails = DarwinNotificationDetails();
    
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.show(0, title, body, details);
  }
}
```

## 🚗 Driver-Specific: Location Updates Service

```dart
// For Driver App - Send location updates to backend
class DriverLocationService {
  final ApiService _api = ApiService();
  StreamSubscription<Position>? _locationSubscription;
  
  void startLocationUpdates() {
    _locationSubscription = LocationService.getLocationStream().listen((position) {
      _updateLocationOnServer(position.latitude, position.longitude);
    });
  }
  
  void stopLocationUpdates() {
    _locationSubscription?.cancel();
  }
  
  Future<void> _updateLocationOnServer(double lat, double lon) async {
    try {
      await _api.post('/drivers/location', data: {
        'lat': lat,
        'lon': lon,
      });
    } catch (e) {
      print('Error updating location: $e');
    }
  }
}
```

## 📱 Example Screens

### ON_DEMAND Trip Creation (Client App)

```dart
// lib/features/trip_create/on_demand_screen.dart
class OnDemandTripScreen extends StatefulWidget {
  @override
  _OnDemandTripScreenState createState() => _OnDemandTripScreenState();
}

class _OnDemandTripScreenState extends State<OnDemandTripScreen> {
  final ApiService _api = ApiService();
  
  Position? _currentLocation;
  String _pickupAddress = '';
  String _dropoffAddress = '';
  
  @override
  void initState() {
    super.initState();
    _getCurrentLocation();
  }
  
  Future<void> _getCurrentLocation() async {
    final position = await LocationService.getCurrentLocation();
    setState(() => _currentLocation = position);
  }
  
  Future<void> _createTrip() async {
    try {
      final response = await _api.post('/trips/request/on-demand', data: {
        'pickup': {
          'address': _pickupAddress,
          'lat': _currentLocation!.latitude,
          'lon': _currentLocation!.longitude,
        },
        'dropoff': {
          'address': _dropoffAddress,
          'lat': -31.4201, // example
          'lon': -64.1888,
        },
        'estimated_fare': 1500.0,
      });
      
      // Navigate to waiting screen
      Navigator.pushNamed(context, '/trip-waiting', 
        arguments: response.data['id']
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error creating trip: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Nueva Solicitud')),
      body: Column(
        children: [
          // Google Map Widget
          Expanded(
            child: GoogleMap(
              initialCameraPosition: CameraPosition(
                target: LatLng(
                  _currentLocation?.latitude ?? -31.4201,
                  _currentLocation?.longitude ?? -64.1888,
                ),
                zoom: 14,
              ),
            ),
          ),
          // Form
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  decoration: InputDecoration(labelText: 'Dirección de recogida'),
                  onChanged: (value) => _pickupAddress = value,
                ),
                SizedBox(height: 16),
                TextField(
                  decoration: InputDecoration(labelText: 'Dirección de entrega'),
                  onChanged: (value) => _dropoffAddress = value,
                ),
                SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _createTrip,
                  child: Text('Solicitar Flete'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size(double.infinity, 50),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

### Offers Screen (Driver App)

```dart
// lib/features/offers/offers_screen.dart
class OffersScreen extends StatefulWidget {
  @override
  _OffersScreenState createState() => _OffersScreenState();
}

class _OffersScreenState extends State<OffersScreen> {
  final ApiService _api = ApiService();
  List<dynamic> _offers = [];
  bool _loading = true;
  
  @override
  void initState() {
    super.initState();
    _loadOffers();
  }
  
  Future<void> _loadOffers() async {
    try {
      final response = await _api.get('/trips/my-offers', 
        queryParams: {'status': 'PENDING'}
      );
      setState(() {
        _offers = response.data['items'];
        _loading = false;
      });
    } catch (e) {
      print('Error loading offers: $e');
      setState(() => _loading = false);
    }
  }
  
  Future<void> _acceptOffer(int offerId) async {
    try {
      await _api.post('/trips/offer/$offerId/accept');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('¡Oferta aceptada!')),
      );
      _loadOffers();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Center(child: CircularProgressIndicator());
    }
    
    if (_offers.isEmpty) {
      return Center(
        child: Text('No hay ofertas disponibles'),
      );
    }
    
    return ListView.builder(
      itemCount: _offers.length,
      itemBuilder: (context, index) {
        final offer = _offers[index];
        return Card(
          margin: EdgeInsets.all(8),
          child: ListTile(
            title: Text('Flete: \$${offer['offered_fare']}'),
            subtitle: Text(
              'De: ${offer['trip_request']['pickup_address']}\n'
              'A: ${offer['trip_request']['dropoff_address']}'
            ),
            trailing: ElevatedButton(
              onPressed: () => _acceptOffer(offer['id']),
              child: Text('Aceptar'),
            ),
          ),
        );
      },
    );
  }
}
```

## 🚀 Main Entry Point

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'core/config/theme.dart';
import 'core/services/fcm_service.dart';
import 'features/auth/login_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp();
  
  // Initialize FCM
  await FCMService().initialize();
  
  runApp(RebuApp());
}

class RebuApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rebu Client', // or 'Rebu Driver'
      theme: AppTheme.lightTheme,
      home: LoginScreen(),
      // Define routes
      routes: {
        '/home': (context) => HomeScreen(),
        '/on-demand': (context) => OnDemandTripScreen(),
        '/scheduled': (context) => ScheduledTripScreen(),
        // ... more routes
      },
    );
  }
}
```

## 📝 Notes

1. **State Management**: Esta guía usa setState(), pero para apps grandes considere Provider, Riverpod o BLoC
2. **Error Handling**: Implemente manejo robusto de errores en producción
3. **Testing**: Agregue unit tests y widget tests
4. **Offline Support**: Considere usar Hive o SQLite para cache offline
5. **Real-time Updates**: Para tracking en tiempo real, use WebSockets o Firestore listeners

## 🔐 Security

- Nunca almacene tokens en texto plano
- Use Flutter Secure Storage para datos sensibles
- Implemente certificate pinning para producción
- Valide entrada del usuario en cliente y servidor
