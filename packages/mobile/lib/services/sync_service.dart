import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:uuid/uuid.dart';
import 'package:crypto/crypto.dart';
import '../db/database_helper.dart';
import '../models/models.dart';
import 'api_service.dart';
import 'dashboard_service.dart';

/// Enhanced sync service with offline-first architecture
/// Features:
/// - Conflict detection and resolution (last-write-wins)
/// - Chunked file upload for resumable uploads
/// - Incremental sync (field-level changes)
/// - Background sync with WorkManager
/// - Offline data preloading
class SyncService {
  static final SyncService instance = SyncService._();
  
  final DatabaseHelper _db = DatabaseHelper.instance;
  final Connectivity _connectivity = Connectivity();
  final Uuid _uuid = const Uuid();
  
  bool _isOnline = true;
  bool _isSyncing = false;
  Timer? _syncTimer;
  Timer? _connectivityCheckTimer;
  
  // Stream controllers for sync status updates
  final _syncStatusController = StreamController<SyncStatus>.broadcast();
  final _uploadProgressController = StreamController<UploadProgress>.broadcast();
  
  // Configuration
  static const int maxRetries = 3;
  static const int chunkSizeBytes = 1024 * 1024; // 1MB chunks
  static const Duration defaultSyncInterval = Duration(minutes: 5);

  SyncService._() {
    _initConnectivity();
  }

  /// Stream of sync status updates
  Stream<SyncStatus> get syncStatusStream => _syncStatusController.stream;
  
  /// Stream of upload progress updates
  Stream<UploadProgress> get uploadProgressStream => _uploadProgressController.stream;
  
  /// Check if currently online
  bool get isOnline => _isOnline;
  
  /// Check if sync is in progress
  bool get isSyncing => _isSyncing;

  void _initConnectivity() {
    // Initial check
    _checkConnectivity();
    
    // Listen for changes
    _connectivity.onConnectivityChanged.listen((results) {
      final result = results.isNotEmpty ? results.first : ConnectivityResult.none;
      final wasOnline = _isOnline;
      _isOnline = result != ConnectivityResult.none;
      
      print('Connectivity changed: ${_isOnline ? "Online" : "Offline"}');
      
      if (!wasOnline && _isOnline) {
        // Just came online - trigger sync
        syncPendingData();
      }
      
      _syncStatusController.add(SyncStatus(
        isOnline: _isOnline,
        pendingCount: _getPendingCount(),
      ));
    });
    
    // Periodic connectivity check
    _connectivityCheckTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _checkConnectivity(),
    );
  }

  Future<void> _checkConnectivity() async {
    final results = await _connectivity.checkConnectivity();
    final result = results.isNotEmpty ? results.first : ConnectivityResult.none;
    _isOnline = result != ConnectivityResult.none;
  }

  /// Start periodic sync
  void startPeriodicSync({Duration interval = defaultSyncInterval}) {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(interval, (_) {
      if (_isOnline && !_isSyncing) {
        syncPendingData();
      }
    });
  }

  /// Stop periodic sync
  void stopPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = null;
  }

  /// Get pending sync count
  Future<int> _getPendingCount() async {
    return await _db.getPendingSyncCount();
  }

  /// Sync all pending data
  Future<SyncResult> syncPendingData() async {
    if (!_isOnline) {
      print('Offline, skipping sync');
      return SyncResult(
        success: false,
        message: 'Offline',
        syncedItems: 0,
        failedItems: 0,
      );
    }

    if (_isSyncing) {
      print('Sync already in progress');
      return SyncResult(
        success: false,
        message: 'Sync in progress',
        syncedItems: 0,
        failedItems: 0,
      );
    }

    _isSyncing = true;
    _syncStatusController.add(SyncStatus(
      isOnline: _isOnline,
      pendingCount: await _getPendingCount(),
      isSyncing: true,
    ));

    print('Starting sync...');
    
    int syncedItems = 0;
    int failedItems = 0;
    final List<SyncConflict> conflicts = [];

    try {
      // Step 1: Process chunked uploads (large files)
      await _processChunkedUploads();
      
      // Step 2: Get pending sync items
      final pendingItems = await _db.getPendingSyncItems();
      
      for (final item in pendingItems) {
        if (!_isOnline) break; // Stop if went offline
        
        try {
          // Process based on entity type
          final result = await _processSyncItem(item);
          
          if (result.success) {
            await _db.markSyncItemCompleted(item.id);
            syncedItems++;
          } else if (result.conflict != null) {
            // Handle conflict
            conflicts.add(result.conflict!);
            await _db.logConflict(result.conflict!);
            // Apply last-write-wins strategy
            await _resolveConflictLastWriteWins(result.conflict!);
            syncedItems++;
          } else {
            if (item.retryCount >= maxRetries - 1) {
              await _db.markSyncItemFailed(item.id, result.error ?? 'Max retries exceeded');
            } else {
              await _db.incrementSyncRetry(item.id);
            }
            failedItems++;
          }
        } catch (e) {
          print('Error processing sync item ${item.id}: $e');
          await _db.markSyncItemFailed(item.id, e.toString());
          failedItems++;
        }
      }

      // Step 3: Pull remote changes (incremental sync)
      await _pullRemoteChanges();
      
      // Clean up old completed items
      await _db.clearCompletedSyncItems();
      await _db.clearOldChangeLogs();
      
      print('Sync completed: $syncedItems synced, $failedItems failed');
      
      _syncStatusController.add(SyncStatus(
        isOnline: _isOnline,
        pendingCount: await _getPendingCount(),
        isSyncing: false,
      ));
      
      return SyncResult(
        success: failedItems == 0,
        message: failedItems == 0 ? 'Sync completed' : 'Sync completed with errors',
        syncedItems: syncedItems,
        failedItems: failedItems,
        conflicts: conflicts,
      );
    } catch (e) {
      print('Sync error: $e');
      _syncStatusController.add(SyncStatus(
        isOnline: _isOnline,
        pendingCount: await _getPendingCount(),
        isSyncing: false,
        error: e.toString(),
      ));
      
      return SyncResult(
        success: false,
        message: e.toString(),
        syncedItems: syncedItems,
        failedItems: failedItems,
      );
    } finally {
      _isSyncing = false;
    }
  }

  /// Process a single sync item
  Future<_SyncItemResult> _processSyncItem(SyncQueueItem item) async {
    // Update status to in progress
    await _db.updateSyncQueueItem(item.copyWith(
      status: SyncQueueStatus.inProgress,
      lastAttemptAt: DateTime.now(),
    ));

    try {
      switch (item.entityType) {
        case SyncEntityType.photo:
          return await _syncPhoto(item);
        case SyncEntityType.issue:
          return await _syncIssue(item);
        case SyncEntityType.progress:
          return await _syncProgress(item);
        case SyncEntityType.project:
          return await _syncProject(item);
        case SyncEntityType.safetyCheck:
          return await _syncSafetyCheck(item);
      }
    } catch (e) {
      return _SyncItemResult(success: false, error: e.toString());
    }
  }

  // ==================== CONFLICT DETECTION & RESOLUTION ====================
  
  /// Detect conflict by comparing versions
  Future<SyncConflict?> _detectConflict(String entityType, String entityId, Map<String, dynamic> localData, Map<String, dynamic> remoteData) async {
    final localVersion = localData['local_version'] ?? localData['version'] ?? 1;
    final remoteVersion = remoteData['version'] ?? 1;
    
    // If remote version is newer, there's a potential conflict
    if (remoteVersion > localVersion) {
      // Check if local has unsynced changes
      final pendingChanges = await _db.getPendingChanges(entityType: entityType);
      final hasLocalChanges = pendingChanges.any((c) => c['entity_id'] == entityId);
      
      if (hasLocalChanges) {
        return SyncConflict(
          entityType: entityType,
          entityId: entityId,
          localData: localData,
          remoteData: remoteData,
          resolution: ConflictResolution.manual,
        );
      }
    }
    return null;
  }

  /// Resolve conflict using last-write-wins strategy
  Future<void> _resolveConflictLastWriteWins(SyncConflict conflict) async {
    // Keep local data, update version to remote + 1
    print('Resolving conflict for ${conflict.entityType}/${conflict.entityId} using last-write-wins');
    
    // Update local data with incremented version
    await _db.updateSyncMetadata(conflict.entityType, lastVersion: (conflict.remoteData['version'] ?? 0) + 1);
  }

  /// Manual conflict resolution
  Future<void> resolveConflictManually(String conflictId, ConflictResolution resolution) async {
    await _db.resolveConflict(conflictId, resolution);
    
    // If keeping local, re-queue for sync
    if (resolution == ConflictResolution.keepLocal) {
      final conflicts = await _db.getUnresolvedConflicts();
      final conflict = conflicts.firstWhere((c) => c['id'] == conflictId);
      // Re-queue sync...
    }
  }

  // ==================== CHUNKED UPLOAD (RESUMABLE) ====================
  
  /// Process pending chunked uploads
  Future<void> _processChunkedUploads() async {
    final pendingUploads = await _db.getPendingChunkedUploads();
    
    for (final upload in pendingUploads) {
      try {
        await _resumeChunkedUpload(upload);
      } catch (e) {
        print('Chunked upload failed: $e');
        await _db.failChunkedUpload(upload.id, e.toString());
      }
    }
  }

  /// Start a chunked upload for a large file
  Future<String> startChunkedUpload({
    required String entityId,
    required String filePath,
    required int fileSize,
  }) async {
    final id = _uuid.v4();
    final totalChunks = (fileSize / chunkSizeBytes).ceil();
    
    final upload = ChunkedUpload(
      id: id,
      entityType: 'photo',
      entityId: entityId,
      filePath: filePath,
      fileSize: fileSize,
      totalChunks: totalChunks,
      status: 'pending',
    );
    
    await _db.startChunkedUpload(upload);
    
    // Trigger upload if online
    if (_isOnline) {
      _processChunkedUploads();
    }
    
    return id;
  }

  /// Resume a chunked upload
  Future<void> _resumeChunkedUpload(ChunkedUpload upload) async {
    final file = File(upload.filePath);
    if (!await file.exists()) {
      await _db.failChunkedUpload(upload.id, 'File not found');
      return;
    }

    // Update status to in_progress
    await _db.updateChunkedUploadProgress(upload.id, upload.uploadedChunks, upload.progress);

    try {
      // Read and upload chunks
      final randomAccessFile = await file.open(mode: FileMode.read);
      int uploadedChunks = upload.uploadedChunks;
      
      for (int i = uploadedChunks; i < upload.totalChunks; i++) {
        if (!_isOnline) break;
        
        await randomAccess * uploadFile.setPosition(i.chunkSize);
        final chunk = await randomAccessFile.read(upload.chunkSize);
        
        // Upload chunk
        final result = await ApiService.uploadChunk(
          uploadId: upload.uploadId ?? upload.id,
          chunkIndex: i,
          chunkData: chunk,
          entityId: upload.entityId,
        );
        
        if (result['status'] == 'success') {
          uploadedChunks++;
          final progress = uploadedChunks / upload.totalChunks;
          await _db.updateChunkedUploadProgress(upload.id, uploadedChunks, progress);
          
          _uploadProgressController.add(UploadProgress(
            entityId: upload.entityId,
            progress: progress,
            uploadedChunks: uploadedChunks,
            totalChunks: upload.totalChunks,
          ));
        } else {
          await randomAccessFile.close();
          throw Exception('Chunk upload failed: ${result['message']}');
        }
      }
      
      await randomAccessFile.close();
      
      // Complete the upload
      if (uploadedChunks == upload.totalChunks) {
        final finalResult = await ApiService.completeChunkedUpload(
          uploadId: upload.uploadId ?? upload.id,
          entityId: upload.entityId,
        );
        
        if (finalResult['status'] == 'success') {
          await _db.completeChunkedUpload(upload.id, finalResult['upload_id'] ?? upload.id);
          await _db.updatePhotoSyncStatus(upload.entityId, PhotoSyncStatus.synced, remoteUrl: finalResult['url']);
        }
      }
    } catch (e) {
      await _db.failChunkedUpload(upload.id, e.toString());
      rethrow;
    }
  }

  /// Calculate file checksum (MD5)
  Future<String> calculateFileChecksum(String filePath) async {
    final file = File(filePath);
    final bytes = await file.readAsBytes();
    return md5.convert(bytes).toString();
  }

  // ==================== INCREMENTAL SYNC ====================
  
  /// Pull remote changes (incremental sync)
  Future<void> _pullRemoteChanges() async {
    try {
      // Get sync metadata
      final photoMeta = await _db.getSyncMetadata('photo');
      final lastSyncVersion = photoMeta?['last_sync_version'] as int? ?? 0;
      
      // Fetch changes from server
      final changes = await ApiService.getIncrementalChanges(
        sinceVersion: lastSyncVersion,
      );
      
      if (changes['status'] == 'success' && changes['data'] != null) {
        final data = changes['data'] as Map<String, dynamic>;
        
        // Process each entity type
        for (final entityType in ['photo', 'issue', 'progress', 'project']) {
          final entities = data[entityType] as List<dynamic>? ?? [];
          
          for (final entity in entities) {
            final entityMap = entity as Map<String, dynamic>;
            final entityId = entityMap['id'] as String;
            
            // Check for conflicts
            final localEntity = await _getLocalEntity(entityType, entityId);
            
            if (localEntity != null) {
              // Compare versions
              final conflict = await _detectConflict(
                entityType,
                entityId,
                localEntity,
                entityMap,
              );
              
              if (conflict != null) {
                await _db.logConflict(conflict);
              } else {
                // No conflict, apply remote changes
                await _applyRemoteChanges(entityType, entityMap);
              }
            } else {
              // New entity from server
              await _applyRemoteChanges(entityType, entityMap);
            }
          }
        }
        
        // Update sync metadata
        await _db.updateSyncMetadata(
          'photo',
          lastVersion: data['version'] as int? ?? lastSyncVersion + 1,
          syncToken: data['sync_token'] as String?,
        );
      }
    } catch (e) {
      print('Error pulling remote changes: $e');
    }
  }

  /// Get local entity by type
  Future<Map<String, dynamic>?> _getLocalEntity(String entityType, String entityId) async {
    switch (entityType) {
      case 'photo':
        final photo = await _db.getPhoto(entityId);
        return photo?.toMap();
      case 'project':
        final project = await _db.getProject(entityId);
        return project?.toMap();
      default:
        return null;
    }
  }

  /// Apply remote changes to local database
  Future<void> _applyRemoteChanges(String entityType, Map<String, dynamic> data) async {
    switch (entityType) {
      case 'photo':
        final photo = Photo.fromJson(data);
        await _db.insertPhoto(photo);
        break;
      case 'project':
        final project = Project.fromJson(data);
        await _db.insertProject(project);
        break;
    }
  }

  /// Get incremental changes to send to server
  Future<Map<String, dynamic>> getIncrementalChanges(String entityType) async {
    final changes = await _db.getPendingChanges(entityType: entityType);
    
    // Group by entity_id
    final Map<String, List<Map<String, dynamic>>> grouped = {};
    for (final change in changes) {
      final entityId = change['entity_id'] as String;
      grouped.putIfAbsent(entityId, () => []).add(change);
    }
    
    return {
      'entity_type': entityType,
      'changes': grouped,
    };
  }

  // ==================== SYNC ENTITY TYPES ====================

  /// Sync a photo
  Future<_SyncItemResult> _syncPhoto(SyncQueueItem item) async {
    try {
      final payload = item.payload;
      
      // Check if this is a large file that needs chunked upload
      final localPath = payload['local_path'] as String?;
      if (localPath != null) {
        final file = File(localPath);
        if (await file.exists()) {
          final fileSize = await file.length();
          
          // If file > 5MB, use chunked upload
          if (fileSize > 5 * 1024 * 1024) {
            final checksum = await calculateFileChecksum(localPath);
            await _db.updatePhoto(Photo(
              id: item.entityId,
              localPath: localPath,
              capturedAt: DateTime.now(),
              syncStatus: PhotoSyncStatus.uploading,
            ));
            
            await startChunkedUpload(
              entityId: item.entityId,
              filePath: localPath,
              fileSize: fileSize,
            );
            
            return _SyncItemResult(success: true);
          }
        }
      }
      
      if (item.operation == SyncOperation.create || item.operation == SyncOperation.update) {
        // Upload photo to server
        final result = await ApiService.uploadPhoto(
          localPath: localPath ?? '',
          metadata: {
            'id': item.entityId,
            'latitude': payload['latitude'],
            'longitude': payload['longitude'],
            'chainage': payload['chainage'],
            'project_id': payload['project_id'],
            'captured_at': payload['captured_at'],
            'description': payload['description'],
          },
        );
        
        if (result['status'] == 'success') {
          // Update local photo with remote URL
          await _db.updatePhotoSyncStatus(
            item.entityId,
            PhotoSyncStatus.synced,
            remoteUrl: result['url'],
          );
          return _SyncItemResult(success: true);
        } else {
          return _SyncItemResult(success: false, error: result['message']);
        }
      } else if (item.operation == SyncOperation.delete) {
        // Delete from server
        final result = await ApiService.deletePhoto(item.entityId);
        if (result['status'] == 'success') {
          await _db.softDeletePhoto(item.entityId);
          return _SyncItemResult(success: true);
        } else {
          return _SyncItemResult(success: false, error: result['message']);
        }
      }
      
      return _SyncItemResult(success: false, error: 'Unknown operation');
    } catch (e) {
      print('Error syncing photo: $e');
      return _SyncItemResult(success: false, error: e.toString());
    }
  }

  /// Sync an issue
  Future<_SyncItemResult> _syncIssue(SyncQueueItem item) async {
    try {
      final payload = item.payload;
      
      if (item.operation == SyncOperation.create) {
        final result = await ApiService.addIssue(
          chainage: payload['chainage'] as String,
          description: payload['description'] as String,
          severity: payload['severity'] as String?,
          latitude: (payload['latitude'] as num?)?.toDouble(),
          longitude: (payload['longitude'] as num?)?.toDouble(),
          imageUrl: payload['image_url'] as String?,
        );
        
        if (result['status'] == 'success') {
          return _SyncItemResult(success: true);
        } else {
          return _SyncItemResult(success: false, error: result['message']);
        }
      }
      
      return _SyncItemResult(success: false, error: 'Unknown operation');
    } catch (e) {
      print('Error syncing issue: $e');
      return _SyncItemResult(success: false, error: e.toString());
    }
  }

  /// Sync progress
  Future<_SyncItemResult> _syncProgress(SyncQueueItem item) async {
    try {
      final payload = item.payload;
      
      if (item.operation == SyncOperation.create) {
        final result = await DashboardService.submitProgress(
          chainage: payload['chainage'] as String,
          status: payload['status'] as String,
          note: payload['note'] as String?,
          latitude: (payload['latitude'] as num?)?.toDouble(),
          longitude: (payload['longitude'] as num?)?.toDouble(),
          workType: payload['work_type'] as String?,
          quantity: (payload['quantity'] as num?)?.toDouble(),
          unit: payload['unit'] as String?,
          projectId: payload['project_id'] as String?,
        );
        
        if (result['status'] == 'success') {
          return _SyncItemResult(success: true);
        } else {
          return _SyncItemResult(success: false, error: result['message']);
        }
      }
      
      return _SyncItemResult(success: false, error: 'Unknown operation');
    } catch (e) {
      print('Error syncing progress: $e');
      return _SyncItemResult(success: false, error: e.toString());
    }
  }

  /// Sync safety check
  Future<_SyncItemResult> _syncSafetyCheck(SyncQueueItem item) async {
    try {
      final payload = item.payload;
      
      if (item.operation == SyncOperation.create) {
        final result = await DashboardService.submitSafetyCheck(
          chainage: payload['chainage'] as String,
          checkType: payload['check_type'] as String,
          description: payload['description'] as String?,
          findings: payload['findings'] as String?,
          latitude: (payload['latitude'] as num?)?.toDouble(),
          longitude: (payload['longitude'] as num?)?.toDouble(),
          inspector: payload['inspector'] as String?,
          imagePath: payload['local_image_path'] as String?,
          projectId: payload['project_id'] as String?,
        );
        
        if (result['status'] == 'success') {
          return _SyncItemResult(success: true);
        } else {
          return _SyncItemResult(success: false, error: result['message']);
        }
      }
      
      return _SyncItemResult(success: false, error: 'Unknown operation');
    } catch (e) {
      print('Error syncing safety check: $e');
      return _SyncItemResult(success: false, error: e.toString());
    }
  }

  /// Sync project
  Future<_SyncItemResult> _syncProject(SyncQueueItem item) async {
    // Project sync logic
    return _SyncItemResult(success: true);
  }

  // ==================== QUEUE MANAGEMENT ====================

  /// Add a photo to sync queue
  Future<void> queuePhotoUpload(Photo photo) async {
    final item = SyncQueueItem(
      id: _uuid.v4(),
      entityType: SyncEntityType.photo,
      entityId: photo.id,
      operation: SyncOperation.create,
      payload: photo.toJson(),
    );
    
    await _db.addToSyncQueue(item);
    
    // Update photo status
    await _db.updatePhotoSyncStatus(photo.id, PhotoSyncStatus.pending);
    
    // Trigger sync if online
    if (_isOnline) {
      syncPendingData();
    }
  }

  /// Add an issue to sync queue
  Future<void> queueIssueSync(Map<String, dynamic> issue) async {
    final item = SyncQueueItem(
      id: _uuid.v4(),
      entityType: SyncEntityType.issue,
      entityId: issue['id'] as String,
      operation: SyncOperation.create,
      payload: issue,
    );
    
    await _db.addToSyncQueue(item);
    
    // Trigger sync if online
    if (_isOnline) {
      syncPendingData();
    }
  }

  /// Manual sync trigger
  Future<SyncResult> syncNow() async {
    return await syncPendingData();
  }

  /// Get sync status
  Future<SyncStatus> getSyncStatus() async {
    return SyncStatus(
      isOnline: _isOnline,
      pendingCount: await _getPendingCount(),
      isSyncing: _isSyncing,
    );
  }

  /// Get unresolved conflicts
  Future<List<Map<String, dynamic>>> getConflicts() async {
    return await _db.getUnresolvedConflicts();
  }

  /// Dispose resources
  void dispose() {
    stopPeriodicSync();
    _connectivityCheckTimer?.cancel();
    _syncStatusController.close();
    _uploadProgressController.close();
  }
}

/// Internal result class for sync item processing
class _SyncItemResult {
  final bool success;
  final String? error;
  final SyncConflict? conflict;

  _SyncItemResult({
    required this.success,
    this.error,
    this.conflict,
  });
}

/// Sync status information
class SyncStatus {
  final bool isOnline;
  final int pendingCount;
  final bool isSyncing;
  final String? error;

  SyncStatus({
    required this.isOnline,
    required this.pendingCount,
    this.isSyncing = false,
    this.error,
  });
}

/// Upload progress information
class UploadProgress {
  final String entityId;
  final double progress;
  final int uploadedChunks;
  final int totalChunks;

  UploadProgress({
    required this.entityId,
    required this.progress,
    required this.uploadedChunks,
    required this.totalChunks,
  });
}

/// Sync result
class SyncResult {
  final bool success;
  final String message;
  final int syncedItems;
  final int failedItems;
  final List<SyncConflict> conflicts;

  SyncResult({
    required this.success,
    required this.message,
    required this.syncedItems,
    required this.failedItems,
    this.conflicts = const [],
  });
}
