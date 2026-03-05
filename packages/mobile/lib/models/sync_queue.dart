import 'dart:convert';

/// SyncQueue model - tracks pending sync operations
class SyncQueueItem {
  final int? localId;
  final String id;
  final SyncEntityType entityType;
  final String entityId;
  final SyncOperation operation;
  final Map<String, dynamic> payload;
  final int retryCount;
  final SyncQueueStatus status;
  final String? errorMessage;
  final DateTime createdAt;
  final DateTime? lastAttemptAt;
  final DateTime? completedAt;

  SyncQueueItem({
    this.localId,
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.operation,
    required this.payload,
    this.retryCount = 0,
    this.status = SyncQueueStatus.pending,
    this.errorMessage,
    DateTime? createdAt,
    this.lastAttemptAt,
    this.completedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory SyncQueueItem.fromMap(Map<String, dynamic> map) {
    // Parse payload - handle both JSON string and Map
    Map<String, dynamic> parsedPayload = {};
    final payloadData = map['payload'];
    
    if (payloadData is Map<String, dynamic>) {
      parsedPayload = payloadData;
    } else if (payloadData is String && payloadData.isNotEmpty) {
      try {
        parsedPayload = Map<String, dynamic>.from(jsonDecode(payloadData));
      } catch (e) {
        // If JSON decode fails, try to parse as simple map string
        parsedPayload = {};
      }
    }
    
    return SyncQueueItem(
      localId: map['id'] as int?,
      id: map['id'] as String,
      entityType: SyncEntityType.values.firstWhere(
        (e) => e.name == (map['entity_type'] as String?),
        orElse: () => SyncEntityType.photo,
      ),
      entityId: map['entity_id'] as String,
      operation: SyncOperation.values.firstWhere(
        (e) => e.name == (map['operation'] as String?),
        orElse: () => SyncOperation.create,
      ),
      payload: parsedPayload,
      retryCount: map['retry_count'] as int? ?? 0,
      status: SyncQueueStatus.values.firstWhere(
        (e) => e.name == (map['status'] as String? ?? 'pending'),
        orElse: () => SyncQueueStatus.pending,
      ),
      errorMessage: map['error_message'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
      lastAttemptAt: map['last_attempt_at'] != null
          ? DateTime.parse(map['last_attempt_at'] as String)
          : null,
      completedAt: map['completed_at'] != null
          ? DateTime.parse(map['completed_at'] as String)
          : null,
    );
  }

  /// Convert to database map
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'entity_type': entityType.name,
      'entity_id': entityId,
      'operation': operation.name,
      'payload': jsonEncode(payload), // Proper JSON serialization
      'retry_count': retryCount,
      'status': status.name,
      'error_message': errorMessage,
      'created_at': createdAt.toIso8601String(),
      'last_attempt_at': lastAttemptAt?.toIso8601String(),
      'completed_at': completedAt?.toIso8601String(),
    };
  }

  /// Copy with modifications
  SyncQueueItem copyWith({
    int? localId,
    String? id,
    SyncEntityType? entityType,
    String? entityId,
    SyncOperation? operation,
    Map<String, dynamic>? payload,
    int? retryCount,
    SyncQueueStatus? status,
    String? errorMessage,
    DateTime? createdAt,
    DateTime? lastAttemptAt,
    DateTime? completedAt,
  }) {
    return SyncQueueItem(
      localId: localId ?? this.localId,
      id: id ?? this.id,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      operation: operation ?? this.operation,
      payload: payload ?? this.payload,
      retryCount: retryCount ?? this.retryCount,
      status: status ?? this.status,
      errorMessage: errorMessage ?? this.errorMessage,
      createdAt: createdAt ?? this.createdAt,
      lastAttemptAt: lastAttemptAt ?? this.lastAttemptAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }

  /// Check if max retries exceeded
  bool get canRetry => retryCount < 3 && status != SyncQueueStatus.completed;

  @override
  String toString() {
    return 'SyncQueueItem(id: $id, entity: $entityType/$entityId, op: $operation, status: $status)';
  }
}

/// Entity types that can be synced
enum SyncEntityType {
  photo,
  issue,
  progress,
  project,
  safetyCheck,
}

/// Sync operations
enum SyncOperation {
  create,
  update,
  delete,
}

/// Sync queue status
enum SyncQueueStatus {
  pending,
  inProgress,
  completed,
  failed,
  cancelled,
}

/// Extension for SyncQueueStatus
extension SyncQueueStatusExtension on SyncQueueStatus {
  bool get isTerminal =>
      this == SyncQueueStatus.completed ||
      this == SyncQueueStatus.failed ||
      this == SyncQueueStatus.cancelled;

  String get displayName {
    switch (this) {
      case SyncQueueStatus.pending:
        return 'Pending';
      case SyncQueueStatus.inProgress:
        return 'In Progress';
      case SyncQueueStatus.completed:
        return 'Completed';
      case SyncQueueStatus.failed:
        return 'Failed';
      case SyncQueueStatus.cancelled:
        return 'Cancelled';
    }
  }
}

/// Extension for SyncOperation
extension SyncOperationExtension on SyncOperation {
  String get displayName {
    switch (this) {
      case SyncOperation.create:
        return 'Create';
      case SyncOperation.update:
        return 'Update';
      case SyncOperation.delete:
        return 'Delete';
    }
  }

  String get httpMethod {
    switch (this) {
      case SyncOperation.create:
        return 'POST';
      case SyncOperation.update:
        return 'PUT';
      case SyncOperation.delete:
        return 'DELETE';
    }
  }
}

/// Sync conflict resolution
enum ConflictResolution {
  keepLocal,   // Keep local version
  keepRemote,  // Keep remote version
  merge,       // Attempt to merge
  manual,      // Require manual resolution
}

/// Sync conflict information
class SyncConflict {
  final String entityType;
  final String entityId;
  final Map<String, dynamic> localData;
  final Map<String, dynamic> remoteData;
  final ConflictResolution resolution;
  final DateTime detectedAt;

  SyncConflict({
    required this.entityType,
    required this.entityId,
    required this.localData,
    required this.remoteData,
    this.resolution = ConflictResolution.manual,
    DateTime? detectedAt,
  }) : detectedAt = detectedAt ?? DateTime.now();
}
