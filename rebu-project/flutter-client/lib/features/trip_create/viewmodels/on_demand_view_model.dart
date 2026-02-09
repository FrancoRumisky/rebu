import 'package:flutter/foundation.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/location_service.dart';

class OnDemandViewModel extends ChangeNotifier {
  final ApiService _api;
  OnDemandViewModel({ApiService? api}) : _api = api ?? ApiService();

  bool _isLoading = false;
  String? _error;

  bool get isLoading => _isLoading;
  String? get error => _error;

  // Form state
  String pickupAddress = '';
  double? pickupLat;
  double? pickupLon;

  String dropoffAddress = '';
  double? dropoffLat;
  double? dropoffLon;

  String? cargoDescription;
  double? cargoWeightKg;

  double? _distanceKm;
  double? _estimatedFare;

  double? get distanceKm => _distanceKm;
  double? get estimatedFare => _estimatedFare;

  // Reglas simples de tarifa (MVP)
  static const double baseFare = 1500; // ajustable
  static const double perKm = 700;     // ajustable

  bool get canSubmit =>
      pickupLat != null &&
      pickupLon != null &&
      dropoffLat != null &&
      dropoffLon != null &&
      pickupAddress.trim().isNotEmpty &&
      dropoffAddress.trim().isNotEmpty &&
      (_estimatedFare ?? 0) > 0;

  Future<void> init() async {
    // Importante si tu ApiService requiere init() para cargar tokens
    // (si en tu versión original no lo requiere, no pasa nada)
    try {
      await _api.init();
    } catch (_) {}
  }

  Future<void> useMyLocationAsPickup() async {
    _setLoading(true);
    _error = null;

    try {
      final pos = await LocationService.getCurrentLocation();
      if (pos == null) {
        _error = 'No se pudo obtener tu ubicación. Activá GPS y permisos.';
        _setLoading(false);
        return;
      }

      pickupLat = pos.latitude;
      pickupLon = pos.longitude;

      final addr = await LocationService.getAddressFromCoordinates(
        pickupLat!,
        pickupLon!,
      );

      pickupAddress = addr ?? 'Mi ubicación';
      _recalculateFareIfPossible();
    } catch (e) {
      _error = 'Error obteniendo ubicación';
    }

    _setLoading(false);
  }

  Future<void> setPickupFromAddress(String address) async {
    pickupAddress = address;
    await _geocodePickup();
  }

  Future<void> setDropoffFromAddress(String address) async {
    dropoffAddress = address;
    await _geocodeDropoff();
  }

  Future<void> _geocodePickup() async {
    _error = null;

    if (pickupAddress.trim().isEmpty) {
      pickupLat = null;
      pickupLon = null;
      _recalculateFareIfPossible();
      notifyListeners();
      return;
    }

    _setLoading(true);
    try {
      final locations =
          await LocationService.getCoordinatesFromAddress(pickupAddress);
      if (locations == null || locations.isEmpty) {
        _error = 'No encontramos el origen. Probá con otra dirección.';
        pickupLat = null;
        pickupLon = null;
      } else {
        pickupLat = locations.first.latitude;
        pickupLon = locations.first.longitude;
      }
      _recalculateFareIfPossible();
    } catch (_) {
      _error = 'Error al buscar el origen';
    }
    _setLoading(false);
  }

  Future<void> _geocodeDropoff() async {
    _error = null;

    if (dropoffAddress.trim().isEmpty) {
      dropoffLat = null;
      dropoffLon = null;
      _recalculateFareIfPossible();
      notifyListeners();
      return;
    }

    _setLoading(true);
    try {
      final locations =
          await LocationService.getCoordinatesFromAddress(dropoffAddress);
      if (locations == null || locations.isEmpty) {
        _error = 'No encontramos el destino. Probá con otra dirección.';
        dropoffLat = null;
        dropoffLon = null;
      } else {
        dropoffLat = locations.first.latitude;
        dropoffLon = locations.first.longitude;
      }
      _recalculateFareIfPossible();
    } catch (_) {
      _error = 'Error al buscar el destino';
    }
    _setLoading(false);
  }

  void _recalculateFareIfPossible() {
    if (pickupLat == null ||
        pickupLon == null ||
        dropoffLat == null ||
        dropoffLon == null) {
      _distanceKm = null;
      _estimatedFare = null;
      notifyListeners();
      return;
    }

    final meters = LocationService.calculateDistance(
      pickupLat!,
      pickupLon!,
      dropoffLat!,
      dropoffLon!,
    );

    _distanceKm = (meters / 1000.0);
    _estimatedFare = baseFare + (_distanceKm! * perKm);
    notifyListeners();
  }

  Future<Map<String, dynamic>?> submit() async {
    if (!canSubmit) {
      _error = 'Completá origen y destino primero.';
      notifyListeners();
      return null;
    }

    _setLoading(true);
    _error = null;

    try {
      final result = await _api.createOnDemandTrip(
        pickup: {
          'address': pickupAddress.trim(),
          'lat': pickupLat!,
          'lon': pickupLon!,
        },
        dropoff: {
          'address': dropoffAddress.trim(),
          'lat': dropoffLat!,
          'lon': dropoffLon!,
        },
        estimatedFare: _estimatedFare!,
        cargoDescription: cargoDescription,
        cargoWeightKg: cargoWeightKg,
      );

      _setLoading(false);
      return result;
    } catch (e) {
      _error = 'No se pudo crear el flete. Reintentá.';
      _setLoading(false);
      return null;
    }
  }

  void _setLoading(bool v) {
    _isLoading = v;
    notifyListeners();
  }
}
