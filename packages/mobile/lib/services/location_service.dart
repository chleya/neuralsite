import 'dart:async';
import 'package:geolocator/geolocator.dart';

/// Location service for GPS functionality
class LocationService {
  static final LocationService instance = LocationService._();
  
  StreamSubscription<Position>? _positionSubscription;
  final _positionController = StreamController<Position>.broadcast();
  
  bool _isTracking = false;
  Position? _lastKnownPosition;
  
  LocationService._();

  /// Stream of position updates
  Stream<Position> get positionStream => _positionController.stream;
  
  /// Check if tracking is active
  bool get isTracking => _isTracking;
  
  /// Get last known position
  Position? get lastKnownPosition => _lastKnownPosition;

  /// Check and request location permissions
  Future<LocationPermissionStatus> checkPermission() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return LocationPermissionStatus.serviceDisabled;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    return _mapPermission(permission);
  }

  /// Request location permissions
  Future<LocationPermissionStatus> requestPermission() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return LocationPermissionStatus.serviceDisabled;
    }

    LocationPermission permission = await Geolocator.requestPermission();
    return _mapPermission(permission);
  }

  LocationPermissionStatus _mapPermission(LocationPermission permission) {
    switch (permission) {
      case LocationPermission.denied:
        return LocationPermissionStatus.denied;
      case LocationPermission.deniedForever:
        return LocationPermissionStatus.deniedForever;
      case LocationPermission.whileInUse:
        return LocationPermissionStatus.whileInUse;
      case LocationPermission.always:
        return LocationPermissionStatus.always;
      default:
        return LocationPermissionStatus.denied;
    }
  }

  /// Get current position
  Future<Position?> getCurrentPosition({
    LocationAccuracy accuracy = LocationAccuracy.high,
    int timeoutSeconds = 10,
  }) async {
    try {
      final status = await checkPermission();
      if (status != LocationPermissionStatus.whileInUse &&
          status != LocationPermissionStatus.always) {
        final requestedStatus = await requestPermission();
        if (requestedStatus != LocationPermissionStatus.whileInUse &&
            requestedStatus != LocationPermissionStatus.always) {
          return null;
        }
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: LocationSettings(
          accuracy: accuracy,
          timeLimit: Duration(seconds: timeoutSeconds),
        ),
      );
      
      _lastKnownPosition = position;
      return position;
    } catch (e) {
      print('Error getting position: $e');
      return _lastKnownPosition;
    }
  }

  /// Start continuous position tracking
  Future<bool> startTracking({
    LocationAccuracy accuracy = LocationAccuracy.high,
    int distanceFilter = 10, // meters
    int intervalMs = 5000,   // 5 seconds
  }) async {
    if (_isTracking) return true;

    final status = await checkPermission();
    if (status != LocationPermissionStatus.whileInUse &&
        status != LocationPermissionStatus.always) {
      final requestedStatus = await requestPermission();
      if (requestedStatus != LocationPermissionStatus.whileInUse &&
          requestedStatus != LocationPermissionStatus.always) {
        return false;
      }
    }

    _isTracking = true;
    
    final locationSettings = AndroidSettings(
      accuracy: accuracy,
      distanceFilter: distanceFilter,
      intervalDuration: Duration(milliseconds: intervalMs),
      forceLocationManager: false,
    );

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: locationSettings,
    ).listen(
      (position) {
        _lastKnownPosition = position;
        _positionController.add(position);
      },
      onError: (error) {
        print('Location tracking error: $error');
      },
    );

    return true;
  }

  /// Stop position tracking
  void stopTracking() {
    _positionSubscription?.cancel();
    _positionSubscription = null;
    _isTracking = false;
  }

  /// Calculate distance between two positions in meters
  double calculateDistance(
    double startLat,
    double startLng,
    double endLat,
    double endLng,
  ) {
    return Geolocator.distanceBetween(startLat, startLng, endLat, endLng);
  }

  /// Check if position is within a radius of a point
  bool isWithinRadius(
    double centerLat,
    double centerLng,
    double pointLat,
    double pointLng,
    double radiusMeters,
  ) {
    final distance = calculateDistance(centerLat, centerLng, pointLat, pointLng);
    return distance <= radiusMeters;
  }

  /// Calculate chainage from a reference point given a distance
  /// This is a simplified version - in production would use actual route data
  double calculateChainage(
    double referenceLat,
    double referenceLng,
    double currentLat,
    double currentLng,
  ) {
    return calculateDistance(referenceLat, referenceLng, currentLat, currentLng);
  }

  /// Open location settings
  Future<bool> openLocationSettings() async {
    return await Geolocator.openLocationSettings();
  }

  /// Open app settings for permissions
  Future<bool> openAppSettings() async {
    return await Geolocator.openAppSettings();
  }

  /// Dispose resources
  void dispose() {
    stopTracking();
    _positionController.close();
  }
}

/// Location permission status
enum LocationPermissionStatus {
  serviceDisabled,
  denied,
  deniedForever,
  whileInUse,
  always,
}

extension LocationPermissionStatusExtension on LocationPermissionStatus {
  bool get isGranted =>
      this == LocationPermissionStatus.whileInUse ||
      this == LocationPermissionStatus.always;

  String get displayName {
    switch (this) {
      case LocationPermissionStatus.serviceDisabled:
        return 'Service Disabled';
      case LocationPermissionStatus.denied:
        return 'Denied';
      case LocationPermissionStatus.deniedForever:
        return 'Denied Forever';
      case LocationPermissionStatus.whileInUse:
        return 'While In Use';
      case LocationPermissionStatus.always:
        return 'Always';
    }
  }
}
