import 'package:flutter/foundation.dart';
import 'api_service.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AuthService extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  bool _isAuthenticated = false;
  Map<String, dynamic>? _user;

  // ✅ isLoading ahora incluye el boot inicial
  bool _isLoading = true;

  String? _errorMessage;

  bool get isAuthenticated => _isAuthenticated;
  Map<String, dynamic>? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  AuthService() {
    _bootstrap();
  }

  /// ✅ Se ejecuta una vez al iniciar la app.
  /// Asume que ApiService().init() ya corrió en main (recomendado),
  /// pero igual funciona si no, porque re-sincroniza el estado.
  Future<void> _bootstrap() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _isAuthenticated = _apiService.isAuthenticated;

      if (_isAuthenticated) {
        // Intentar traer el usuario con el token existente
        await loadUser();

        // Si no pudo cargar usuario, lo consideramos no autenticado
        if (_user == null) {
          await logout();
        }
      }
    } catch (_) {
      // Por seguridad, si algo falla, cerrar sesión
      await logout();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // ✅ ApiService.login ya guarda tokens (access/refresh) automáticamente
      await _apiService.login(email, password);

      _isAuthenticated = true;
      await loadUser();

      // Si por alguna razón no carga usuario, fallar login
      if (_user == null) {
        _isAuthenticated = false;
        _errorMessage = 'No se pudo cargar el perfil. Intenta nuevamente';
        _isLoading = false;
        notifyListeners();
        return false;
      }

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _getErrorMessage(e);
      _isAuthenticated = false;
      _user = null;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register({
    required String email,
    required String phone,
    required String password,
    required String fullName,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _apiService.register(
        email: email,
        phone: phone,
        password: password,
        fullName: fullName,
      );

      // ✅ Register parece devolver tokens: los guardamos (como antes)
      await _apiService.setTokens(
        response['access_token'],
        response['refresh_token'],
      );

      _isAuthenticated = true;
      await loadUser();

      if (_user == null) {
        _isAuthenticated = false;
        _errorMessage = 'No se pudo cargar el perfil. Intenta nuevamente';
        _isLoading = false;
        notifyListeners();
        return false;
      }

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _getErrorMessage(e);
      _isAuthenticated = false;
      _user = null;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> loadUser() async {
    try {
      _user = await _apiService.getProfile();
      notifyListeners();
    } catch (e) {
      // Si da 401, normalmente token expiró y refresh falló -> logout
      if (e.toString().contains('401')) {
        await logout();
      }
      // si falla por otra razón, no volteamos sesión automáticamente,
      // pero dejamos el user en null para que el wrapper decida.
      _user = null;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _apiService.clearTokens();
    _isAuthenticated = false;
    _user = null;
    notifyListeners();
  }

  String _getErrorMessage(dynamic error) {
    final msg = error.toString();

    if (msg.contains('401')) {
      return 'Credenciales inválidas';
    } else if (msg.contains('400')) {
      return 'Datos inválidos. Verifica tu información';
    } else if (msg.contains('Network') || msg.contains('SocketException')) {
      return 'Error de conexión. Verifica tu internet';
    }
    return 'Error al iniciar sesión. Intenta nuevamente';
  }

  Future<bool> loginWithGoogle() async {
  _isLoading = true;
  _errorMessage = null;
  notifyListeners();

  try {
    // 1) Google Sign-In
    final googleUser = await GoogleSignIn().signIn();
    if (googleUser == null) {
      // user cancel
      _isLoading = false;
      notifyListeners();
      return false;
    }

    final googleAuth = await googleUser.authentication;
    final idToken = googleAuth.idToken;

    if (idToken == null || idToken.isEmpty) {
      throw Exception('No se pudo obtener idToken de Google');
    }

    // 2) Enviar idToken al backend -> obtener JWTs (access/refresh)
    final response = await _apiService.post('/auth/google', data: {
      'id_token': idToken,
    });

    // 3) Guardar tokens (igual que login normal)
    final access = response.data['access_token'] as String?;
    final refresh = response.data['refresh_token'] as String?;
    if (access == null || refresh == null) {
      throw Exception('Respuesta inválida del servidor');
    }

    await _apiService.setTokens(access, refresh);

    _isAuthenticated = true;
    await loadUser();

    _isLoading = false;
    notifyListeners();
    return true;
  } catch (e) {
    _errorMessage = _getErrorMessage(e);
    _isAuthenticated = false;
    _user = null;
    _isLoading = false;
    notifyListeners();
    return false;
  }
}
}