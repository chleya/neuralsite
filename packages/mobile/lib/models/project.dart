/// Project model - represents a construction project
class Project {
  final String id;
  final String name;
  final String? description;
  final String? routeId;
  final double? startStation;
  final double? endStation;
  final ProjectStatus status;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final bool isActive;

  Project({
    required this.id,
    required this.name,
    this.description,
    this.routeId,
    this.startStation,
    this.endStation,
    this.status = ProjectStatus.active,
    DateTime? createdAt,
    this.updatedAt,
    this.isActive = true,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory Project.fromMap(Map<String, dynamic> map) {
    return Project(
      id: map['id'] as String,
      name: map['name'] as String,
      description: map['description'] as String?,
      routeId: map['route_id'] as String?,
      startStation: (map['start_station'] as num?)?.toDouble(),
      endStation: (map['end_station'] as num?)?.toDouble(),
      status: ProjectStatus.values.firstWhere(
        (e) => e.name == (map['status'] as String? ?? 'active'),
        orElse: () => ProjectStatus.active,
      ),
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: map['updated_at'] != null
          ? DateTime.parse(map['updated_at'] as String)
          : null,
      isActive: (map['is_active'] as int?) == 1,
    );
  }

  /// Convert to database map
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'route_id': routeId,
      'start_station': startStation,
      'end_station': endStation,
      'status': status.name,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'is_active': isActive ? 1 : 0,
    };
  }

  /// Convert to JSON for API
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'route_id': routeId,
      'start_station': startStation,
      'end_station': endStation,
      'status': status.name,
    };
  }

  /// Create from JSON response
  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      routeId: json['route_id'] as String?,
      startStation: (json['start_station'] as num?)?.toDouble(),
      endStation: (json['end_station'] as num?)?.toDouble(),
      status: ProjectStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? 'active'),
        orElse: () => ProjectStatus.active,
      ),
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  /// Copy with modifications
  Project copyWith({
    String? id,
    String? name,
    String? description,
    String? routeId,
    double? startStation,
    double? endStation,
    ProjectStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
    bool? isActive,
  }) {
    return Project(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      routeId: routeId ?? this.routeId,
      startStation: startStation ?? this.startStation,
      endStation: endStation ?? this.endStation,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      isActive: isActive ?? this.isActive,
    );
  }

  /// Get station range string
  String get stationRange {
    if (startStation == null || endStation == null) return 'N/A';
    return 'K${(startStation! / 1000).toStringAsFixed(1)} - K${(endStation! / 1000).toStringAsFixed(1)}';
  }

  @override
  String toString() {
    return 'Project(id: $id, name: $name, status: $status)';
  }
}

/// Project status enum
enum ProjectStatus {
  draft,
  active,
  paused,
  completed,
  archived,
}

/// Extension for ProjectStatus
extension ProjectStatusExtension on ProjectStatus {
  String get displayName {
    switch (this) {
      case ProjectStatus.draft:
        return 'Draft';
      case ProjectStatus.active:
        return 'Active';
      case ProjectStatus.paused:
        return 'Paused';
      case ProjectStatus.completed:
        return 'Completed';
      case ProjectStatus.archived:
        return 'Archived';
    }
  }

  bool get canEdit => this == ProjectStatus.draft || this == ProjectStatus.active;
}
