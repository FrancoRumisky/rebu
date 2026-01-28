import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'api_service.dart';

// Top-level function for background messages
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  print('Handling background message: ${message.messageId}');
}

class FCMService {
  static final FCMService _instance = FCMService._internal();
  factory FCMService() => _instance;
  
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  final ApiService _apiService = ApiService();
  
  String? _fcmToken;
  
  FCMService._internal();
  
  Future<void> initialize() async {
    // Request permission
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('✅ FCM permission granted');
      
      // Get token
      _fcmToken = await _fcm.getToken();
      print('FCM Token: $_fcmToken');
      
      // Send token to backend
      if (_fcmToken != null && _apiService.isAuthenticated) {
        await _sendTokenToBackend(_fcmToken!);
      }
      
      // Listen to token refresh
      _fcm.onTokenRefresh.listen((newToken) {
        _fcmToken = newToken;
        _sendTokenToBackend(newToken);
      });
      
      // Handle foreground messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      
      // Handle background messages
      FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
      
      // Handle notification tap
      FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
      
      // Check if app was opened from notification
      RemoteMessage? initialMessage = await _fcm.getInitialMessage();
      if (initialMessage != null) {
        _handleNotificationTap(initialMessage);
      }
    } else {
      print('⚠️ FCM permission denied');
    }
    
    // Initialize local notifications
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    
    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (details) {
        print('Local notification tapped: ${details.payload}');
      },
    );
  }
  
  Future<void> _sendTokenToBackend(String token) async {
    try {
      await _apiService.updateFcmToken(token);
      print('✅ FCM token sent to backend');
    } catch (e) {
      print('❌ Error sending FCM token: $e');
    }
  }
  
  void _handleForegroundMessage(RemoteMessage message) {
    print('📩 Foreground message: ${message.notification?.title}');
    
    // Show local notification
    _showNotification(
      message.notification?.title ?? 'Rebu',
      message.notification?.body ?? '',
      payload: message.data.toString(),
    );
  }
  
  void _handleNotificationTap(RemoteMessage message) {
    print('🔔 Notification tapped: ${message.data}');
    
    // Navigate based on notification type
    String? type = message.data['type'];
    
    switch (type) {
      case 'TRIP_MATCHED':
        // Navigate to trip tracking
        break;
      case 'TRIP_STATUS_UPDATE':
        // Navigate to trip details
        break;
      case 'TRIP_EXPIRED':
        // Show dialog
        break;
      default:
        print('Unknown notification type: $type');
    }
  }
  
  Future<void> _showNotification(
    String title, 
    String body, 
    {String? payload}
  ) async {
    const androidDetails = AndroidNotificationDetails(
      'rebu_channel',
      'Rebu Notifications',
      channelDescription: 'Notificaciones de Rebu',
      importance: Importance.high,
      priority: Priority.high,
      showWhen: true,
    );
    
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.show(
      DateTime.now().millisecond,
      title,
      body,
      details,
      payload: payload,
    );
  }
  
  String? get token => _fcmToken;
}
