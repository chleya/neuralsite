/// Issue model - represents a construction issue/problem report
class Issue {
  final String id;
  final String chainage;
  final String description;
  final IssueSeverity severity;
  final String? imageUrl;
  final String? localImagePath;
  final double? latitude;
  final double? longitude;
  final IssueStatus status;
  final DateTime timestamp;
  final bool synced;
  final DateTime createdAt;
  final DateTime? updatedAt;

  Issue({
    required this.id,
    required this.chainage,
    required this.description,
    this.severity = IssueSeverity.medium,
    this.imageUrl,
    this.localImagePath,
    this.latitude,
    this.longitude,
    this.status = IssueStatus.open,
    required this.timestamp,
    this.synced = false,
    DateTime? createdAt,
    this.updatedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory Issue.fromMap(Map<String, dynamic> map) {
    return Issue(
      id: map['id'] as String,
      chainage: map['chainage'] as String,
      description: map['description'] as String,
      severity: IssueSeverity.values.firstWhere(
        (e) => e.name == (map['severity'] as String? ?? 'medium'),
        orElse: () => IssueSeverity.medium,
      ),
      imageUrl: map['image_url'] as String?,
      localImagePath: map['local_image_path'] as String?,
      latitude: map['latitude'] as double?,
      longitude: map['longitude'] as double?,
      status: IssueStatus.values.firstWhere(
        (e) => e.name == (map['status'] as String? ?? 'open'),
        orElse: () => IssueStatus.open,
      ),
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

  /// Convert to database map
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'chainage': chainage,
      'description': description,
      'severity': severity.name,
      'image_url': imageUrl,
      'local_image_path': localImagePath,
      'latitude': latitude,
      'longitude': longitude,
      'status': status.name,
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
      'description': description,
      'severity': severity.name,
      'image_url': imageUrl,
      'latitude': latitude,
      'longitude': longitude,
      'status': status.name,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  /// Create from JSON response
  factory Issue.fromJson(Map<String, dynamic> json) {
    return Issue(
      id: json['id'] as String,
      chainage: json['chainage'] as String,
      description: json['description'] as String,
      severity: IssueSeverity.values.firstWhere(
        (e) => e.name == (json['severity'] as String? ?? 'medium'),
        orElse: () => IssueSeverity.medium,
      ),
      imageUrl: json['image_url'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      status: IssueStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? 'open'),
        orElse: () => IssueStatus.open,
      ),
      timestamp: DateTime.parse(json['timestamp'] as String),
      synced: true,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  /// Copy with modifications
  Issue copyWith({
    String? id,
    String? chainage,
    String? description,
    IssueSeverity? severity,
    String? imageUrl,
    String? localImagePath,
    double? latitude,
    double? longitude,
    IssueStatus? status,
    DateTime? timestamp,
    bool? synced,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Issue(
      id: id ?? this.id,
      chainage: chainage ?? this.chainage,
      description: description ?? this.description,
      severity: severity ?? this.severity,
      imageUrl: imageUrl ?? this.imageUrl,
      localImagePath: localImagePath ?? this.localImagePath,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      status: status ?? this.status,
      timestamp: timestamp ?? this.timestamp,
      synced: synced ?? this.synced,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'Issue(id: $id, chainage: $chainage, severity: $severity, status: $status)';
  }
}

/// Issue severity levels
enum IssueSeverity {
  low,
  medium,
  high,
  critical,
}

/// Extension for IssueSeverity
extension IssueSeverityExtension on IssueSeverity {
  String get displayName {
    switch (this) {
      case IssueSeverity.low:
        return 'Low';
      case IssueSeverity.medium:
        return 'Medium';
      case IssueSeverity.high:
        return 'High';
      case IssueSeverity.critical:
        return 'Critical';
    }
  }

  int get priority {
    switch (this) {
      case IssueSeverity.low:
        return 1;
      case IssueSeverity.medium:
        return 2;
      case IssueSeverity.high:
        return 3;
      case IssueSeverity.critical:
        return 4;
    }
  }
}

/// Issue status
enum IssueStatus {
  open,
  inProgress,
  resolved,
  closed,
  rejected,
}

/// Extension for IssueStatus
extension IssueStatusExtension on IssueStatus {
  String get displayName {
    switch (this) {
      case IssueStatus.open:
        return 'Open';
      case IssueStatus.inProgress:
        return 'In Progress';
      case IssueStatus.resolved:
        return 'Resolved';
      case IssueStatus.closed:
        return 'Closed';
      case IssueStatus.rejected:
        return 'Rejected';
    }
  }
}
