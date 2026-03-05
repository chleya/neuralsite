/// AIDetection model - represents AI-powered image detection results
class AIDetection {
  final String id;
  final String? photoId;
  final String? localImagePath;
  final String? remoteImageUrl;
  final DetectionStatus status;
  final List<DetectionResult> results;
  final String? summary;
  final double confidence;
  final DateTime analyzedAt;
  final DateTime createdAt;

  AIDetection({
    required this.id,
    this.photoId,
    this.localImagePath,
    this.remoteImageUrl,
    this.status = DetectionStatus.pending,
    this.results = const [],
    this.summary,
    this.confidence = 0.0,
    required this.analyzedAt,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory AIDetection.fromMap(Map<String, dynamic> map) {
    List<DetectionResult> parsedResults = [];
    if (map['results'] != null && map['results'] is String) {
      try {
        // Results stored as JSON string - simplified
        parsedResults = [];
      } catch (_) {
        parsedResults = [];
      }
    }

    return AIDetection(
      id: map['id'] as String,
      photoId: map['photo_id'] as String?,
      localImagePath: map['local_image_path'] as String?,
      remoteImageUrl: map['remote_image_url'] as String?,
      status: DetectionStatus.values.firstWhere(
        (e) => e.name == (map['status'] as String? ?? 'pending'),
        orElse: () => DetectionStatus.pending,
      ),
      results: parsedResults,
      summary: map['summary'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble() ?? 0.0,
      analyzedAt: map['analyzed_at'] != null
          ? DateTime.parse(map['analyzed_at'] as String)
          : DateTime.now(),
      createdAt: map['created_at'] != null
          ? DateTime.parse(map['created_at'] as String)
          : DateTime.now(),
    );
  }

  /// Convert to database map
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'photo_id': photoId,
      'local_image_path': localImagePath,
      'remote_image_url': remoteImageUrl,
      'status': status.name,
      'summary': summary,
      'confidence': confidence,
      'analyzed_at': analyzedAt.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
    };
  }

  /// Create from API response
  factory AIDetection.fromApiResponse(Map<String, dynamic> json) {
    List<DetectionResult> parsedResults = [];
    if (json['results'] != null) {
      parsedResults = (json['results'] as List)
          .map((r) => DetectionResult.fromJson(r as Map<String, dynamic>))
          .toList();
    }

    return AIDetection(
      id: json['id'] as String? ?? '',
      photoId: json['photo_id'] as String?,
      remoteImageUrl: json['image_url'] as String?,
      status: DetectionStatus.completed,
      results: parsedResults,
      summary: json['summary'] as String?,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      analyzedAt: DateTime.now(),
      createdAt: DateTime.now(),
    );
  }

  /// Copy with modifications
  AIDetection copyWith({
    String? id,
    String? photoId,
    String? localImagePath,
    String? remoteImageUrl,
    DetectionStatus? status,
    List<DetectionResult>? results,
    String? summary,
    double? confidence,
    DateTime? analyzedAt,
    DateTime? createdAt,
  }) {
    return AIDetection(
      id: id ?? this.id,
      photoId: photoId ?? this.photoId,
      localImagePath: localImagePath ?? this.localImagePath,
      remoteImageUrl: remoteImageUrl ?? this.remoteImageUrl,
      status: status ?? this.status,
      results: results ?? this.results,
      summary: summary ?? this.summary,
      confidence: confidence ?? this.confidence,
      analyzedAt: analyzedAt ?? this.analyzedAt,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  /// Check if any issues detected
  bool get hasIssues => results.any((r) => r.severity == DetectionSeverity.high || r.severity == DetectionSeverity.critical);

  @override
  String toString() {
    return 'AIDetection(id: $id, status: $status, issues: ${results.length})';
  }
}

/// Detection status
enum DetectionStatus {
  pending,
  processing,
  completed,
  failed,
}

/// Extension for DetectionStatus
extension DetectionStatusExtension on DetectionStatus {
  String get displayName {
    switch (this) {
      case DetectionStatus.pending:
        return 'Pending';
      case DetectionStatus.processing:
        return 'Processing';
      case DetectionStatus.completed:
        return 'Completed';
      case DetectionStatus.failed:
        return 'Failed';
    }
  }
}

/// Detection result for a single item
class DetectionResult {
  final String id;
  final String label;
  final String category;
  final double confidence;
  final DetectionSeverity severity;
  final String? description;
  final BoundingBox? boundingBox;
  final String? recommendation;

  DetectionResult({
    required this.id,
    required this.label,
    required this.category,
    required this.confidence,
    this.severity = DetectionSeverity.low,
    this.description,
    this.boundingBox,
    this.recommendation,
  });

  factory DetectionResult.fromJson(Map<String, dynamic> json) {
    BoundingBox? box;
    if (json['bounding_box'] != null) {
      box = BoundingBox.fromJson(json['bounding_box'] as Map<String, dynamic>);
    }

    return DetectionResult(
      id: json['id'] as String? ?? '',
      label: json['label'] as String,
      category: json['category'] as String? ?? 'general',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      severity: DetectionSeverity.values.firstWhere(
        (e) => e.name == (json['severity'] as String? ?? 'low'),
        orElse: () => DetectionSeverity.low,
      ),
      description: json['description'] as String?,
      boundingBox: box,
      recommendation: json['recommendation'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'label': label,
      'category': category,
      'confidence': confidence,
      'severity': severity.name,
      'description': description,
      'bounding_box': boundingBox?.toJson(),
      'recommendation': recommendation,
    };
  }
}

/// Bounding box for detection
class BoundingBox {
  final double x;
  final double y;
  final double width;
  final double height;

  BoundingBox({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
  });

  factory BoundingBox.fromJson(Map<String, dynamic> json) {
    return BoundingBox(
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
      width: (json['width'] as num).toDouble(),
      height: (json['height'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'x': x,
      'y': y,
      'width': width,
      'height': height,
    };
  }
}

/// Detection severity
enum DetectionSeverity {
  info,
  low,
  medium,
  high,
  critical,
}

/// Extension for DetectionSeverity
extension DetectionSeverityExtension on DetectionSeverity {
  String get displayName {
    switch (this) {
      case DetectionSeverity.info:
        return 'Info';
      case DetectionSeverity.low:
        return 'Low';
      case DetectionSeverity.medium:
        return 'Medium';
      case DetectionSeverity.high:
        return 'High';
      case DetectionSeverity.critical:
        return 'Critical';
    }
  }
}

/// Detection categories
class DetectionCategories {
  static const String quality = 'quality';
  static const String safety = 'safety';
  static const String compliance = 'compliance';
  static const String progress = 'progress';
  static const String general = 'general';

  static List<String> get all => [quality, safety, compliance, progress, general];
}

/// Workflow approval status
class WorkflowApproval {
  final String id;
  final String detectionId;
  final String approver;
  final ApprovalStatus status;
  final String? comment;
  final DateTime timestamp;

  WorkflowApproval({
    required this.id,
    required this.detectionId,
    required this.approver,
    required this.status,
    this.comment,
    required this.timestamp,
  });

  factory WorkflowApproval.fromJson(Map<String, dynamic> json) {
    return WorkflowApproval(
      id: json['id'] as String,
      detectionId: json['detection_id'] as String,
      approver: json['approver'] as String,
      status: ApprovalStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? 'pending'),
        orElse: () => ApprovalStatus.pending,
      ),
      comment: json['comment'] as String?,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}

/// Approval status
enum ApprovalStatus {
  pending,
  approved,
  rejected,
  needsRevision,
}

/// Extension for ApprovalStatus
extension ApprovalStatusExtension on ApprovalStatus {
  String get displayName {
    switch (this) {
      case ApprovalStatus.pending:
        return 'Pending';
      case ApprovalStatus.approved:
        return 'Approved';
      case ApprovalStatus.rejected:
        return 'Rejected';
      case ApprovalStatus.needsRevision:
        return 'Needs Revision';
    }
  }
}
