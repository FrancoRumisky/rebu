import 'package:dio/dio.dart';
import '../config/api_config.dart';
import 'token_storage.dart'; // ✅ nuevo
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';


class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  late Dio _dio;
  final TokenStorage _tokenStorage = TokenStorage(); // ✅ nuevo

  String? _accessToken;
  String? _refreshToken;

  bool _isRefreshing = false; // ✅ nuevo: evita múltiples refresh a la vez

  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    // Interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (_accessToken != null && _accessToken!.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        final status = error.response?.statusCode;
        final requestOptions = error.requestOptions;

        // Evitar loop si el 401 viene del refresh endpoint
        final isRefreshCall = requestOptions.path.contains('/auth/refresh');

        if (status == 401 && !isRefreshCall) {
          final refreshed = await _refreshAccessToken();
          if (refreshed) {
            final response = await _retry(requestOptions);
            return handler.resolve(response);
          }
        }

        return handler.next(error);
      },
    ));
  }

  // ✅ IMPORTANTE: llamar esto al iniciar la app (main/splash) antes de usar ApiService
  Future<void> init() async {
    _accessToken = await _tokenStorage.readAccessToken();
    _refreshToken = await _tokenStorage.readRefreshToken();
  }

  Future<void> setTokens(String accessToken, String refreshToken) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;

    await _tokenStorage.saveTokens(
      accessToken: accessToken,
      refreshToken: refreshToken,
    );
  }

  Future<bool> _refreshAccessToken() async {
    if (_isRefreshing) return false;
    if (_refreshToken == null || _refreshToken!.isEmpty) return false;

    _isRefreshing = true;
    try {
      // ✅ usar un Dio limpio sin interceptors para refresh
      final refreshDio = Dio(BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: ApiConfig.connectTimeout,
        receiveTimeout: ApiConfig.receiveTimeout,
        headers: {'Content-Type': 'application/json'},
      ));

      final response = await refreshDio.post(
        '/auth/refresh',
        data: {'refresh_token': _refreshToken},
      );

      final newAccess = response.data['access_token'] as String?;
      final newRefresh = response.data['refresh_token'] as String?;

      if (newAccess == null || newAccess.isEmpty) {
        await clearTokens();
        return false;
      }

      // ✅ Guardar access token nuevo
      _accessToken = newAccess;
      await _tokenStorage.saveAccessToken(newAccess);

      // ✅ SOLO actualizar refresh si el backend lo devuelve (rotación)
      if (newRefresh != null && newRefresh.isNotEmpty) {
        _refreshToken = newRefresh;
        await _tokenStorage.saveRefreshToken(newRefresh);
      }

      return true;
    } catch (_) {
      await clearTokens();
      return false;
    } finally {
      _isRefreshing = false;
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
        contentType: requestOptions.contentType,
        responseType: requestOptions.responseType,
        followRedirects: requestOptions.followRedirects,
        validateStatus: requestOptions.validateStatus,
        receiveDataWhenStatusError: requestOptions.receiveDataWhenStatusError,
      ),
    );
  }

  Future<void> clearTokens() async {
    _accessToken = null;
    _refreshToken = null;
    await _tokenStorage.clear();
  }

  bool get isAuthenticated =>
      _accessToken != null && _accessToken!.isNotEmpty;

  // =========================
  // API Methods
  // =========================
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

  // =========================
  // Specific API calls
  // =========================
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await post(ApiConfig.loginEndpoint, data: {
      'email': email,
      'password': password,
    });

    // ✅ Si el backend devuelve tokens, los guardamos automáticamente
    final access = response.data['access_token'] as String?;
    final refresh = response.data['refresh_token'] as String?;
    if (access != null && refresh != null) {
      await setTokens(access, refresh);
    }

    return response.data;
  }

  Future<Map<String, dynamic>> loginWithGoogle() async {
  try {

    print("holaaa");
    final googleSignIn = GoogleSignIn(
  scopes: <String>[
    'email',
    'profile',
    'openid',
  ],
);

final googleUser = await googleSignIn.signIn();
    if (googleUser == null) {
      throw Exception('LOGIN_CANCELLED');
    }

    final googleAuth = await googleUser.authentication;
    final idToken = googleAuth.idToken;
    final accessToken = googleAuth.accessToken;

    if (idToken == null || accessToken == null) {
      throw Exception('GOOGLE_TOKEN_MISSING');
    }

    final credential = GoogleAuthProvider.credential(
      idToken: idToken,
      accessToken: accessToken,
    );

    // Esto hace que aparezca en Firebase Auth (si está todo configurado)
    await FirebaseAuth.instance.signInWithCredential(credential);

    // ✅ OJO: sin slash inicial para respetar /api/v1 del baseUrl
    final response = await post('auth/google', data: {
      'id_token': idToken,
    });

    return response.data as Map<String, dynamic>;
  } on FirebaseAuthException catch (e) {
    // errores típicos: account-exists-with-different-credential, invalid-credential, etc.
    throw Exception('FIREBASE_AUTH_${e.code}');
  } catch (e) {
    // log útil mientras debug
    // ignore: avoid_print
    print('loginWithGoogle error: $e');
    rethrow;
  }
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

