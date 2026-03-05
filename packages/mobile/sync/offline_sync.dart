// NeuralSite 移动端离线同步模块
// 对应 P0 优先级功能

import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

// ==================== 数据模型 ====================

class SyncItem {
  final String entityType; // photo/issue
  final String localId;
  final String operation; // create/update/delete
  final Map<String, dynamic> data;
  final DateTime createdAt;
  String status; // pending/synced/conflict/failed
  
  SyncItem({
    required this.entityType,
    required this.localId,
    required this.operation,
    required this.data,
    required this.createdAt,
    this.status = 'pending',
  });
  
  Map<String, dynamic> toJson() => {
    'entity_type': entityType,
    'local_id': localId,
    'operation': operation,
    'data': data,
    'created_at': createdAt.toIso8601String(),
    'status': status,
  };
  
  factory SyncItem.fromJson(Map<String, dynamic> json) => SyncItem(
    entityType: json['entity_type'],
    localId: json['local_id'],
    operation: json['operation'],
    data: json['data'],
    createdAt: DateTime.parse(json['created_at']),
    status: json['status'] ?? 'pending',
  );
}

class PhotoRecord {
  String? localId;
  String? serverId;
  String projectId;
  String filePath;
  DateTime capturedAt;
  double? latitude;
  double? longitude;
  double? station;
  String? stationDisplay;
  String? description;
  String? capturedBy;
  String? syncStatus;
  
  PhotoRecord({
    this.localId,
    this.serverId,
    required this.projectId,
    required this.filePath,
    required this.capturedAt,
    this.latitude,
    this.longitude,
    this.station,
    this.stationDisplay,
    this.description,
    this.capturedBy,
    this.syncStatus = 'pending',
  });
  
  Map<String, dynamic> toJson() => {
    'local_id': localId,
    'project_id': projectId,
    'file_path': filePath,
    'captured_at': capturedAt.toIso8601String(),
    'latitude': latitude,
    'longitude': longitude,
    'station': station,
    'station_display': stationDisplay,
    'description': description,
    'captured_by': capturedBy,
    'sync_status': syncStatus,
  };
  
  factory PhotoRecord.fromJson(Map<String, dynamic> json) => PhotoRecord(
    localId: json['local_id'],
    serverId: json['server_id'],
    projectId: json['project_id'],
    filePath: json['file_path'],
    capturedAt: DateTime.parse(json['captured_at']),
    latitude: json['latitude']?.toDouble(),
    longitude: json['longitude']?.toDouble(),
    station: json['station']?.toDouble(),
    stationDisplay: json['station_display'],
    description: json['description'],
    capturedBy: json['captured_by'],
    syncStatus: json['sync_status'],
  );
}

class IssueRecord {
  String? localId;
  String? serverId;
  String projectId;
  String issueType; // quality/safety/progress
  String title;
  String? description;
  String severity; // critical/major/minor
  double? station;
  String? stationDisplay;
  double? latitude;
  double? longitude;
  String? locationDescription;
  List<String> photoIds;
  String status; // open/in_progress/resolved/closed
  DateTime? deadline;
  String? syncStatus;
  
  IssueRecord({
    this.localId,
    this.serverId,
    required this.projectId,
    required this.issueType,
    required this.title,
    this.description,
    this.severity = 'medium',
    this.station,
    this.stationDisplay,
    this.latitude,
    this.longitude,
    this.locationDescription,
    this.photoIds = const [],
    this.status = 'open',
    this.deadline,
    this.syncStatus = 'pending',
  });
  
  Map<String, dynamic> toJson() => {
    'local_id': localId,
    'project_id': projectId,
    'issue_type': issueType,
    'title': title,
    'description': description,
    'severity': severity,
    'station': station,
    'station_display': stationDisplay,
    'latitude': latitude,
    'longitude': longitude,
    'location_description': locationDescription,
    'photo_ids': photoIds,
    'status': status,
    'deadline': deadline?.toIso8601String(),
    'sync_status': syncStatus,
  };
  
  factory IssueRecord.fromJson(Map<String, dynamic> json) => IssueRecord(
    localId: json['local_id'],
    serverId: json['server_id'],
    projectId: json['project_id'],
    issueType: json['issue_type'],
    title: json['title'],
    description: json['description'],
    severity: json['severity'] ?? 'medium',
    station: json['station']?.toDouble(),
    stationDisplay: json['station_display'],
    latitude: json['latitude']?.toDouble(),
    longitude: json['longitude']?.toDouble(),
    locationDescription: json['location_description'],
    photoIds: List<String>.from(json['photo_ids'] ?? []),
    status: json['status'] ?? 'open',
    deadline: json['deadline'] != null ? DateTime.parse(json['deadline']) : null,
    syncStatus: json['sync_status'],
  );
}

// ==================== 本地数据库 ====================

class LocalDatabase {
  static Database? _db;
  
  static Future<Database> get instance async {
    if (_db != null) return _db!;
    _db = await _initDatabase();
    return _db!;
  }
  
  static Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'neuralsite.db');
    
    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        // 照片表
        await db.execute('''
          CREATE TABLE photos (
            local_id TEXT PRIMARY KEY,
            server_id TEXT,
            project_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            station REAL,
            station_display TEXT,
            description TEXT,
            captured_by TEXT,
            sync_status TEXT DEFAULT 'pending'
          )
        ''');
        
        // 问题表
        await db.execute('''
          CREATE TABLE issues (
            local_id TEXT PRIMARY KEY,
            server_id TEXT,
            project_id TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'medium',
            station REAL,
            station_display TEXT,
            latitude REAL,
            longitude REAL,
            location_description TEXT,
            photo_ids TEXT,
            status TEXT DEFAULT 'open',
            deadline TEXT,
            sync_status TEXT DEFAULT 'pending'
          )
        ''');
        
        // 同步队列表
        await db.execute('''
          CREATE TABLE sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            local_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
          )
        ''');
        
        // 同步状态表
        await db.execute('''
          CREATE TABLE sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT
          )
        ''');
      },
    );
  }
  
  // ==================== 照片操作 ====================
  
  Future<void> insertPhoto(PhotoRecord photo) async {
    final db = await instance;
    await db.insert(
      'photos',
      {
        ...photo.toJson(),
        'local_id': photo.localId ?? DateTime.now().millisecondsSinceEpoch.toString(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }
  
  Future<List<PhotoRecord>> getPendingPhotos() async {
    final db = await instance;
    final results = await db.query(
      'photos',
      where: 'sync_status = ?',
      whereArgs: ['pending'],
    );
    return results.map((r) => PhotoRecord.fromJson(r)).toList();
  }
  
  Future<void> updatePhotoSyncStatus(String localId, String status, {String? serverId}) async {
    final db = await instance;
    final update = {'sync_status': status};
    if (serverId != null) update['server_id'] = serverId;
    await db.update('photos', update, where: 'local_id = ?', whereArgs: [localId]);
  }
  
  // ==================== 问题操作 ====================
  
  Future<void> insertIssue(IssueRecord issue) async {
    final db = await instance;
    await db.insert(
      'issues',
      {
        ...issue.toJson(),
        'local_id': issue.localId ?? DateTime.now().millisecondsSinceEpoch.toString(),
        'photo_ids': jsonEncode(issue.photoIds),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }
  
  Future<List<IssueRecord>> getPendingIssues() async {
    final db = await instance;
    final results = await db.query(
      'issues',
      where: 'sync_status = ?',
      whereArgs: ['pending'],
    );
    return results.map((r) => IssueRecord.fromJson({
      ...r,
      'photo_ids': jsonDecode(r['photo_ids'] as String? ?? '[]'),
    })).toList();
  }
  
  Future<void> updateIssueSyncStatus(String localId, String status, {String? serverId}) async {
    final db = await instance;
    final update = {'sync_status': status};
    if (serverId != null) update['server_id'] = serverId;
    await db.update('issues', update, where: 'local_id = ?', whereArgs: [localId]);
  }
  
  // ==================== 同步队列操作 ====================
  
  Future<void> addToSyncQueue(SyncItem item) async {
    final db = await instance;
    await db.insert('sync_queue', {
      ...item.toJson(),
      'data': jsonEncode(item.data),
    });
  }
  
  Future<List<SyncItem>> getPendingSyncItems() async {
    final db = await instance;
    final results = await db.query(
      'sync_queue',
      where: 'status = ?',
      whereArgs: ['pending'],
      orderBy: 'created_at ASC',
    );
    return results.map((r) => SyncItem.fromJson({
      ...r,
      'data': jsonDecode(r['data'] as String),
    })).toList();
  }
  
  Future<void> updateSyncItemStatus(int id, String status) async {
    final db = await instance;
    await db.update('sync_queue', {'status': status}, where: 'id = ?', whereArgs: [id]);
  }
  
  // ==================== 元数据 ====================
  
  Future<DateTime?> getLastSyncTime() async {
    final db = await instance;
    final results = await db.query('sync_meta', where: 'key = ?', whereArgs: ['last_sync_time']);
    if (results.isEmpty) return null;
    return DateTime.parse(results.first['value'] as String);
  }
  
  Future<void> setLastSyncTime(DateTime time) async {
    final db = await instance;
    await db.insert('sync_meta', {'key': 'last_sync_time', 'value': time.toIso8601String()});
  }
}

// ==================== 同步管理器 ====================

class OfflineSyncManager {
  final String baseUrl;
  final String deviceId;
  final String appVersion;
  final LocalDatabase _db = LocalDatabase();
  
  bool _isSyncing = false;
  bool get isSyncing => _isSyncing;
  
  // 网络状态回调
  Function(bool isOnline)? onNetworkStatusChanged;
  
  OfflineSyncManager({
    required this.baseUrl,
    required this.deviceId,
    required this.appVersion,
  });
  
  /// 检查网络状态并自动同步
  Future<void> checkAndSync(bool isOnline) async {
    if (!isOnline) {
      onNetworkStatusChanged?.call(false);
      return;
    }
    
    onNetworkStatusChanged?.call(true);
    await sync();
  }
  
  /// 手动触发同步
  Future<SyncResult> sync() async {
    if (_isSyncing) {
      return SyncResult(success: false, message: '同步正在进行中');
    }
    
    _isSyncing = true;
    final result = SyncResult();
    
    try {
      // 1. 获取待同步的照片
      final pendingPhotos = await _db.getPendingPhotos();
      
      // 2. 获取待同步的问题
      final pendingIssues = await _db.getPendingIssues();
      
      // 3. 批量推送到服务器
      if (pendingPhotos.isNotEmpty || pendingIssues.isNotEmpty) {
        final response = await _pushToServer({
          'photos': pendingPhotos.map((p) => p.toJson()).toList(),
          'issues': pendingIssues.map((i) => i.toJson()).toList(),
        });
        
        if (response['synced'] != null) {
          // 更新本地状态
          for (final photo in pendingPhotos) {
            await _db.updatePhotoSyncStatus(photo.localId!, 'synced');
          }
          for (final issue in pendingIssues) {
            await _db.updateIssueSyncStatus(issue.localId!, 'synced');
          }
          result.syncedCount = pendingPhotos.length + pendingIssues.length;
        }
        
        if (response['conflicts'] != null) {
          result.conflictCount = (response['conflicts'] as List).length;
          // 处理冲突
          for (final conflict in response['conflicts']) {
            await _handleConflict(conflict);
          }
        }
      }
      
      // 4. 拉取服务器最新数据
      final lastSyncTime = await _db.getLastSyncTime();
      if (lastSyncTime != null) {
        await _pullFromServer(lastSyncTime);
      }
      
      // 5. 更新同步时间
      await _db.setLastSyncTime(DateTime.now());
      
      result.success = true;
      result.message = '同步完成';
      
    } catch (e) {
      result.success = false;
      result.message = '同步失败: $e';
    } finally {
      _isSyncing = false;
    }
    
    return result;
  }
  
  /// 推送到服务器
  Future<Map<String, dynamic>> _pushToServer(Map<String, dynamic> data) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/sync/push'),
        headers: {
          'Content-Type': 'application/json',
          'X-Device-ID': deviceId,
          'X-App-Version': appVersion,
        },
        body: jsonEncode({
          ...data,
          'device_id': deviceId,
          'app_version': appVersion,
        }),
      ).timeout(const Duration(seconds: 30));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return {'synced': [], 'conflicts': [], 'failed': []};
    } catch (e) {
      return {'synced': [], 'conflicts': [], 'failed': [], 'error': e.toString()};
    }
  }
  
  /// 从服务器拉取
  Future<void> _pullFromServer(DateTime since) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/sync/pull?last_sync_time=${since.toIso8601String()}'),
        headers: {
          'X-Device-ID': deviceId,
          'X-App-Version': appVersion,
        },
      ).timeout(const Duration(seconds: 30));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // 保存拉取的照片
        for (final photoJson in data['photos'] ?? []) {
          final photo = PhotoRecord.fromJson(photoJson);
          await _db.insertPhoto(photo);
        }
        
        // 保存拉取的问题
        for (final issueJson in data['issues'] ?? []) {
          final issue = IssueRecord.fromJson(issueJson);
          await _db.insertIssue(issue);
        }
      }
    } catch (e) {
      // 忽略拉取错误，继续使用本地数据
    }
  }
  
  /// 处理冲突
  Future<void> _handleConflict(Map<String, dynamic> conflict) async {
    // 策略：服务器数据优先，更新本地
    // TODO: 可以让用户选择保留本地或服务器数据
    
    final entityType = conflict['entity_type'];
    final serverData = conflict['server_data'];
    
    if (entityType == 'photo') {
      final photo = PhotoRecord.fromJson(serverData);
      await _db.insertPhoto(photo);
    } else if (entityType == 'issue') {
      final issue = IssueRecord.fromJson(serverData);
      await _db.insertIssue(issue);
    }
  }
  
  /// 获取同步状态
  Future<SyncStatusInfo> getSyncStatus() async {
    final pendingPhotos = await _db.getPendingPhotos();
    final pendingIssues = await _db.getPendingIssues();
    final lastSyncTime = await _db.getLastSyncTime();
    
    return SyncStatusInfo(
      pendingCount: pendingPhotos.length + pendingIssues.length,
      lastSyncTime: lastSyncTime,
      isSyncing: _isSyncing,
    );
  }
}

// ==================== 辅助类 ====================

class SyncResult {
  bool success;
  String message;
  int syncedCount = 0;
  int conflictCount = 0;
  
  SyncResult({this.success = false, this.message = ''});
}

class SyncStatusInfo {
  int pendingCount;
  DateTime? lastSyncTime;
  bool isSyncing;
  
  SyncStatusInfo({
    required this.pendingCount,
    this.lastSyncTime,
    required this.isSyncing,
  });
}
