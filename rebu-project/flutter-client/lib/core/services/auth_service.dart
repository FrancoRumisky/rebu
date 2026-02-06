import 'package:flutter/foundation.dart';
import 'api_service.dart';

class AuthService extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  bool _isAuthenticated = false;
  Map<String, dynamic>? _user;
  bool _isLoading = false;
  String? _errorMessage;
  
  bool get isAuthenticated => _isAuthenticated;
  Map<String, dynamic>? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  
  AuthService() {
    _checkAuthStatus();
  }
  
  Future<void> _checkAuthStatus() async {
    _isAuthenticated = _apiService.isAuthenticated;
    if (_isAuthenticated) {
      await loadUser();
    }
    notifyListeners();
  }
  
  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final response = await _apiService.login(email, password);
      
      await _apiService.setTokens(
        response['access_token'],
        response['refresh_token'],
      );
      
      _isAuthenticated = true;
      await loadUser();
      
      _isLoading = false;
      notifyListeners();
      return true;
      
    } catch (e) {
      _errorMessage = _getErrorMessage(e);
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
      
      await _apiService.setTokens(
        response['access_token'],
        response['refresh_token'],
      );
      
      _isAuthenticated = true;
      await loadUser();
      
      _isLoading = false;
      notifyListeners();
      
      return true;
      
    } catch (e) {
      _errorMessage = _getErrorMessage(e);
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
      print('Error loading user: $e');
    }
  }
  
  Future<void> logout() async {
    await _apiService.clearTokens();
    _isAuthenticated = false;
    _user = null;
    notifyListeners();
  }
  
  String _getErrorMessage(dynamic error) {
    if (error.toString().contains('401')) {
      return 'Credenciales inválidas';
    } else if (error.toString().contains('400')) {
      return 'Datos inválidos. Verifica tu información';
    } else if (error.toString().contains('Network')) {
      return 'Error de conexión. Verifica tu internet';
    }
    return 'Error al iniciar sesión. Intenta nuevamente';
  }
}
