import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:uuid/uuid.dart';
import '../db/database_helper.dart';
import '../db/offline_database_helper.dart';
import '../models/models.dart';
import '../services/location_service.dart';
import '../services/camera_service.dart';
import '../services/sync_service.dart';
import '../services/api_service.dart';
import '../services/offline_data_service.dart';

// ==================== Core Providers ====================

/// Database provider
final databaseProvider = Provider<DatabaseHelper>((ref) {
  return DatabaseHelper.instance;
});

/// Location service provider
final locationServiceProvider = Provider<LocationService>((ref) {
  return LocationService.instance;
});

/// Camera service provider
final cameraServiceProvider = Provider<CameraService>((ref) {
  return CameraService.instance;
});

/// Sync service provider
final syncServiceProvider = Provider<SyncService>((ref) {
  return SyncService.instance;
});

// ==================== Location Providers ====================

/// Current position provider
final currentPositionProvider = FutureProvider<Position?>((ref) async {
  final locationService = ref.watch(locationServiceProvider);
  return await locationService.getCurrentPosition();
});

/// Location permission status provider
final locationPermissionProvider = FutureProvider<LocationPermissionStatus>((ref) async {
  final locationService = ref.watch(locationServiceProvider);
  return await locationService.checkPermission();
});

/// Location stream provider
final locationStreamProvider = StreamProvider<Position?>((ref) {
  final locationService = ref.watch(locationServiceProvider);
  
  // Start tracking
  locationService.startTracking();
  
  return locationService.positionStream;
});

// ==================== Project Providers ====================

/// All projects provider
final projectsProvider = FutureProvider<List<Project>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getAllProjects();
});

/// Active project provider
final activeProjectProvider = FutureProvider<Project?>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getActiveProject();
});

/// Selected project ID provider
final selectedProjectIdProvider = StateProvider<String?>((ref) => null);

/// Selected project provider
final selectedProjectProvider = FutureProvider<Project?>((ref) async {
  final projectId = ref.watch(selectedProjectIdProvider);
  if (projectId == null) return null;
  
  final db = ref.watch(databaseProvider);
  return await db.getProject(projectId);
});

// ==================== Photo Providers ====================

/// All photos provider
final photosProvider = FutureProvider<List<Photo>>((ref) async {
  final db = ref.watch(databaseProvider);
  final projectId = ref.watch(selectedProjectIdProvider);
  return await db.getAllPhotos(projectId: projectId);
});

/// Unsynced photos provider
final unsyncedPhotosProvider = FutureProvider<List<Photo>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getUnsyncedPhotos();
});

/// Photo capture state
class PhotoCaptureState {
  final bool isCapturing;
  final Position? position;
  final String? chainage;
  final String? error;

  PhotoCaptureState({
    this.isCapturing = false,
    this.position,
    this.chainage,
    this.error,
  });

  PhotoCaptureState copyWith({
    bool? isCapturing,
    Position? position,
    String? chainage,
    String? error,
  }) {
    return PhotoCaptureState(
      isCapturing: isCapturing ?? this.isCapturing,
      position: position ?? this.position,
      chainage: chainage ?? this.chainage,
      error: error ?? this.error,
    );
  }
}

/// Photo capture notifier
class PhotoCaptureNotifier extends StateNotifier<PhotoCaptureState> {
  final Ref ref;
  
  PhotoCaptureNotifier(this.ref) : super(PhotoCaptureState());

  Future<void> capturePhoto() async {
    state = state.copyWith(isCapturing: true, error: null);
    
    try {
      // Get current position
      final locationService = ref.read(locationServiceProvider);
      final position = await locationService.getCurrentPosition();
      
      // Take photo
      final cameraService = ref.read(cameraServiceProvider);
      final capturedPhoto = await cameraService.takePhoto();
      
      if (capturedPhoto == null) {
        state = state.copyWith(isCapturing: false, error: 'No photo captured');
        return;
      }
      
      // Get active project
      final db = ref.read(databaseProvider);
      final activeProject = await db.getActiveProject();
      
      // Create photo model
      final photo = Photo(
        id: const Uuid().v4(),
        localPath: capturedPhoto.path,
        latitude: position?.latitude,
        longitude: position?.longitude,
        capturedAt: capturedPhoto.capturedAt,
        projectId: activeProject?.id,
        syncStatus: PhotoSyncStatus.pending,
      );
      
      // Save to database
      await db.insertPhoto(photo);
      
      // Queue for sync
      final syncService = ref.read(syncServiceProvider);
      await syncService.queuePhotoUpload(photo);
      
      // Update state
      state = PhotoCaptureState(
        position: position,
        chainage: _calculateChainage(position, activeProject),
      );
      
      // Refresh photos list
      ref.invalidate(photosProvider);
      ref.invalidate(unsyncedPhotosProvider);
      
    } catch (e) {
      state = state.copyWith(isCapturing: false, error: e.toString());
    }
  }

  String? _calculateChainage(Position? position, Project? project) {
    if (position == null || project?.startStation == null) return null;
    
    // Simplified chainage calculation
    // In production, would use route data
    final distance = project!.startStation!;
    final km = (distance / 1000).floor();
    final m = (distance % 1000).toInt();
    return 'K$km+$m';
  }

  void reset() {
    state = PhotoCaptureState();
  }
}

/// Photo capture provider
final photoCaptureProvider = StateNotifierProvider<PhotoCaptureNotifier, PhotoCaptureState>((ref) {
  return PhotoCaptureNotifier(ref);
});

// ==================== Sync Providers ====================

/// Sync status provider
final syncStatusProvider = StreamProvider<SyncStatus>((ref) {
  final syncService = ref.watch(syncServiceProvider);
  return syncService.syncStatusStream;
});

/// Pending sync count provider
final pendingSyncCountProvider = FutureProvider<int>((ref) async {
  final syncService = ref.watch(syncServiceProvider);
  final status = await syncService.getSyncStatus();
  return status.pendingCount;
});

/// Is online provider
final isOnlineProvider = Provider<bool>((ref) {
  final syncStatus = ref.watch(syncStatusProvider);
  return syncStatus.when(
    data: (status) => status.isOnline,
    loading: () => true,
    error: (_, __) => false,
  );
});

// ==================== Issue Providers ====================

/// Issues list provider
final issuesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getAllIssues();
});

// ==================== Progress Providers ====================

/// Progress list provider
final progressProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getAllProgress();
});

/// Unsynced progress provider
final unsyncedProgressProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getUnsyncedProgress();
});

// ==================== Safety Check Providers ====================

/// Safety checks list provider
final safetyChecksProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getAllSafetyChecks();
});

// ==================== AI Detection Providers ====================

/// Detections list provider
final detectionsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getAllDetections();
});

/// Pending approvals provider
final pendingApprovalsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getPendingApprovals();
});

/// AI Detection capture state
class AIDetectionState {
  final bool isAnalyzing;
  final String? currentPhotoId;
  final List<Map<String, dynamic>>? results;
  final String? error;

  AIDetectionState({
    this.isAnalyzing = false,
    this.currentPhotoId,
    this.results,
    this.error,
  });

  AIDetectionState copyWith({
    bool? isAnalyzing,
    String? currentPhotoId,
    List<Map<String, dynamic>>? results,
    String? error,
  }) {
    return AIDetectionState(
      isAnalyzing: isAnalyzing ?? this.isAnalyzing,
      currentPhotoId: currentPhotoId ?? this.currentPhotoId,
      results: results ?? this.results,
      error: error ?? this.error,
    );
  }
}

/// AI Detection notifier
class AIDetectionNotifier extends StateNotifier<AIDetectionState> {
  final Ref ref;
  
  AIDetectionNotifier(this.ref) : super(AIDetectionState());

  Future<void> analyzePhoto(Photo photo) async {
    if (photo.localPath == null) {
      state = state.copyWith(error: 'No photo path available');
      return;
    }

    state = state.copyWith(isAnalyzing: true, currentPhotoId: photo.id, error: null);
    
    try {
      // Submit photo for AI detection
      final result = await ApiService.submitForDetection(
        localPath: photo.localPath!,
        photoId: photo.id,
        detectionType: 'construction',
      );
      
      if (result['status'] == 'success') {
        // Save detection result to local DB
        final db = ref.read(databaseProvider);
        await db.insertDetection({
          'id': result['id'] ?? const Uuid().v4(),
          'photo_id': photo.id,
          'local_image_path': photo.localPath,
          'remote_image_url': result['image_url'],
          'status': 'completed',
          'summary': result['summary'],
          'confidence': result['confidence'] ?? 0.0,
          'results': result['results']?.toString(),
          'analyzed_at': DateTime.now().toIso8601String(),
          'created_at': DateTime.now().toIso8601String(),
        });
        
        state = state.copyWith(
          isAnalyzing: false,
          results: result['results'] != null ? List<Map<String, dynamic>>.from(result['results']) : [],
        );
        
        // Refresh detections
        ref.invalidate(detectionsProvider);
      } else {
        state = state.copyWith(
          isAnalyzing: false,
          error: result['message'] ?? 'Analysis failed',
        );
      }
    } catch (e) {
      state = state.copyWith(isAnalyzing: false, error: e.toString());
    }
  }

  Future<void> submitForApproval(String detectionId, String approver) async {
    try {
      await ApiService.submitForApproval(
        detectionId: detectionId,
        approver: approver,
      );
      ref.invalidate(pendingApprovalsProvider);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> approveDetection(String approvalId, {String? comment}) async {
    try {
      await ApiService.processApproval(
        approvalId: approvalId,
        status: 'approved',
        comment: comment,
      );
      ref.invalidate(pendingApprovalsProvider);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> rejectDetection(String approvalId, {String? comment}) async {
    try {
      await ApiService.processApproval(
        approvalId: approvalId,
        status: 'rejected',
        comment: comment,
      );
      ref.invalidate(pendingApprovalsProvider);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  void reset() {
    state = AIDetectionState();
  }
}

/// AI Detection provider
final aiDetectionProvider = StateNotifierProvider<AIDetectionNotifier, AIDetectionState>((ref) {
  return AIDetectionNotifier(ref);
});

// ==================== Settings Providers ====================

/// API server URL provider
final apiServerUrlProvider = StateProvider<String>((ref) => 'http://localhost:8000');

/// Offline mode enabled provider
final offlineModeProvider = StateProvider<bool>((ref) => true);

/// Auto sync enabled provider
final autoSyncProvider = StateProvider<bool>((ref) => true);

// ==================== Offline Data Providers ====================

import '../services/offline_data_service.dart';
import '../db/offline_database_helper.dart';

/// Offline data service provider
final offlineDataServiceProvider = Provider<OfflineDataService>((ref) {
  return OfflineDataService.instance;
});

/// Station search provider
final stationSearchProvider = FutureProvider.family<List<StationSearchResult>, String>((ref, query) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  final projectId = ref.watch(selectedProjectIdProvider);
  
  if (query.isEmpty) return [];
  
  return await offlineService.searchStations(
    query,
    projectId: projectId,
    limit: 20,
  );
});

/// Nearest station provider
final nearestStationProvider = FutureProvider.family<StationSearchResult?, ({double lat, double lon})>((ref, coords) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  final projectId = ref.watch(selectedProjectIdProvider);
  
  return await offlineService.getNearestStation(
    coords.lat,
    coords.lon,
    projectId: projectId,
  );
});

/// Material search provider
final materialSearchProvider = FutureProvider.family<List<MaterialStandard>, String>((ref, query) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  
  if (query.isEmpty) return [];
  
  return await offlineService.searchMaterials(query, limit: 20);
});

/// Material categories provider
final materialCategoriesProvider = FutureProvider<List<String>>((ref) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  return await offlineService.getMaterialCategories();
});

/// FAQ search provider
final faqSearchProvider = FutureProvider.family<List<FaqItem>, String>((ref, query) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  
  if (query.isEmpty) return [];
  
  return await offlineService.searchFaqs(query, limit: 20);
});

/// FAQ categories provider
final faqCategoriesProvider = FutureProvider<List<String>>((ref) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  return await offlineService.getFaqCategories();
});

/// User role provider
final userRoleProvider = FutureProvider<UserRole>((ref) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  return await offlineService.getUserRole();
});

/// Project phase provider
final projectPhaseProvider = FutureProvider<ProjectPhase>((ref) async {
  final offlineService = ref.watch(offlineDataServiceProvider);
  return await offlineService.getProjectPhase();
});
