// NeuralSite 移动端问题服务
// 问题创建、照片关联

import 'package:dio/dio.dart';
import '../sync/offline_sync.dart';

/// 问题类型
enum IssueType {
  quality('quality', '质量问题'),
  safety('safety', '安全问题'),
  progress('progress', '进度问题'),
  other('other', '其他问题');
  
  final String value;
  final String label;
  const IssueType(this.value, this.label);
  
  static IssueType fromString(String value) {
    return IssueType.values.firstWhere(
      (e) => e.value == value,
      orElse: () => IssueType.other,
    );
  }
}

/// 问题严重程度
enum IssueSeverity {
  critical('critical', '严重'),
  major('major', '重要'),
  minor('minor', '一般');
  
  final String value;
  final String label;
  const IssueSeverity(this.value, this.label);
  
  static IssueSeverity fromString(String value) {
    return IssueSeverity.values.firstWhere(
      (e) => e.value == value,
      orElse: () => IssueSeverity.minor,
    );
  }
}

/// 问题状态
enum IssueStatus {
  open('open', '待处理'),
  inProgress('in_progress', '处理中'),
  resolved('resolved', '已解决'),
  closed('closed', '已关闭');
  
  final String value;
  final String label;
  const IssueStatus(this.value, this.label);
  
  static IssueStatus fromString(String value) {
    return IssueStatus.values.firstWhere(
      (e) => e.value == value,
      orElse: () => IssueStatus.open,
    );
  }
}

/// 问题服务
class IssueService {
  final Dio _dio;
  final LocalDatabase _db = LocalDatabase();
  
  List<IssueRecord> _issues = [];
  List<IssueRecord> get issues => _issues;
  
  bool _isLoading = false;
  bool get isLoading => _isLoading;
  
  String? _error;
  String? get error => _error;
  
  final List<VoidCallback> _listeners = [];
  
  IssueService({required Dio dio}) : _dio = dio;
  
  void addListener(VoidCallback listener) {
    _listeners.add(listener);
  }
  
  void removeListener(VoidCallback listener) {
    _listeners.remove(listener);
  }
  
  void notifyListeners() {
    for (final listener in _listeners) {
      listener();
    }
  }
  
  /// 加载问题列表
  Future<void> loadIssues({String? projectId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      if (projectId != null) {
        // 从本地数据库加载
        _issues = await _db.getPendingIssues();
        _issues = _issues.where((i) => i.projectId == projectId).toList();
      } else {
        _issues = await _db.getPendingIssues();
      }
    } catch (e) {
      _error = '加载问题失败: $e';
    }
    
    _isLoading = false;
    notifyListeners();
  }
  
  /// 创建问题
  Future<IssueRecord?> createIssue({
    required String projectId,
    required IssueType issueType,
    required String title,
    String? description,
    IssueSeverity severity = IssueSeverity.minor,
    double? station,
    String? stationDisplay,
    double? latitude,
    double? longitude,
    String? locationDescription,
    List<String> photoIds = const [],
    DateTime? deadline,
  }) async {
    try {
      final issue = IssueRecord(
        localId: DateTime.now().millisecondsSinceEpoch.toString(),
        projectId: projectId,
        issueType: issueType.value,
        title: title,
        description: description,
        severity: severity.value,
        station: station,
        stationDisplay: stationDisplay,
        latitude: latitude,
        longitude: longitude,
        locationDescription: locationDescription,
        photoIds: photoIds,
        status: IssueStatus.open.value,
        deadline: deadline,
        syncStatus: 'pending',
      );
      
      // 保存到本地数据库
      await _db.insertIssue(issue);
      
      // 添加到列表
      _issues.insert(0, issue);
      notifyListeners();
      
      return issue;
    } catch (e) {
      _error = '创建问题失败: $e';
      notifyListeners();
      return null;
    }
  }
  
  /// 更新问题
  Future<bool> updateIssue(IssueRecord issue) async {
    try {
      await _db.insertIssue(issue);
      
      final index = _issues.indexWhere((i) => i.localId == issue.localId);
      if (index >= 0) {
        _issues[index] = issue;
        notifyListeners();
      }
      
      return true;
    } catch (e) {
      _error = '更新问题失败: $e';
      notifyListeners();
      return false;
    }
  }
  
  /// 关联照片到问题
  Future<bool> addPhotosToIssue(String issueLocalId, List<String> photoLocalIds) async {
    try {
      final index = _issues.indexWhere((i) => i.localId == issueLocalId);
      if (index < 0) return false;
      
      final issue = _issues[index];
      final updatedPhotoIds = [...issue.photoIds, ...photoLocalIds];
      
      final updatedIssue = IssueRecord(
        localId: issue.localId,
        serverId: issue.serverId,
        projectId: issue.projectId,
        issueType: issue.issueType,
        title: issue.title,
        description: issue.description,
        severity: issue.severity,
        station: issue.station,
        stationDisplay: issue.stationDisplay,
        latitude: issue.latitude,
        longitude: issue.longitude,
        locationDescription: issue.locationDescription,
        photoIds: updatedPhotoIds,
        status: issue.status,
        deadline: issue.deadline,
        syncStatus: 'pending',
      );
      
      await _db.insertIssue(updatedIssue);
      _issues[index] = updatedIssue;
      notifyListeners();
      
      return true;
    } catch (e) {
      _error = '关联照片失败: $e';
      notifyListeners();
      return false;
    }
  }
  
  /// 移除问题中的照片
  Future<bool> removePhotoFromIssue(String issueLocalId, String photoLocalId) async {
    try {
      final index = _issues.indexWhere((i) => i.localId == issueLocalId);
      if (index < 0) return false;
      
      final issue = _issues[index];
      final updatedPhotoIds = issue.photoIds.where((id) => id != photoLocalId).toList();
      
      final updatedIssue = IssueRecord(
        localId: issue.localId,
        serverId: issue.serverId,
        projectId: issue.projectId,
        issueType: issue.issueType,
        title: issue.title,
        description: issue.description,
        severity: issue.severity,
        station: issue.station,
        stationDisplay: issue.stationDisplay,
        latitude: issue.latitude,
        longitude: issue.longitude,
        locationDescription: issue.locationDescription,
        photoIds: updatedPhotoIds,
        status: issue.status,
        deadline: issue.deadline,
        syncStatus: 'pending',
      );
      
      await _db.insertIssue(updatedIssue);
      _issues[index] = updatedIssue;
      notifyListeners();
      
      return true;
    } catch (e) {
      _error = '移除照片失败: $e';
      notifyListeners();
      return false;
    }
  }
  
  /// 更新问题状态
  Future<bool> updateIssueStatus(String issueLocalId, IssueStatus status) async {
    try {
      final index = _issues.indexWhere((i) => i.localId == issueLocalId);
      if (index < 0) return false;
      
      final issue = _issues[index];
      final updatedIssue = IssueRecord(
        localId: issue.localId,
        serverId: issue.serverId,
        projectId: issue.projectId,
        issueType: issue.issueType,
        title: issue.title,
        description: issue.description,
        severity: issue.severity,
        station: issue.station,
        stationDisplay: issue.stationDisplay,
        latitude: issue.latitude,
        longitude: issue.longitude,
        locationDescription: issue.locationDescription,
        photoIds: issue.photoIds,
        status: status.value,
        deadline: issue.deadline,
        syncStatus: 'pending',
      );
      
      await _db.insertIssue(updatedIssue);
      _issues[index] = updatedIssue;
      notifyListeners();
      
      return true;
    } catch (e) {
      _error = '更新状态失败: $e';
      notifyListeners();
      return false;
    }
  }
  
  /// 上传问题到服务器
  Future<String?> syncIssueToServer(IssueRecord issue) async {
    try {
      final response = await _dio.post(
        '/api/v1/issues',
        data: issue.toJson(),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        final serverId = response.data['id'];
        await _db.updateIssueSyncStatus(issue.localId!, 'synced', serverId: serverId);
        return serverId;
      }
      
      return null;
    } catch (e) {
      _error = '同步问题失败: $e';
      return null;
    }
  }
  
  /// 获取问题统计
  Map<IssueStatus, int> getIssueStats() {
    final stats = <IssueStatus, int>{};
    for (final status in IssueStatus.values) {
      stats[status] = _issues.where((i) => i.status == status.value).length;
    }
    return stats;
  }
  
  /// 按严重程度统计
  Map<IssueSeverity, int> getSeverityStats() {
    final stats = <IssueSeverity, int>{};
    for (final severity in IssueSeverity.values) {
      stats[severity] = _issues.where((i) => i.severity == severity.value).length;
    }
    return stats;
  }
  
  /// 按类型统计
  Map<IssueType, int> getTypeStats() {
    final stats = <IssueType, int>{};
    for (final type in IssueType.values) {
      stats[type] = _issues.where((i) => i.issueType == type.value).length;
    }
    return stats;
  }
  
  /// 清除错误
  void clearError() {
    _error = null;
    notifyListeners();
  }
}

/// 空回调类型
typedef VoidCallback = void Function();
