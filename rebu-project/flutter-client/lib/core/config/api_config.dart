class ApiConfig {
  // Backend URL - Cambiar según el entorno
  
  // Para Android Emulator
  //static const String baseUrl = 'http://10.0.2.2:8000/api/v1';
  
  // Para iOS Simulator
  // static const String baseUrl = 'http://localhost:8000/api/v1';
  
  // Para dispositivo físico (usar tu IP local)
  static const String baseUrl = 'http://192.168.100.5:8000/api/v1';
  
  // Producción
  // static const String baseUrl = 'https://api.rebu.com/api/v1';
  
  // Endpoints
  static const String loginEndpoint = '/auth/login';
  static const String registerUserEndpoint = '/auth/register/user';
  static const String createOnDemandTripEndpoint = '/trips/request/on-demand';
  static const String createScheduledTripEndpoint = '/trips/request/scheduled';
  static const String myTripsEndpoint = '/trips/my-requests';
  static const String tripDetailsEndpoint = '/trips/request';
  static const String updateFcmTokenEndpoint = '/auth/fcm-token';
  static const String profileEndpoint = '/users/me';
  static const String tripsHistoryEndpoint = '/users/trips';
  
  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
}
