/// Progress model - represents construction progress report
class Progress {
  final String id;
  final String chainage;
  final ProgressStatus status;
  final String? note;
  final double? latitude;
  final double? longitude;
  final String? workType;
  final double? quantity;
  final String? unit;
  final DateTime timestamp;
  final bool synced;
  final DateTime createdAt;
  final DateTime? updatedAt;

  Progress({
    required this.id,
    required this.chainage,
    required this.status,
    this.note,
    this.latitude,
    this.longitude,
    this.workType,
    this.quantity,
    this.unit,
    required this.timestamp,
    this.synced = false,
    DateTime? createdAt,
    this.updatedAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Create from database map
  factory Progress.fromMap(Map<String, dynamic> map) {
    return Progress(
      id: map['id'] as String,
      chainage: map['chainage'] as String,
      status: ProgressStatus.values.firstWhere(
        (e) => e.name == (map['status'] as String? ?? 'planned'),
        orElse: () => ProgressStatus.planned,
      ),
      note: map['note'] as String?,
      latitude: map['latitude'] as double?,
      longitude: map['longitude'] as double?,
      workType: map['work_type'] as String?,
      quantity: (map['quantity'] as num?)?.toDouble(),
      unit: map['unit'] as String?,
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
      'status': status.name,
      'note': note,
      'latitude': latitude,
      'longitude': longitude,
      'work_type': workType,
      'quantity': quantity,
      'unit': unit,
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
      'status': status.name,
      'note': note,
      'latitude': latitude,
      'longitude': longitude,
      'work_type': workType,
      'quantity': quantity,
      'unit': unit,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  /// Create from JSON response
  factory Progress.fromJson(Map<String, dynamic> json) {
    return Progress(
      id: json['id'] as String,
      chainage: json['chainage'] as String,
      status: ProgressStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? 'planned'),
        orElse: () => ProgressStatus.planned,
      ),
      note: json['note'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      workType: json['work_type'] as String?,
      quantity: (json['quantity'] as num?)?.toDouble(),
      unit: json['unit'] as String?,
      timestamp: DateTime.parse(json['timestamp'] as String),
      synced: true,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  /// Copy with modifications
  Progress copyWith({
    String? id,
    String? chainage,
    ProgressStatus? status,
    String? note,
    double? latitude,
    double? longitude,
    String? workType,
    double? quantity,
    String? unit,
    DateTime? timestamp,
    bool? synced,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Progress(
      id: id ?? this.id,
      chainage: chainage ?? this.chainage,
      status: status ?? this.status,
      note: note ?? this.note,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      workType: workType ?? this.workType,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
      timestamp: timestamp ?? this.timestamp,
      synced: synced ?? this.synced,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'Progress(id: $id, chainage: $chainage, status: $status)';
  }
}

/// Progress status enum
enum ProgressStatus {
  planned,
  inProgress,
  completed,
  delayed,
  blocked,
}

/// Extension for ProgressStatus
extension ProgressStatusExtension on ProgressStatus {
  String get displayName {
    switch (this) {
      case ProgressStatus.planned:
        return 'Planned';
      case ProgressStatus.inProgress:
        return 'In Progress';
      case ProgressStatus.completed:
        return 'Completed';
      case ProgressStatus.delayed:
        return 'Delayed';
      case ProgressStatus.blocked:
        return 'Blocked';
    }
  }

  bool get isActive => this == ProgressStatus.planned || this == ProgressStatus.inProgress;
}

/// Common work types
class WorkTypes {
  static const String earthwork = 'Earthwork';
  static const String pavement = 'Pavement';
  static const String bridge = 'Bridge';
  static const String tunnel = 'Tunnel';
  static const String drainage = 'Drainage';
  static const String utility = 'Utility';
  static const String other = 'Other';

  static List<String> get all => [
    earthwork,
    pavement,
    bridge,
    tunnel,
    drainage,
    utility,
    other,
  ];
}

/// Common units
class ProgressUnits {
  static const String meter = 'm';
  static const String squareMeter = 'm²';
  static const String cubicMeter = 'm³';
  static const String ton = 't';
  static const String piece = 'pcs';
  static const String percent = '%';

  static List<String> get all => [
    meter,
    squareMeter,
    cubicMeter,
    ton,
    piece,
    percent,
  ];
}
