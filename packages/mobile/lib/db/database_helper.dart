import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/models.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('neuralsite.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 3, // Bumped version for progress work_type/quantity/unit columns
      onCreate: _createDB,
      onUpgrade: _upgradeDB,
    );
  }

  Future<void> _upgradeDB(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      // Add new tables for v2
      await _createV2Tables(db);
    }
    if (oldVersion < 3) {
      // Add new columns for progress table in v3
      await db.execute('ALTER TABLE progress ADD COLUMN work_type TEXT');
      await db.execute('ALTER TABLE progress ADD COLUMN quantity REAL');
      await db.execute('ALTER TABLE progress ADD COLUMN unit TEXT');
    }
  }

  Future<void> _createDB(Database db, int version) async {
    // Issues table
    await db.execute('''
      CREATE TABLE issues (
        id TEXT PRIMARY KEY,
        chainage TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT,
        image_url TEXT,
        latitude REAL,
        longitude REAL,
        timestamp TEXT NOT NULL,
        synced INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1,
        local_version INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        deleted_at TEXT
      )
    ''');

    // Progress table
    await db.execute('''
      CREATE TABLE progress (
        id TEXT PRIMARY KEY,
        chainage TEXT NOT NULL,
        status TEXT NOT NULL,
        note TEXT,
        latitude REAL,
        longitude REAL,
        work_type TEXT,
        quantity REAL,
        unit TEXT,
        timestamp TEXT NOT NULL,
        synced INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1,
        local_version INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        deleted_at TEXT
      )
    ''');

    // Safety checks table
    await db.execute('''
      CREATE TABLE safety_checks (
        id TEXT PRIMARY KEY,
        chainage TEXT NOT NULL,
        check_type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        description TEXT,
        findings TEXT,
        image_url TEXT,
        local_image_path TEXT,
        latitude REAL,
        longitude REAL,
        inspector TEXT,
        timestamp TEXT NOT NULL,
        synced INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT
      )
    ''');

    // AI detections table
    await db.execute('''
      CREATE TABLE ai_detections (
        id TEXT PRIMARY KEY,
        photo_id TEXT,
        local_image_path TEXT,
        remote_image_url TEXT,
        status TEXT DEFAULT 'pending',
        summary TEXT,
        confidence REAL DEFAULT 0.0,
        results TEXT,
        analyzed_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    ''');

    // Approvals table
    await db.execute('''
      CREATE TABLE approvals (
        id TEXT PRIMARY KEY,
        detection_id TEXT NOT NULL,
        approver TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        comment TEXT,
        timestamp TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    ''');

    // Photos table
    await db.execute('''
      CREATE TABLE photos (
        id TEXT PRIMARY KEY,
        local_path TEXT,
        remote_url TEXT,
        latitude REAL,
        longitude REAL,
        chainage TEXT,
        project_id TEXT,
        captured_at TEXT NOT NULL,
        description TEXT,
        sync_status TEXT DEFAULT 'pending',
        version INTEGER DEFAULT 1,
        local_version INTEGER DEFAULT 1,
        file_size INTEGER,
        checksum TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        deleted_at TEXT
      )
    ''');

    // Projects table
    await db.execute('''
      CREATE TABLE projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        route_id TEXT,
        start_station REAL,
        end_station REAL,
        status TEXT DEFAULT 'active',
        is_active INTEGER DEFAULT 1,
        version INTEGER DEFAULT 1,
        local_version INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        deleted_at TEXT
      )
    ''');

    // Sync queue table
    await db.execute('''
      CREATE TABLE sync_queue (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        operation TEXT NOT NULL,
        payload TEXT,
        retry_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_attempt_at TEXT,
        completed_at TEXT,
        priority INTEGER DEFAULT 0
      )
    ''');

    // Create indexes for better query performance
    await db.execute('CREATE INDEX idx_photos_sync_status ON photos(sync_status)');
    await db.execute('CREATE INDEX idx_photos_project ON photos(project_id)');
    await db.execute('CREATE INDEX idx_issues_synced ON issues(synced)');
    await db.execute('CREATE INDEX idx_sync_queue_status ON sync_queue(status)');
    await db.execute('CREATE INDEX idx_projects_active ON projects(is_active)');
    
    // Create v2 tables
    await _createV2Tables(db);
  }

  Future<void> _createV2Tables(Database db) async {
    // ==================== NEW TABLES FOR OFFLINE SYNC ENHANCEMENT ====================
    
    // Conflict log table - records all sync conflicts
    await db.execute('''
      CREATE TABLE conflict_logs (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        local_data TEXT NOT NULL,
        remote_data TEXT NOT NULL,
        conflict_type TEXT NOT NULL,
        resolution TEXT DEFAULT 'pending',
        resolved_at TEXT,
        resolved_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    ''');
    await db.execute('CREATE INDEX idx_conflict_entity ON conflict_logs(entity_type, entity_id)');
    await db.execute('CREATE INDEX idx_conflict_resolution ON conflict_logs(resolution)');

    // Chunked upload state table - tracks resumable uploads
    await db.execute('''
      CREATE TABLE chunked_uploads (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        chunk_size INTEGER DEFAULT 1048576,
        total_chunks INTEGER NOT NULL,
        uploaded_chunks INTEGER DEFAULT 0,
        upload_id TEXT,
        status TEXT DEFAULT 'pending',
        progress REAL DEFAULT 0,
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        completed_at TEXT
      )
    ''');
    await db.execute('CREATE INDEX idx_chunked_status ON chunked_uploads(status)');
    await db.execute('CREATE INDEX idx_chunked_entity ON chunked_uploads(entity_type, entity_id)');

    // Change log table - tracks incremental changes for sync
    await db.execute('''
      CREATE TABLE change_logs (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        field_name TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        change_type TEXT NOT NULL,
        synced INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    ''');
    await db.execute('CREATE INDEX idx_change_entity ON change_logs(entity_type, entity_id)');
    await db.execute('CREATE INDEX idx_change_synced ON change_logs(synced)');

    // Offline cache - drawings (blueprints)
    await db.execute('''
      CREATE TABLE cached_drawings (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        version INTEGER DEFAULT 1,
        downloaded_at TEXT,
        expires_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    ''');
    await db.execute('CREATE INDEX idx_drawings_project ON cached_drawings(project_id)');

    // Offline cache - specifications (规范条文)
    await db.execute('''
      CREATE TABLE cached_specifications (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT,
        version INTEGER DEFAULT 1,
        downloaded_at TEXT,
        expires_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    ''');
    await db.execute('CREATE INDEX idx_specs_project ON cached_specifications(project_id)');
    await db.execute('CREATE INDEX idx_specs_category ON cached_specifications(category)');

    // Sync metadata - tracks last sync times per entity
    await db.execute('''
      CREATE TABLE sync_metadata (
        entity_type TEXT PRIMARY KEY,
        last_sync_at TEXT,
        last_sync_version INTEGER DEFAULT 0,
        sync_token TEXT,
        updated_at TEXT
      )
    ''');
  }

  // ==================== Photo Operations ====================

  Future<int> insertPhoto(Photo photo) async {
    final db = await database;
    return await db.insert(
      'photos',
      photo.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<Photo?> getPhoto(String id) async {
    final db = await database;
    final maps = await db.query(
      'photos',
      where: 'id = ? AND deleted_at IS NULL',
      whereArgs: [id],
    );
    if (maps.isEmpty) return null;
    return Photo.fromMap(maps.first);
  }

  Future<List<Photo>> getAllPhotos({String? projectId}) async {
    final db = await database;
    final maps = await db.query(
      'photos',
      where: (projectId != null ? 'project_id = ? AND ' : '') + 'deleted_at IS NULL',
      whereArgs: projectId != null ? [projectId] : null,
      orderBy: 'captured_at DESC',
    );
    return maps.map((m) => Photo.fromMap(m)).toList();
  }

  Future<List<Photo>> getUnsyncedPhotos() async {
    final db = await database;
    final maps = await db.query(
      'photos',
      where: "sync_status IN ('pending', 'failed') AND deleted_at IS NULL",
    );
    return maps.map((m) => Photo.fromMap(m)).toList();
  }

  Future<int> updatePhoto(Photo photo) async {
    final db = await database;
    // Log the change for incremental sync
    await _logChange('photo', photo.id, photo.toMap());
    
    return await db.update(
      'photos',
      photo.toMap(),
      where: 'id = ?',
      whereArgs: [photo.id],
    );
  }

  Future<int> updatePhotoSyncStatus(String id, PhotoSyncStatus status, {String? remoteUrl}) async {
    final db = await database;
    final updates = <String, dynamic>{
      'sync_status': status.name,
      'updated_at': DateTime.now().toIso8601String(),
    };
    if (remoteUrl != null) {
      updates['remote_url'] = remoteUrl;
    }
    return await db.update(
      'photos',
      updates,
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> softDeletePhoto(String id) async {
    final db = await database;
    // Log deletion for sync
    await _logChange('photo', id, {'deleted': true}, changeType: 'delete');
    
    return await db.update(
      'photos',
      {
        'deleted_at': DateTime.now().toIso8601String(),
        'sync_status': PhotoSyncStatus.pending.name,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> deletePhoto(String id) async {
    final db = await database;
    return await db.delete(
      'photos',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // ==================== Project Operations ====================

  Future<int> insertProject(Project project) async {
    final db = await database;
    return await db.insert(
      'projects',
      project.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<Project?> getProject(String id) async {
    final db = await database;
    final maps = await db.query(
      'projects',
      where: 'id = ? AND deleted_at IS NULL',
      whereArgs: [id],
    );
    if (maps.isEmpty) return null;
    return Project.fromMap(maps.first);
  }

  Future<List<Project>> getAllProjects({bool activeOnly = true}) async {
    final db = await database;
    final maps = await db.query(
      'projects',
      where: (activeOnly ? 'is_active = 1 AND ' : '') + 'deleted_at IS NULL',
      orderBy: 'created_at DESC',
    );
    return maps.map((m) => Project.fromMap(m)).toList();
  }

  Future<Project?> getActiveProject() async {
    final db = await database;
    final maps = await db.query(
      'projects',
      where: "is_active = 1 AND status = 'active' AND deleted_at IS NULL",
      limit: 1,
    );
    if (maps.isEmpty) return null;
    return Project.fromMap(maps.first);
  }

  Future<int> updateProject(Project project) async {
    final db = await database;
    // Log the change for incremental sync
    await _logChange('project', project.id, project.toMap());
    
    return await db.update(
      'projects',
      project.toMap(),
      where: 'id = ?',
      whereArgs: [project.id],
    );
  }

  // ==================== Issue Operations ====================

  Future<int> insertIssue(Map<String, dynamic> issue) async {
    final db = await database;
    return await db.insert(
      'issues',
      issue,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getUnsyncedIssues() async {
    final db = await database;
    return await db.query('issues', where: 'synced = ? AND deleted_at IS NULL', whereArgs: [0]);
  }

  Future<int> markIssueSynced(int id) async {
    final db = await database;
    return await db.update(
      'issues',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<List<Map<String, dynamic>>> getAllIssues() async {
    final db = await database;
    return await db.query('issues', where: 'deleted_at IS NULL', orderBy: 'timestamp DESC');
  }

  // ==================== Progress Operations ====================

  Future<int> insertProgress(Map<String, dynamic> progress) async {
    final db = await database;
    return await db.insert(
      'progress',
      progress,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getUnsyncedProgress() async {
    final db = await database;
    return await db.query('progress', where: 'synced = ? AND deleted_at IS NULL', whereArgs: [0]);
  }

  Future<List<Map<String, dynamic>>> getAllProgress() async {
    final db = await database;
    return await db.query('progress', where: 'deleted_at IS NULL', orderBy: 'timestamp DESC');
  }

  Future<int> markProgressSynced(String id) async {
    final db = await database;
    return await db.update(
      'progress',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // ==================== Safety Check Operations ====================

  Future<int> insertSafetyCheck(Map<String, dynamic> safetyCheck) async {
    final db = await database;
    return await db.insert(
      'safety_checks',
      safetyCheck,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getAllSafetyChecks() async {
    final db = await database;
    return await db.query('safety_checks', where: 'deleted_at IS NULL', orderBy: 'timestamp DESC');
  }

  Future<List<Map<String, dynamic>>> getUnsyncedSafetyChecks() async {
    final db = await database;
    return await db.query('safety_checks', where: 'synced = ? AND deleted_at IS NULL', whereArgs: [0]);
  }

  Future<int> markSafetyCheckSynced(String id) async {
    final db = await database;
    return await db.update(
      'safety_checks',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // ==================== AI Detection Operations ====================

  Future<int> insertDetection(Map<String, dynamic> detection) async {
    final db = await database;
    return await db.insert(
      'ai_detections',
      detection,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getAllDetections() async {
    final db = await database;
    return await db.query('ai_detections', orderBy: 'created_at DESC');
  }

  Future<Map<String, dynamic>?> getDetectionByPhotoId(String photoId) async {
    final db = await database;
    final results = await db.query('ai_detections', where: 'photo_id = ?', whereArgs: [photoId]);
    return results.isNotEmpty ? results.first : null;
  }

  Future<int> updateDetectionStatus(String id, String status) async {
    final db = await database;
    return await db.update(
      'ai_detections',
      {'status': status},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // ==================== Approval Operations ====================

  Future<int> insertApproval(Map<String, dynamic> approval) async {
    final db = await database;
    return await db.insert(
      'approvals',
      approval,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getPendingApprovals() async {
    final db = await database;
    return await db.query('approvals', where: "status = 'pending'", orderBy: 'timestamp DESC');
  }

  Future<int> updateApprovalStatus(String id, String status, {String? comment}) async {
    final db = await database;
    return await db.update(
      'approvals',
      {'status': status, if (comment != null) 'comment': comment},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // ==================== Spatial Points Cache ====================

  Future<int> insertSpatialPoint(Map<String, dynamic> point) async {
    final db = await database;
    return await db.insert(
      'spatial_points',
      point,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getNearbyPoints(double lat, double lon, double radius) async {
    final db = await database;
    // Simple distance calculation (for offline use)
    // In production, use PostGIS on server
    return await db.query('spatial_points');
  }

  // ==================== Sync Queue Operations ====================

  Future<int> addToSyncQueue(SyncQueueItem item) async {
    final db = await database;
    return await db.insert(
      'sync_queue',
      item.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<SyncQueueItem>> getPendingSyncItems({int limit = 50}) async {
    final db = await database;
    final maps = await db.query(
      'sync_queue',
      where: "status IN ('pending', 'failed') AND retry_count < 3",
      orderBy: 'priority DESC, created_at ASC',
      limit: limit,
    );
    return maps.map((m) => SyncQueueItem.fromMap(m)).toList();
  }

  Future<int> updateSyncQueueItem(SyncQueueItem item) async {
    final db = await database;
    return await db.update(
      'sync_queue',
      item.toMap(),
      where: 'id = ?',
      whereArgs: [item.id],
    );
  }

  Future<int> markSyncItemCompleted(String id) async {
    final db = await database;
    return await db.update(
      'sync_queue',
      {
        'status': SyncQueueStatus.completed.name,
        'completed_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> markSyncItemFailed(String id, String error) async {
    final db = await database;
    return await db.update(
      'sync_queue',
      {
        'status': SyncQueueStatus.failed.name,
        'error_message': error,
        'last_attempt_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> incrementSyncRetry(String id) async {
    final db = await database;
    return await db.rawUpdate(
      'UPDATE sync_queue SET retry_count = retry_count + 1, last_attempt_at = ? WHERE id = ?',
      [DateTime.now().toIso8601String(), id],
    );
  }

  Future<int> getPendingSyncCount() async {
    final db = await database;
    final result = await db.rawQuery(
      "SELECT COUNT(*) as count FROM sync_queue WHERE status IN ('pending', 'failed') AND retry_count < 3",
    );
    return result.first['count'] as int? ?? 0;
  }

  Future<void> clearCompletedSyncItems({int olderThanDays = 7}) async {
    final db = await database;
    final cutoff = DateTime.now()
        .subtract(Duration(days: olderThanDays))
        .toIso8601String();
    await db.delete(
      'sync_queue',
      where: "status = 'completed' AND completed_at < ?",
      whereArgs: [cutoff],
    );
  }

  // ==================== CONFLICT LOG OPERATIONS ====================
  
  /// Log a conflict for later resolution
  Future<int> logConflict(SyncConflict conflict) async {
    final db = await database;
    return await db.insert('conflict_logs', {
      'id': conflict.entityType + '_' + conflict.entityId + '_' + DateTime.now().millisecondsSinceEpoch.toString(),
      'entity_type': conflict.entityType,
      'entity_id': conflict.entityId,
      'local_data': jsonEncode(conflict.localData),
      'remote_data': jsonEncode(conflict.remoteData),
      'conflict_type': 'version_mismatch',
      'resolution': conflict.resolution.name,
      'created_at': DateTime.now().toIso8601String(),
    });
  }

  /// Get all unresolved conflicts
  Future<List<Map<String, dynamic>>> getUnresolvedConflicts() async {
    final db = await database;
    return await db.query(
      'conflict_logs',
      where: "resolution = 'pending' OR resolution = 'manual'",
      orderBy: 'created_at DESC',
    );
  }

  /// Resolve a conflict
  Future<int> resolveConflict(String id, ConflictResolution resolution, {String? resolvedBy}) async {
    final db = await database;
    return await db.update('conflict_logs', {
      'resolution': resolution.name,
      'resolved_at': DateTime.now().toIso8601String(),
      'resolved_by': resolvedBy ?? 'system',
    }, where: 'id = ?', whereArgs: [id]);
  }

  // ==================== CHUNKED UPLOAD OPERATIONS ====================
  
  /// Start a chunked upload
  Future<int> startChunkedUpload(ChunkedUpload upload) async {
    final db = await database;
    return await db.insert('chunked_uploads', upload.toMap());
  }

  /// Update chunked upload progress
  Future<int> updateChunkedUploadProgress(String id, int uploadedChunks, double progress) async {
    final db = await database;
    return await db.update('chunked_uploads', {
      'uploaded_chunks': uploadedChunks,
      'progress': progress,
      'updated_at': DateTime.now().toIso8601String(),
    }, where: 'id = ?', whereArgs: [id]);
  }

  /// Get pending chunked uploads
  Future<List<ChunkedUpload>> getPendingChunkedUploads() async {
    final db = await database;
    final maps = await db.query(
      'chunked_uploads',
      where: "status IN ('pending', 'in_progress', 'failed')",
      orderBy: 'created_at ASC',
    );
    return maps.map((m) => ChunkedUpload.fromMap(m)).toList();
  }

  /// Mark chunked upload completed
  Future<int> completeChunkedUpload(String id, String uploadId) async {
    final db = await database;
    return await db.update('chunked_uploads', {
      'status': 'completed',
      'upload_id': uploadId,
      'uploaded_chunks': await _getChunkedUploadTotalChunks(id),
      'progress': 1.0,
      'completed_at': DateTime.now().toIso8601String(),
    }, where: 'id = ?', whereArgs: [id]);
  }

  Future<int> _getChunkedUploadTotalChunks(String id) async {
    final db = await database;
    final result = await db.query('chunked_uploads', where: 'id = ?', whereArgs: [id]);
    if (result.isEmpty) return 0;
    return result.first['total_chunks'] as int? ?? 0;
  }

  /// Mark chunked upload failed
  Future<int> failChunkedUpload(String id, String error) async {
    final db = await database;
    return await db.update('chunked_uploads', {
      'status': 'failed',
      'error_message': error,
      'updated_at': DateTime.now().toIso8601String(),
    }, where: 'id = ?', whereArgs: [id]);
  }

  // ==================== CHANGE LOG OPERATIONS ====================
  
  /// Log a field change for incremental sync
  Future<void> _logChange(String entityType, String entityId, Map<String, dynamic> data, {String changeType = 'update'}) async {
    final db = await database;
    for (final entry in data.entries) {
      await db.insert('change_logs', {
        'id': '${entityType}_${entityId}_${entry.key}_${DateTime.now().millisecondsSinceEpoch}',
        'entity_type': entityType,
        'entity_id': entityId,
        'field_name': entry.key,
        'new_value': entry.value?.toString(),
        'change_type': changeType,
        'created_at': DateTime.now().toIso8601String(),
      });
    }
  }

  /// Get pending changes for incremental sync
  Future<List<Map<String, dynamic>>> getPendingChanges({String? entityType, int limit = 100}) async {
    final db = await database;
    return await db.query(
      'change_logs',
      where: entityType != null ? 'entity_type = ? AND synced = 0' : 'synced = 0',
      whereArgs: entityType != null ? [entityType] : null,
      orderBy: 'created_at ASC',
      limit: limit,
    );
  }

  /// Mark changes as synced
  Future<void> markChangesSynced(List<String> changeIds) async {
    final db = await database;
    final batch = db.batch();
    for (final id in changeIds) {
      batch.update('change_logs', {'synced': 1}, where: 'id = ?', whereArgs: [id]);
    }
    await batch.commit(noResult: true);
  }

  /// Clear old change logs
  Future<void> clearOldChangeLogs({int olderThanDays = 7}) async {
    final db = await database;
    final cutoff = DateTime.now().subtract(Duration(days: olderThanDays)).toIso8601String();
    await db.delete('change_logs', where: 'synced = 1 AND created_at < ?', whereArgs: [cutoff]);
  }

  // ==================== SYNC METADATA OPERATIONS ====================
  
  /// Update sync metadata
  Future<void> updateSyncMetadata(String entityType, {String? syncToken, int? lastVersion}) async {
    final db = await database;
    await db.insert('sync_metadata', {
      'entity_type': entityType,
      'last_sync_at': DateTime.now().toIso8601String(),
      'sync_token': syncToken,
      'last_sync_version': lastVersion ?? 0,
      'updated_at': DateTime.now().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  /// Get sync metadata
  Future<Map<String, dynamic>?> getSyncMetadata(String entityType) async {
    final db = await database;
    final result = await db.query('sync_metadata', where: 'entity_type = ?', whereArgs: [entityType]);
    return result.isNotEmpty ? result.first : null;
  }

  // ==================== OFFLINE CACHE OPERATIONS ====================
  
  /// Cache a drawing (blueprint)
  Future<int> cacheDrawing(Map<String, dynamic> drawing) async {
    final db = await database;
    return await db.insert('cached_drawings', drawing, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  /// Get cached drawings for a project
  Future<List<Map<String, dynamic>>> getCachedDrawings(String projectId) async {
    final db = await database;
    return await db.query(
      'cached_drawings',
      where: 'project_id = ? AND (expires_at IS NULL OR expires_at > ?)',
      whereArgs: [projectId, DateTime.now().toIso8601String()],
    );
  }

  /// Cache a specification (规范条文)
  Future<int> cacheSpecification(Map<String, dynamic> spec) async {
    final db = await database;
    return await db.insert('cached_specifications', spec, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  /// Get cached specifications for a project
  Future<List<Map<String, dynamic>>> getCachedSpecifications(String projectId, {String? category}) async {
    final db = await database;
    return await db.query(
      'cached_specifications',
      where: 'project_id = ? AND (expires_at IS NULL OR expires_at > ?)' + (category != null ? ' AND category = ?' : ''),
      whereArgs: category != null ? [projectId, DateTime.now().toIso8601String(), category] : [projectId, DateTime.now().toIso8601String()],
    );
  }

  /// Clear expired cache
  Future<void> clearExpiredCache() async {
    final db = await database;
    final now = DateTime.now().toIso8601String();
    await db.delete('cached_drawings', where: 'expires_at < ?', whereArgs: [now]);
    await db.delete('cached_specifications', where: 'expires_at < ?', whereArgs: [now]);
  }

  // ==================== Utility ====================

  Future<void> close() async {
    final db = await database;
    await db.close();
    _database = null;
  }

  Future<void> clearAllData() async {
    final db = await database;
    await db.delete('photos');
    await db.delete('projects');
    await db.delete('issues');
    await db.delete('progress');
    await db.delete('spatial_points');
    await db.delete('sync_queue');
    await db.delete('conflict_logs');
    await db.delete('chunked_uploads');
    await db.delete('change_logs');
    await db.delete('cached_drawings');
    await db.delete('cached_specifications');
    await db.delete('sync_metadata');
    await db.delete('safety_checks');
    await db.delete('ai_detections');
    await db.delete('approvals');
  }
}

/// Chunked upload model for resumable uploads
class ChunkedUpload {
  final String id;
  final String entityType;
  final String entityId;
  final String filePath;
  final int fileSize;
  final int chunkSize;
  final int totalChunks;
  final int uploadedChunks;
  final String? uploadId;
  final String status;
  final double progress;
  final String? errorMessage;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final DateTime? completedAt;

  ChunkedUpload({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.filePath,
    required this.fileSize,
    this.chunkSize = 1024 * 1024, // 1MB default
    required this.totalChunks,
    this.uploadedChunks = 0,
    this.uploadId,
    this.status = 'pending',
    this.progress = 0,
    this.errorMessage,
    DateTime? createdAt,
    this.updatedAt,
    this.completedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  factory ChunkedUpload.fromMap(Map<String, dynamic> map) {
    return ChunkedUpload(
      id: map['id'] as String,
      entityType: map['entity_type'] as String,
      entityId: map['entity_id'] as String,
      filePath: map['file_path'] as String,
      fileSize: map['file_size'] as int,
      chunkSize: map['chunk_size'] as int? ?? 1024 * 1024,
      totalChunks: map['total_chunks'] as int,
      uploadedChunks: map['uploaded_chunks'] as int? ?? 0,
      uploadId: map['upload_id'] as String?,
      status: map['status'] as String? ?? 'pending',
      progress: (map['progress'] as num?)?.toDouble() ?? 0,
      errorMessage: map['error_message'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: map['updated_at'] != null ? DateTime.parse(map['updated_at'] as String) : null,
      completedAt: map['completed_at'] != null ? DateTime.parse(map['completed_at'] as String) : null,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'entity_type': entityType,
      'entity_id': entityId,
      'file_path': filePath,
      'file_size': fileSize,
      'chunk_size': chunkSize,
      'total_chunks': totalChunks,
      'uploaded_chunks': uploadedChunks,
      'upload_id': uploadId,
      'status': status,
      'progress': progress,
      'error_message': errorMessage,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'completed_at': completedAt?.toIso8601String(),
    };
  }

  ChunkedUpload copyWith({
    String? id,
    String? entityType,
    String? entityId,
    String? filePath,
    int? fileSize,
    int? chunkSize,
    int? totalChunks,
    int? uploadedChunks,
    String? uploadId,
    String? status,
    double? progress,
    String? errorMessage,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? completedAt,
  }) {
    return ChunkedUpload(
      id: id ?? this.id,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      filePath: filePath ?? this.filePath,
      fileSize: fileSize ?? this.fileSize,
      chunkSize: chunkSize ?? this.chunkSize,
      totalChunks: totalChunks ?? this.totalChunks,
      uploadedChunks: uploadedChunks ?? this.uploadedChunks,
      uploadId: uploadId ?? this.uploadId,
      status: status ?? this.status,
      progress: progress ?? this.progress,
      errorMessage: errorMessage ?? this.errorMessage,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }
}
