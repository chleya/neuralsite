import 'package:uuid/uuid.dart';
import '../db/database_helper.dart';
import '../models/models.dart';
import 'dashboard_service.dart';

/// Local data service - handles offline-first data operations
/// Stores data locally first, then syncs to server when online
class LocalDataService {
  static final LocalDataService instance = LocalDataService._();
  
  final DatabaseHelper _db = DatabaseHelper.instance;
  final Uuid _uuid = const Uuid();

  LocalDataService._();

  // ==================== PROGRESS OPERATIONS ====================
  
  /// Save progress locally and queue for sync
  Future<Map<String, dynamic>> saveProgressLocal({
    required String chainage,
    required ProgressStatus status,
    String? note,
    double? latitude,
    double? longitude,
    String? workType,
    double? quantity,
    String? unit,
    String? projectId,
  }) async {
    final id = _uuid.v4();
    final now = DateTime.now();
    
    final progress = Progress(
      id: id,
      chainage: chainage,
      status: status,
      note: note,
      latitude: latitude,
      longitude: longitude,
      workType: workType,
      quantity: quantity,
      unit: unit,
      timestamp: now,
      synced: false,
      createdAt: now,
    );
    
    // Save to local database
    await _db.insertProgress(progress.toMap());
    
    // Queue for sync
    await _db.addToSyncQueue(SyncQueueItem(
      id: _uuid.v4(),
      entityType: SyncEntityType.progress,
      entityId: id,
      operation: SyncOperation.create,
      payload: {
        'id': id,
        'chainage': chainage,
        'status': status.name,
        'note': note,
        'latitude': latitude,
        'longitude': longitude,
        'work_type': workType,
        'quantity': quantity,
        'unit': unit,
        'project_id': projectId,
        'timestamp': now.toIso8601String(),
      },
    ).toMap());
    
    return {
      'status': 'success',
      'id': id,
      'local': true,
      'message': 'Progress saved locally, will sync when online',
    };
  }

  /// Submit progress - tries online first, falls back to local
  Future<Map<String, dynamic>> submitProgress({
    required String chainage,
    required ProgressStatus status,
    String? note,
    double? latitude,
    double? longitude,
    String? workType,
    double? quantity,
    String? unit,
    String? projectId,
    bool forceOffline = false,
  }) async {
    // Try to submit online
    if (!forceOffline) {
      final result = await DashboardService.submitProgress(
        chainage: chainage,
        status: status.name,
        note: note,
        latitude: latitude,
        longitude: longitude,
        workType: workType,
        quantity: quantity,
        unit: unit,
        projectId: projectId,
      );
      
      if (result['status'] == 'success') {
        // Save to local with synced flag
        final id = _uuid.v4();
        final now = DateTime.now();
        
        final progress = Progress(
          id: id,
          chainage: chainage,
          status: status,
          note: note,
          latitude: latitude,
          longitude: longitude,
          workType: workType,
          quantity: quantity,
          unit: unit,
          timestamp: now,
          synced: true,
          createdAt: now,
        );
        
        await _db.insertProgress(progress.toMap());
        
        return {
          'status': 'success',
          'id': id,
          'local': false,
          'data': result['data'],
        };
      }
    }
    
    // Fallback to local storage
    return await saveProgressLocal(
      chainage: chainage,
      status: status,
      note: note,
      latitude: latitude,
      longitude: longitude,
      workType: workType,
      quantity: quantity,
      unit: unit,
      projectId: projectId,
    );
  }

  /// Get all progress (local + synced)
  Future<List<Progress>> getAllProgress({String? projectId}) async {
    final maps = await _db.getAllProgress();
    return maps.map((m) => Progress.fromMap(m)).toList();
  }

  /// Get unsynced progress
  Future<List<Progress>> getUnsyncedProgress() async {
    final maps = await _db.getUnsyncedProgress();
    return maps.map((m) => Progress.fromMap(m)).toList();
  }

  // ==================== QUALITY ISSUE OPERATIONS ====================
  
  /// Save issue locally and queue for sync
  Future<Map<String, dynamic>> saveIssueLocal({
    required String chainage,
    required String description,
    IssueSeverity severity = IssueSeverity.medium,
    double? latitude,
    double? longitude,
    String? imagePath,
    String? projectId,
  }) async {
    final id = _uuid.v4();
    final now = DateTime.now();
    
    final issue = Issue(
      id: id,
      chainage: chainage,
      description: description,
      severity: severity,
      latitude: latitude,
      longitude: longitude,
      localImagePath: imagePath,
      timestamp: now,
      synced: false,
      createdAt: now,
    );
    
    // Save to local database
    await _db.insertIssue(issue.toMap());
    
    // Queue for sync
    await _db.addToSyncQueue(SyncQueueItem(
      id: _uuid.v4(),
      entityType: SyncEntityType.issue,
      entityId: id,
      operation: SyncOperation.create,
      payload: {
        'id': id,
        'chainage': chainage,
        'description': description,
        'severity': severity.name,
        'latitude': latitude,
        'longitude': longitude,
        'local_image_path': imagePath,
        'project_id': projectId,
        'timestamp': now.toIso8601String(),
      },
    ).toMap());
    
    return {
      'status': 'success',
      'id': id,
      'local': true,
      'message': 'Issue saved locally, will sync when online',
    };
  }

  /// Submit issue - tries online first, falls back to local
  Future<Map<String, dynamic>> submitIssue({
    required String chainage,
    required String description,
    IssueSeverity severity = IssueSeverity.medium,
    double? latitude,
    double? longitude,
    String? imagePath,
    String? projectId,
    bool forceOffline = false,
  }) async {
    // Try to submit online
    if (!forceOffline) {
      final result = await DashboardService.submitQualityIssue(
        chainage: chainage,
        description: description,
        severity: severity.name,
        latitude: latitude,
        longitude: longitude,
        imagePath: imagePath,
        projectId: projectId,
      );
      
      if (result['status'] == 'success') {
        // Save to local with synced flag
        final id = _uuid.v4();
        final now = DateTime.now();
        
        final issue = Issue(
          id: id,
          chainage: chainage,
          description: description,
          severity: severity,
          latitude: latitude,
          longitude: longitude,
          timestamp: now,
          synced: true,
          createdAt: now,
        );
        
        await _db.insertIssue(issue.toMap());
        
        return {
          'status': 'success',
          'id': id,
          'local': false,
          'data': result['data'],
        };
      }
    }
    
    // Fallback to local storage
    return await saveIssueLocal(
      chainage: chainage,
      description: description,
      severity: severity,
      latitude: latitude,
      longitude: longitude,
      imagePath: imagePath,
      projectId: projectId,
    );
  }

  /// Get all issues (local + synced)
  Future<List<Issue>> getAllIssues() async {
    final maps = await _db.getAllIssues();
    return maps.map((m) => Issue.fromMap(m)).toList();
  }

  /// Get unsynced issues
  Future<List<Issue>> getUnsyncedIssues() async {
    final maps = await _db.getUnsyncedIssues();
    return maps.map((m) => Issue.fromMap(m)).toList();
  }

  // ==================== SAFETY CHECK OPERATIONS ====================
  
  /// Save safety check locally and queue for sync
  Future<Map<String, dynamic>> saveSafetyCheckLocal({
    required String chainage,
    required SafetyCheckType checkType,
    SafetyStatus status = SafetyStatus.pending,
    String? description,
    String? findings,
    double? latitude,
    double? longitude,
    String? inspector,
    String? imagePath,
    String? projectId,
  }) async {
    final id = _uuid.v4();
    final now = DateTime.now();
    
    final safetyCheck = SafetyCheck(
      id: id,
      chainage: chainage,
      checkType: checkType,
      status: status,
      description: description,
      findings: findings,
      latitude: latitude,
      longitude: longitude,
      inspector: inspector,
      localImagePath: imagePath,
      timestamp: now,
      synced: false,
      createdAt: now,
    );
    
    // Save to local database
    await _db.insertSafetyCheck(safetyCheck.toMap());
    
    // Queue for sync
    await _db.addToSyncQueue(SyncQueueItem(
      id: _uuid.v4(),
      entityType: SyncEntityType.safetyCheck,
      entityId: id,
      operation: SyncOperation.create,
      payload: {
        'id': id,
        'chainage': chainage,
        'check_type': checkType.name,
        'status': status.name,
        'description': description,
        'findings': findings,
        'latitude': latitude,
        'longitude': longitude,
        'inspector': inspector,
        'local_image_path': imagePath,
        'project_id': projectId,
        'timestamp': now.toIso8601String(),
      },
    ).toMap());
    
    return {
      'status': 'success',
      'id': id,
      'local': true,
      'message': 'Safety check saved locally, will sync when online',
    };
  }

  /// Submit safety check - tries online first, falls back to local
  Future<Map<String, dynamic>> submitSafetyCheck({
    required String chainage,
    required SafetyCheckType checkType,
    SafetyStatus status = SafetyStatus.pending,
    String? description,
    String? findings,
    double? latitude,
    double? longitude,
    String? inspector,
    String? imagePath,
    String? projectId,
    bool forceOffline = false,
  }) async {
    // Try to submit online
    if (!forceOffline) {
      final result = await DashboardService.submitSafetyCheck(
        chainage: chainage,
        checkType: checkType.name,
        description: description,
        findings: findings,
        latitude: latitude,
        longitude: longitude,
        inspector: inspector,
        imagePath: imagePath,
        projectId: projectId,
      );
      
      if (result['status'] == 'success') {
        // Save to local with synced flag
        final id = _uuid.v4();
        final now = DateTime.now();
        
        final safetyCheck = SafetyCheck(
          id: id,
          chainage: chainage,
          checkType: checkType,
          status: status,
          description: description,
          findings: findings,
          latitude: latitude,
          longitude: longitude,
          inspector: inspector,
          timestamp: now,
          synced: true,
          createdAt: now,
        );
        
        await _db.insertSafetyCheck(safetyCheck.toMap());
        
        return {
          'status': 'success',
          'id': id,
          'local': false,
          'data': result['data'],
        };
      }
    }
    
    // Fallback to local storage
    return await saveSafetyCheckLocal(
      chainage: chainage,
      checkType: checkType,
      status: status,
      description: description,
      findings: findings,
      latitude: latitude,
      longitude: longitude,
      inspector: inspector,
      imagePath: imagePath,
      projectId: projectId,
    );
  }

  /// Get all safety checks (local + synced)
  Future<List<SafetyCheck>> getAllSafetyChecks() async {
    final maps = await _db.getAllSafetyChecks();
    return maps.map((m) => SafetyCheck.fromMap(m)).toList();
  }

  /// Get unsynced safety checks
  Future<List<SafetyCheck>> getUnsyncedSafetyChecks() async {
    final maps = await _db.getUnsyncedSafetyChecks();
    return maps.map((m) => SafetyCheck.fromMap(m)).toList();
  }

  // ==================== SYNC STATUS ====================
  
  /// Get pending sync count
  Future<int> getPendingSyncCount() async {
    return await _db.getPendingSyncCount();
  }

  /// Check if has unsynced data
  Future<bool> hasUnsyncedData() async {
    final pendingCount = await getPendingSyncCount();
    return pendingCount > 0;
  }
}
