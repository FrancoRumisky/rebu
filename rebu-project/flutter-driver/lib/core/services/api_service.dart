import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  
  late Dio _dio;
  String? _accessToken;
  String? _refreshToken;
  
  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    ));
    
    // Request interceptor
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
          final refreshed = await _refreshToken();
          if (refreshed) {
            return handler.resolve(await _retry(error.requestOptions));
          }
        }
        return handler.next(error);
      },
    ));
    
    _loadTokens();
  }
  
  Future<void> _loadTokens() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString('access_token');
    _refreshToken = prefs.getString('refresh_token');
  }
  
  Future<void> setTokens(String accessToken, String refreshToken) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', accessToken);
    await prefs.setString('refresh_token', refreshToken);
  }
  
  Future<bool> _refreshToken() async {
    if (_refreshToken == null) return false;
    
    try {
      final response = await _dio.post('/auth/refresh', 
        data: {'refresh_token': _refreshToken}
      );
      
      await setTokens(
        response.data['access_token'],
        response.data['refresh_token'],
      );
      return true;
    } catch (e) {
      await clearTokens();
      return false;
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
  
  Future<void> clearTokens() async {
    _accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
  }
  
  bool get isAuthenticated => _accessToken != null;
  
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
  
  // Specific API calls
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await post(ApiConfig.loginEndpoint, data: {
      'email': email,
      'password': password,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> register({
    required String email,
    required String phone,
    required String password,
    required String fullName,
  }) async {
    final response = await post(ApiConfig.registerUserEndpoint, data: {
      'email': email,
      'phone': phone,
      'password': password,
      'full_name': fullName,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> createOnDemandTrip({
    required Map<String, dynamic> pickup,
    required Map<String, dynamic> dropoff,
    required double estimatedFare,
    String? cargoDescription,
    double? cargoWeightKg,
  }) async {
    final response = await post(ApiConfig.createOnDemandTripEndpoint, data: {
      'pickup': pickup,
      'dropoff': dropoff,
      'estimated_fare': estimatedFare,
      'cargo_description': cargoDescription,
      'cargo_weight_kg': cargoWeightKg,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> createScheduledTrip({
    required Map<String, dynamic> pickup,
    required Map<String, dynamic> dropoff,
    required double estimatedFare,
    required String scheduledStartAt,
    required String scheduledEndAt,
    String? cargoDescription,
  }) async {
    final response = await post(ApiConfig.createScheduledTripEndpoint, data: {
      'pickup': pickup,
      'dropoff': dropoff,
      'estimated_fare': estimatedFare,
      'scheduled_start_at': scheduledStartAt,
      'scheduled_end_at': scheduledEndAt,
      'cargo_description': cargoDescription,
    });
    return response.data;
  }
  
  Future<List<dynamic>> getMyTrips({String? status}) async {
    final response = await get(
      ApiConfig.myTripsEndpoint,
      queryParams: status != null ? {'status': status} : null,
    );
    return response.data['items'];
  }
  
  Future<Map<String, dynamic>> getTripDetails(int tripRequestId) async {
    final response = await get('${ApiConfig.tripDetailsEndpoint}/$tripRequestId');
    return response.data;
  }
  
  Future<void> updateFcmToken(String fcmToken) async {
    await post(ApiConfig.updateFcmTokenEndpoint, data: {
      'fcm_token': fcmToken,
    });
  }
  
  Future<Map<String, dynamic>> getProfile() async {
    final response = await get(ApiConfig.profileEndpoint);
    return response.data;
  }
}
