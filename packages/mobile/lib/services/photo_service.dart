// NeuralSite 移动端照片服务
// 封装拍照功能、GPS获取、桩号输入

import 'dart:io';
import 'package:dio/dio.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import '../sync/offline_sync.dart';

/// 照片服务
class PhotoService {
  final ImagePicker _imagePicker = ImagePicker();
  final Dio _dio;
  
  PhotoService({required Dio dio}) : _dio = dio;
  
  /// 拍照
  /// 返回拍摄的照片文件路径
  Future<String?> takePhoto({
    ImageSource source = ImageSource.camera,
    int? maxWidth,
    int? maxHeight,
    int imageQuality = 85,
  }) async {
    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: source,
        maxWidth: maxWidth?.toDouble(),
        maxHeight: maxHeight?.toDouble(),
        imageQuality: imageQuality,
      );
      
      if (photo == null) return null;
      
      // 保存到应用目录
      final savedPath = await _saveToAppDirectory(photo.path);
      return savedPath;
    } catch (e) {
      throw PhotoServiceException('拍照失败: $e');
    }
  }
  
  /// 从相册选择照片
  Future<String?> pickFromGallery({
    int? maxWidth,
    int? maxHeight,
    int imageQuality = 85,
  }) async {
    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        maxWidth: maxWidth?.toDouble(),
        maxHeight: maxHeight?.toDouble(),
        imageQuality: imageQuality,
      );
      
      if (photo == null) return null;
      
      final savedPath = await _saveToAppDirectory(photo.path);
      return savedPath;
    } catch (e) {
      throw PhotoServiceException('选择照片失败: $e');
    }
  }
  
  /// 保存照片到应用目录
  Future<String> _saveToAppDirectory(String originalPath) async {
    final appDir = await getApplicationDocumentsDirectory();
    final photosDir = Directory('${appDir.path}/photos');
    
    if (!await photosDir.exists()) {
      await photosDir.create(recursive: true);
    }
    
    final fileName = '${DateTime.now().millisecondsSinceEpoch}_${path.basename(originalPath)}';
    final newPath = '${photosDir.path}/$fileName';
    
    await File(originalPath).copy(newPath);
    return newPath;
  }
  
  /// 获取当前GPS位置
  Future<Position?> getCurrentLocation({
    bool highAccuracy = true,
    int timeoutSeconds = 10,
  }) async {
    try {
      // 检查权限
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw PhotoServiceException('定位服务未启用');
      }
      
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw PhotoServiceException('定位权限被拒绝');
        }
      }
      
      if (permission == LocationPermission.deniedForever) {
        throw PhotoServiceException('定位权限被永久拒绝');
      }
      
      // 获取位置
      final position = await Geolocator.getCurrentPosition(
        locationSettings: LocationSettings(
          accuracy: highAccuracy ? LocationAccuracy.high : LocationAccuracy.medium,
          timeLimit: Duration(seconds: timeoutSeconds),
        ),
      );
      
      return position;
    } catch (e) {
      if (e is PhotoServiceException) rethrow;
      throw PhotoServiceException('获取位置失败: $e');
    }
  }
  
  /// 格式化桩号显示
  /// station: 桩号数值（米）
  /// displayFormat: 显示格式 (K0+000, 0+000, etc.)
  String formatStation(double station, {String format = 'K'}) {
    final km = (station / 1000).floor();
    final meters = (station % 1000).toInt();
    
    if (format == 'K') {
      return 'K$km+$meters'.padLeft(8, '0');
    } else if (format == 'A') {
      return 'A$km+$meters'.padLeft(8, '0');
    }
    return '$km+$meters';
  }
  
  /// 解析桩号字符串为数值
  /// 支持格式: K1+200, 1+200, A1+200, 1200
  double? parseStation(String stationStr) {
    try {
      // 移除空格
      final cleaned = stationStr.replaceAll(' ', '');
      
      // 匹配 K1+200, A1+200 格式
      final match1 = RegExp(r'^([KA]?)(\d+)\+(\d+)$').firstMatch(cleaned);
      if (match1 != null) {
        final km = int.parse(match1.group(2)!);
        final meters = int.parse(match1.group(3)!);
        return km * 1000 + meters.toDouble();
      }
      
      // 纯数字格式
      return double.tryParse(cleaned);
    } catch (e) {
      return null;
    }
  }
  
  /// 创建照片记录
  PhotoRecord createPhotoRecord({
    required String projectId,
    required String filePath,
    double? latitude,
    double? longitude,
    double? station,
    String? stationDisplay,
    String? description,
    String? capturedBy,
  }) {
    return PhotoRecord(
      localId: DateTime.now().millisecondsSinceEpoch.toString(),
      projectId: projectId,
      filePath: filePath,
      capturedAt: DateTime.now(),
      latitude: latitude,
      longitude: longitude,
      station: station,
      stationDisplay: stationDisplay,
      description: description,
      capturedBy: capturedBy,
      syncStatus: 'pending',
    );
  }
  
  /// 上传照片到服务器
  Future<String?> uploadPhoto(String filePath, {
    required String projectId,
    void Function(int sent, int total)? onProgress,
  }) async {
    try {
      final file = File(filePath);
      if (!await file.exists()) {
        throw PhotoServiceException('文件不存在');
      }
      
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          filePath,
          filename: path.basename(filePath),
        ),
        'project_id': projectId,
      });
      
      final response = await _dio.post(
        '/api/v1/photos/upload',
        data: formData,
        onSendProgress: onProgress,
      );
      
      if (response.statusCode == 200) {
        return response.data['server_id'];
      }
      
      return null;
    } catch (e) {
      throw PhotoServiceException('上传失败: $e');
    }
  }
  
  /// 删除本地照片文件
  Future<void> deletePhoto(String filePath) async {
    try {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
      }
    } catch (e) {
      throw PhotoServiceException('删除照片失败: $e');
    }
  }
}

/// 照片服务异常
class PhotoServiceException implements Exception {
  final String message;
  PhotoServiceException(this.message);
  
  @override
  String toString() => message;
}
