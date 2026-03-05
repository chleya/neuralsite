import 'dart:convert';

/// Photo model - represents a captured photo with GPS and chainage info
class Photo {
  final String id;
  final String? localPath;
  final String? remoteUrl;
  final double? latitude;
  final double? longitude;
  final String? chainage;
  final String? projectId;
  final DateTime capturedAt;
  final String? description;
  final PhotoSyncStatus syncStatus;
  final DateTime createdAt;
  final DateTime? updatedAt;

  Photo({
    required this.id,
    this.localPath,
    this.remoteUrl,
    this.latitude,
    this.longitude,
    this.chainage,
    this.projectId,
    required this.capturedAt,
    this.description,
    this.syncStatus = PhotoSyncStatus.pending,
    DateTime? createdAt,
    this.updatedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory Photo.fromMap(Map<String, dynamic> map) {
    return Photo(
      id: map['id'] as String,
      localPath: map['local_path'] as String?,
      remoteUrl: map['remote_url'] as String?,
      latitude: map['latitude'] as double?,
      longitude: map['longitude'] as double?,
      chainage: map['chainage'] as String?,
      projectId: map['project_id'] as String?,
      capturedAt: DateTime.parse(map['captured_at'] as String),
      description: map['description'] as String?,
      syncStatus: PhotoSyncStatus.values.firstWhere(
        (e) => e.name == (map['sync_status'] as String? ?? 'pending'),
        orElse: () => PhotoSyncStatus.pending,
      ),
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: map['updated_at'] != null
          ? DateTime.parse(map['updated_at'] as String)
          : null,
    );
  }

  /// Convert to database map
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'local_path': localPath,
      'remote_url': remoteUrl,
      'latitude': latitude,
      'longitude': longitude,
      'chainage': chainage,
      'project_id': projectId,
      'captured_at': capturedAt.toIso8601String(),
      'description': description,
      'sync_status': syncStatus.name,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  /// Convert to JSON for API
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'local_path': localPath,
      'remote_url': remoteUrl,
      'latitude': latitude,
      'longitude': longitude,
      'chainage': chainage,
      'project_id': projectId,
      'captured_at': capturedAt.toIso8601String(),
      'description': description,
    };
  }

  /// Create from JSON response
  factory Photo.fromJson(Map<String, dynamic> json) {
    return Photo(
      id: json['id'] as String,
      localPath: json['local_path'] as String?,
      remoteUrl: json['remote_url'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      chainage: json['chainage'] as String?,
      projectId: json['project_id'] as String?,
      capturedAt: DateTime.parse(json['captured_at'] as String),
      description: json['description'] as String?,
      syncStatus: PhotoSyncStatus.synced,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  /// Copy with modifications
  Photo copyWith({
    String? id,
    String? localPath,
    String? remoteUrl,
    double? latitude,
    double? longitude,
    String? chainage,
    String? projectId,
    DateTime? capturedAt,
    String? description,
    PhotoSyncStatus? syncStatus,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Photo(
      id: id ?? this.id,
      localPath: localPath ?? this.localPath,
      remoteUrl: remoteUrl ?? this.remoteUrl,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      chainage: chainage ?? this.chainage,
      projectId: projectId ?? this.projectId,
      capturedAt: capturedAt ?? this.capturedAt,
      description: description ?? this.description,
      syncStatus: syncStatus ?? this.syncStatus,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'Photo(id: $id, chainage: $chainage, lat: $latitude, lng: $longitude, status: $syncStatus)';
  }
}

/// Photo sync status enum
enum PhotoSyncStatus {
  pending,    // Not yet uploaded
  uploading, // Currently uploading
  synced,    // Successfully synced with server
  conflict,  // Conflict detected
  failed,    // Upload failed
}

/// Extension for PhotoSyncStatus
extension PhotoSyncStatusExtension on PhotoSyncStatus {
  String get displayName {
    switch (this) {
      case PhotoSyncStatus.pending:
        return 'Pending';
      case PhotoSyncStatus.uploading:
        return 'Uploading';
      case PhotoSyncStatus.synced:
        return 'Synced';
      case PhotoSyncStatus.conflict:
        return 'Conflict';
      case PhotoSyncStatus.failed:
        return 'Failed';
    }
  }

  bool get needsSync => this == PhotoSyncStatus.pending || this == PhotoSyncStatus.failed;
}
