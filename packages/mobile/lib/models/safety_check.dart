/// SafetyCheck model - represents a safety inspection/audit
class SafetyCheck {
  final String id;
  final String chainage;
  final SafetyCheckType checkType;
  final SafetyStatus status;
  final String? description;
  final String? findings;
  final String? imageUrl;
  final String? localImagePath;
  final double? latitude;
  final double? longitude;
  final String? inspector;
  final List<SafetyIssue> issues;
  final DateTime timestamp;
  final bool synced;
  final DateTime createdAt;
  final DateTime? updatedAt;

  SafetyCheck({
    required this.id,
    required this.chainage,
    required this.checkType,
    this.status = SafetyStatus.pending,
    this.description,
    this.findings,
    this.imageUrl,
    this.localImagePath,
    this.latitude,
    this.longitude,
    this.inspector,
    this.issues = const [],
    required this.timestamp,
    this.synced = false,
    DateTime? createdAt,
    this.updatedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory SafetyCheck.fromMap(Map<String, dynamic> map) {
    List<SafetyIssue> parsedIssues = [];
    if (map['issues'] != null && map['issues'] is String) {
      // Handle JSON string if stored as text
      try {
        // ignore: avoid_dynamic_calls
        parsedIssues = _parseIssuesFromString(map['issues'] as String);
      } catch (_) {
        parsedIssues = [];
      }
    }

    return SafetyCheck(
      id: map['id'] as String,
      chainage: map['chainage'] as String,
      checkType: SafetyCheckType.values.firstWhere(
        (e) => e.name == (map['check_type'] as String? ?? 'routine'),
        orElse: () => SafetyCheckType.routine,
      ),
      status: SafetyStatus.values.firstWhere(
        (e) => e.name == (map['status'] as String? ?? 'pending'),
        orElse: () => SafetyStatus.pending,
      ),
      description: map['description'] as String?,
      findings: map['findings'] as String?,
      imageUrl: map['image_url'] as String?,
      localImagePath: map['local_image_path'] as String?,
      latitude: map['latitude'] as double?,
      longitude: map['longitude'] as double?,
      inspector: map['inspector'] as String?,
      issues: parsedIssues,
      timestamp: DateTime.parse(map['timestamp'] as String),
      synced: (map['synced'] as int?) == 1,
      createdAt: map['created_at'] != null
          ? DateTime.parse(map['created_at'] as String)
          : DateTime.now(),
      updatedAt: map['updated_at'] != null
          ? DateTime.parse(map['updated_at'] as String)
          : null,
    );
  }

  static List<SafetyIssue> _parseIssuesFromString(String jsonString) {
    // Simplified parsing - in production use proper JSON parsing
    return [];
  }

  /// Convert to database map
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'chainage': chainage,
      'check_type': checkType.name,
      'status': status.name,
      'description': description,
      'findings': findings,
      'image_url': imageUrl,
      'local_image_path': localImagePath,
      'latitude': latitude,
      'longitude': longitude,
      'inspector': inspector,
      'timestamp': timestamp.toIso8601String(),
      'synced': synced ? 1 : 0,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  /// Convert to JSON for API
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'chainage': chainage,
      'check_type': checkType.name,
      'status': status.name,
      'description': description,
      'findings': findings,
      'image_url': imageUrl,
      'latitude': latitude,
      'longitude': longitude,
      'inspector': inspector,
      'issues': issues.map((i) => i.toJson()).toList(),
      'timestamp': timestamp.toIso8601String(),
    };
  }

  /// Create from JSON response
  factory SafetyCheck.fromJson(Map<String, dynamic> json) {
    List<SafetyIssue> parsedIssues = [];
    if (json['issues'] != null) {
      parsedIssues = (json['issues'] as List)
          .map((i) => SafetyIssue.fromJson(i as Map<String, dynamic>))
          .toList();
    }

    return SafetyCheck(
      id: json['id'] as String,
      chainage: json['chainage'] as String,
      checkType: SafetyCheckType.values.firstWhere(
        (e) => e.name == (json['check_type'] as String? ?? 'routine'),
        orElse: () => SafetyCheckType.routine,
      ),
      status: SafetyStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? 'pending'),
        orElse: () => SafetyStatus.pending,
      ),
      description: json['description'] as String?,
      findings: json['findings'] as String?,
      imageUrl: json['image_url'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      inspector: json['inspector'] as String?,
      issues: parsedIssues,
      timestamp: DateTime.parse(json['timestamp'] as String),
      synced: true,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  /// Copy with modifications
  SafetyCheck copyWith({
    String? id,
    String? chainage,
    SafetyCheckType? checkType,
    SafetyStatus? status,
    String? description,
    String? findings,
    String? imageUrl,
    String? localImagePath,
    double? latitude,
    double? longitude,
    String? inspector,
    List<SafetyIssue>? issues,
    DateTime? timestamp,
    bool? synced,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return SafetyCheck(
      id: id ?? this.id,
      chainage: chainage ?? this.chainage,
      checkType: checkType ?? this.checkType,
      status: status ?? this.status,
      description: description ?? this.description,
      findings: findings ?? this.findings,
      imageUrl: imageUrl ?? this.imageUrl,
      localImagePath: localImagePath ?? this.localImagePath,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      inspector: inspector ?? this.inspector,
      issues: issues ?? this.issues,
      timestamp: timestamp ?? this.timestamp,
      synced: synced ?? this.synced,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'SafetyCheck(id: $id, chainage: $chainage, type: $checkType, status: $status)';
  }
}

/// Safety check types
enum SafetyCheckType {
  routine,
  focused,
  incident,
  compliance,
  emergency,
}

/// Extension for SafetyCheckType
extension SafetyCheckTypeExtension on SafetyCheckType {
  String get displayName {
    switch (this) {
      case SafetyCheckType.routine:
        return 'Routine';
      case SafetyCheckType.focused:
        return 'Focused';
      case SafetyCheckType.incident:
        return 'Incident';
      case SafetyCheckType.compliance:
        return 'Compliance';
      case SafetyCheckType.emergency:
        return 'Emergency';
    }
  }
}

/// Safety status
enum SafetyStatus {
  pending,
  pass,
  fail,
  needsAttention,
  resolved,
}

/// Extension for SafetyStatus
extension SafetyStatusExtension on SafetyStatus {
  String get displayName {
    switch (this) {
      case SafetyStatus.pending:
        return 'Pending';
      case SafetyStatus.pass:
        return 'Pass';
      case SafetyStatus.fail:
        return 'Fail';
      case SafetyStatus.needsAttention:
        return 'Needs Attention';
      case SafetyStatus.resolved:
        return 'Resolved';
    }
  }
}

/// Safety issue found during check
class SafetyIssue {
  final String id;
  final String description;
  final SafetyIssueSeverity severity;
  final bool resolved;
  final String? resolution;
  final DateTime? resolvedAt;

  SafetyIssue({
    required this.id,
    required this.description,
    this.severity = SafetyIssueSeverity.low,
    this.resolved = false,
    this.resolution,
    this.resolvedAt,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'severity': severity.name,
      'resolved': resolved,
      'resolution': resolution,
      'resolved_at': resolvedAt?.toIso8601String(),
    };
  }

  factory SafetyIssue.fromJson(Map<String, dynamic> json) {
    return SafetyIssue(
      id: json['id'] as String,
      description: json['description'] as String,
      severity: SafetyIssueSeverity.values.firstWhere(
        (e) => e.name == (json['severity'] as String? ?? 'low'),
        orElse: () => SafetyIssueSeverity.low,
      ),
      resolved: json['resolved'] as bool? ?? false,
      resolution: json['resolution'] as String?,
      resolvedAt: json['resolved_at'] != null
          ? DateTime.parse(json['resolved_at'] as String)
          : null,
    );
  }
}

/// Safety issue severity
enum SafetyIssueSeverity {
  low,
  medium,
  high,
  critical,
}

/// Extension for SafetyIssueSeverity
extension SafetyIssueSeverityExtension on SafetyIssueSeverity {
  String get displayName {
    switch (this) {
      case SafetyIssueSeverity.low:
        return 'Low';
      case SafetyIssueSeverity.medium:
        return 'Medium';
      case SafetyIssueSeverity.high:
        return 'High';
      case SafetyIssueSeverity.critical:
        return 'Critical';
    }
  }
}
