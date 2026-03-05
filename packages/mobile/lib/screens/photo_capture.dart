// NeuralSite 移动端照片采集组件
// 功能：相机拍照、相册选择、GPS位置获取、桩号输入、照片描述

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

/// 照片采集结果
class PhotoCaptureResult {
  final String? photoPath;
  final Position? position;
  final double? station;
  final String? stationDisplay;
  final String? description;
  
  PhotoCaptureResult({
    this.photoPath,
    this.position,
    this.station,
    this.stationDisplay,
    this.description,
  });
  
  bool get hasPhoto => photoPath != null;
  bool get hasPosition => position != null;
  bool get hasStation => station != null;
}

/// 照片采集组件
class PhotoCapture extends StatefulWidget {
  /// 初始照片路径（用于编辑已有照片）
  final String? initialPhotoPath;
  
  /// 初始GPS位置
  final Position? initialPosition;
  
  /// 初始桩号
  final double? initialStation;
  
  /// 初始描述
  final String? initialDescription;
  
  /// 照片采集完成回调
  final void Function(PhotoCaptureResult result)? onCapture;
  
  /// 是否显示桩号输入
  final bool showStationInput;
  
  /// 是否显示描述输入
  final bool showDescription;
  
  /// 是否在加载时自动获取GPS
  final bool autoFetchLocation;
  
  const PhotoCapture({
    super.key,
    this.initialPhotoPath,
    this.initialPosition,
    this.initialStation,
    this.initialDescription,
    this.onCapture,
    this.showStationInput = true,
    this.showDescription = true,
    this.autoFetchLocation = true,
  });
  
  @override
  State<PhotoCapture> createState() => _PhotoCaptureState();
}

class _PhotoCaptureState extends State<PhotoCapture> {
  final ImagePicker _imagePicker = ImagePicker();
  final TextEditingController _stationController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  
  String? _capturedPhotoPath;
  Position? _currentPosition;
  double? _stationValue;
  bool _isLoadingLocation = false;
  bool _isCapturing = false;
  String? _errorMessage;
  
  @override
  void initState() {
    super.initState();
    _initializeValues();
  }
  
  void _initializeValues() {
    _capturedPhotoPath = widget.initialPhotoPath;
    _currentPosition = widget.initialPosition;
    _stationValue = widget.initialStation;
    
    if (widget.initialStation != null) {
      _stationController.text = _formatStation(widget.initialStation!);
    }
    if (widget.initialDescription != null) {
      _descriptionController.text = widget.initialDescription!;
    }
    
    if (widget.autoFetchLocation && widget.initialPosition == null) {
      _getCurrentLocation();
    }
  }
  
  @override
  void dispose() {
    _stationController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }
  
  /// 格式化桩号显示
  String _formatStation(double station) {
    final km = (station / 1000).floor();
    final meters = (station % 1000).toInt();
    return 'K$km+$meters'.padLeft(8, '0');
  }
  
  /// 解析桩号
  double? _parseStation(String stationStr) {
    try {
      final cleaned = stationStr.replaceAll(' ', '');
      final match = RegExp(r'^([KA]?)(\d+)\+(\d+)$').firstMatch(cleaned);
      if (match != null) {
        final km = int.parse(match.group(2)!);
        final meters = int.parse(match.group(3)!);
        return km * 1000 + meters.toDouble();
      }
      return double.tryParse(cleaned);
    } catch (e) {
      return null;
    }
  }
  
  /// 获取当前位置
  Future<void> _getCurrentLocation() async {
    setState(() {
      _isLoadingLocation = true;
      _errorMessage = null;
    });
    
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw Exception('定位服务未启用');
      }
      
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception('定位权限被拒绝');
        }
      }
      
      if (permission == LocationPermission.deniedForever) {
        throw Exception('定位权限被永久拒绝');
      }
      
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 10),
        ),
      );
      
      setState(() {
        _currentPosition = position;
        _isLoadingLocation = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingLocation = false;
        _errorMessage = e.toString();
      });
    }
  }
  
  /// 拍照
  Future<void> _takePhoto() async {
    setState(() {
      _isCapturing = true;
      _errorMessage = null;
    });
    
    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );
      
      if (photo != null) {
        final savedPath = await _saveToAppDirectory(photo.path);
        setState(() {
          _capturedPhotoPath = savedPath;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = '拍照失败: $e';
      });
    } finally {
      setState(() {
        _isCapturing = false;
      });
    }
  }
  
  /// 从相册选择
  Future<void> _pickFromGallery() async {
    setState(() {
      _isCapturing = true;
      _errorMessage = null;
    });
    
    try {
      final XFile? photo = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );
      
      if (photo != null) {
        final savedPath = await _saveToAppDirectory(photo.path);
        setState(() {
          _capturedPhotoPath = savedPath;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = '选择照片失败: $e';
      });
    } finally {
      setState(() {
        _isCapturing = false;
      });
    }
  }
  
  /// 保存到应用目录
  Future<String> _saveToAppDirectory(String originalPath) async {
    final appDir = await getApplicationDocumentsDirectory();
    final photosDir = Directory('${appDir.path}/photos');
    
    if (!await photosDir.exists()) {
      await photosDir.create(recursive: true);
    }
    
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final ext = path.extension(originalPath);
    final fileName = '${timestamp}$ext';
    final newPath = '${photosDir.path}/$fileName';
    
    await File(originalPath).copy(newPath);
    return newPath;
  }
  
  /// 确认桩号
  void _confirmStation() {
    final station = _parseStation(_stationController.text);
    if (station != null) {
      setState(() {
        _stationValue = station;
        _stationController.text = _formatStation(station);
      });
    } else {
      setState(() {
        _errorMessage = '无效的桩号格式';
      });
    }
  }
  
  /// 获取结果
  PhotoCaptureResult getResult() {
    return PhotoCaptureResult(
      photoPath: _capturedPhotoPath,
      position: _currentPosition,
      station: _stationValue,
      stationDisplay: _stationController.text.isNotEmpty 
          ? _stationController.text 
          : null,
      description: _descriptionController.text.isNotEmpty 
          ? _descriptionController.text 
          : null,
    );
  }
  
  /// 完成采集
  void complete() {
    widget.onCapture?.call(getResult());
  }
  
  /// 重拍
  void _retake() {
    if (_capturedPhotoPath != null) {
      try {
        File(_capturedPhotoPath!).delete();
      } catch (_) {}
    }
    setState(() {
      _capturedPhotoPath = null;
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 照片预览/拍摄区域
          _buildPhotoArea(),
          
          const SizedBox(height: 24),
          
          // GPS位置
          _buildLocationSection(),
          
          if (widget.showStationInput) ...[
            const SizedBox(height: 24),
            _buildStationSection(),
          ],
          
          if (widget.showDescription) ...[
            const SizedBox(height: 24),
            _buildDescriptionSection(),
          ],
          
          // 错误提示
          if (_errorMessage != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: Colors.red.shade700),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _errorMessage!,
                      style: TextStyle(color: Colors.red.shade700),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
  
  /// 构建照片区域
  Widget _buildPhotoArea() {
    if (_capturedPhotoPath != null) {
      return Column(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Stack(
              children: [
                Image.file(
                  File(_capturedPhotoPath!),
                  height: 280,
                  width: double.infinity,
                  fit: BoxFit.cover,
                ),
                Positioned(
                  top: 8,
                  right: 8,
                  child: CircleAvatar(
                    backgroundColor: Colors.black54,
                    child: IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      onPressed: _retake,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => _showPhotoSourceDialog(),
            icon: const Icon(Icons.camera_alt),
            label: const Text('更换照片'),
          ),
        ],
      );
    }
    
    return Container(
      height: 280,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: _isCapturing
          ? const Center(child: CircularProgressIndicator())
          : Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.add_a_photo,
                  size: 64,
                  color: Colors.grey.shade400,
                ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ElevatedButton.icon(
                      onPressed: _takePhoto,
                      icon: const Icon(Icons.camera_alt),
                      label: const Text('拍照'),
                    ),
                    const SizedBox(width: 16),
                    OutlinedButton.icon(
                      onPressed: _pickFromGallery,
                      icon: const Icon(Icons.photo_library),
                      label: const Text('相册'),
                    ),
                  ],
                ),
              ],
            ),
    );
  }
  
  /// 显示照片来源选择对话框
  void _showPhotoSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('拍照'),
              onTap: () {
                Navigator.pop(context);
                _takePhoto();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('从相册选择'),
              onTap: () {
                Navigator.pop(context);
                _pickFromGallery();
              },
            ),
          ],
        ),
      ),
    );
  }
  
  /// 构建位置区域
  Widget _buildLocationSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.location_on,
                  color: _currentPosition != null ? Colors.green : Colors.grey,
                ),
                const SizedBox(width: 8),
                const Text(
                  'GPS位置',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                if (_isLoadingLocation)
                  const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                else
                  IconButton(
                    onPressed: _getCurrentLocation,
                    icon: const Icon(Icons.refresh),
                    tooltip: '刷新位置',
                  ),
              ],
            ),
            const SizedBox(height: 12),
            if (_currentPosition != null) ...[
              _buildInfoRow('纬度', _currentPosition!.latitude.toStringAsFixed(6)),
              _buildInfoRow('经度', _currentPosition!.longitude.toStringAsFixed(6)),
              _buildInfoRow(
                '精度', 
                '±${_currentPosition!.accuracy.toStringAsFixed(1)}米',
              ),
            ] else
              Text(
                _isLoadingLocation ? '正在获取位置...' : '点击刷新获取位置',
                style: TextStyle(color: Colors.grey.shade600),
              ),
          ],
        ),
      ),
    );
  }
  
  /// 构建桩号区域
  Widget _buildStationSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.linear_scale),
                const SizedBox(width: 8),
                const Text(
                  '桩号',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (_stationValue != null) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.green.shade100,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      _formatStation(_stationValue!),
                      style: TextStyle(
                        color: Colors.green.shade700,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _stationController,
                    decoration: InputDecoration(
                      hintText: '输入桩号 (如: K1+200)',
                      border: const OutlineInputBorder(),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 10,
                      ),
                      isDense: true,
                    ),
                    onSubmitted: (_) => _confirmStation(),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: _confirmStation,
                  child: const Text('确认'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '支持格式: K1+200, A0+500, 1200',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade600,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  /// 构建描述区域
  Widget _buildDescriptionSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.notes),
                const SizedBox(width: 8),
                const Text(
                  '描述',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descriptionController,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: '添加照片描述（可选）',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  /// 构建信息行
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 50,
            child: Text(
              '$label: ',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}

/// 独立的照片采集页面
class PhotoCaptureScreen extends StatelessWidget {
  /// 项目ID
  final String projectId;
  
  /// 照片采集完成回调
  final void Function(PhotoCaptureResult result)? onCapture;
  
  /// 是否显示桩号输入
  final bool showStationInput;
  
  /// 是否显示描述输入
  final bool showDescription;
  
  const PhotoCaptureScreen({
    super.key,
    required this.projectId,
    this.onCapture,
    this.showStationInput = true,
    this.showDescription = true,
  });
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('照片采集'),
        actions: [
          TextButton(
            onPressed: () {
              // 这里通过builder获取状态
              final state = context.findAncestorStateOfType<_PhotoCaptureState>();
              final result = state?.getResult();
              if (result != null) {
                onCapture?.call(result);
                Navigator.of(context).pop(result);
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('请先拍摄或选择照片')),
                );
              }
            },
            child: const Text('完成'),
          ),
        ],
      ),
      body: PhotoCapture(
        onCapture: (result) {
          onCapture?.call(result);
        },
        showStationInput: showStationInput,
        showDescription: showDescription,
      ),
    );
  }
}

/// 便捷函数：打开照片采集页面
Future<PhotoCaptureResult?> openPhotoCapture(
  BuildContext context, {
  required String projectId,
  bool showStationInput = true,
  bool showDescription = true,
}) {
  return Navigator.of(context).push<PhotoCaptureResult>(
    MaterialPageRoute(
      builder: (context) => PhotoCaptureScreen(
        projectId: projectId,
        showStationInput: showStationInput,
        showDescription: showDescription,
      ),
    ),
  );
}
