// NeuralSite 移动端拍摄屏幕
// 拍照+上传UI, GPS显示, 桩号输入

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart';
import '../services/photo_service.dart';
import '../services/sync_service.dart';
import '../sync/offline_sync.dart';

/// 拍摄屏幕
class CaptureScreen extends StatefulWidget {
  final String projectId;
  final IssueType? issueType;
  final String? issueTitle;
  
  const CaptureScreen({
    super.key,
    required this.projectId,
    this.issueType,
    this.issueTitle,
  });
  
  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  late final PhotoService _photoService;
  final TextEditingController _stationController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  
  String? _capturedPhotoPath;
  Position? _currentPosition;
  double? _stationValue;
  bool _isLoadingLocation = false;
  bool _isSaving = false;
  String? _errorMessage;
  
  @override
  void initState() {
    super.initState();
    // 在initState中获取dio，因为context在这里才可用
    _photoService = PhotoService(
      dio: context.read<SyncService>().dio,
    );
    _getCurrentLocation();
  }
  
  @override
  void dispose() {
    _stationController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }
  
  /// 获取当前位置
  Future<void> _getCurrentLocation() async {
    setState(() {
      _isLoadingLocation = true;
      _errorMessage = null;
    });
    
    try {
      final position = await _photoService.getCurrentLocation();
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
    try {
      final path = await _photoService.takePhoto();
      if (path != null) {
        setState(() {
          _capturedPhotoPath = path;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    }
  }
  
  /// 从相册选择
  Future<void> _pickFromGallery() async {
    try {
      final path = await _photoService.pickFromGallery();
      if (path != null) {
        setState(() {
          _capturedPhotoPath = path;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    }
  }
  
  /// 确认桩号
  void _confirmStation() {
    final station = _photoService.parseStation(_stationController.text);
    if (station != null) {
      setState(() {
        _stationValue = station;
        _stationController.text = _photoService.formatStation(station);
      });
    } else {
      setState(() {
        _errorMessage = '无效的桩号格式';
      });
    }
  }
  
  /// 保存照片记录
  Future<void> _savePhoto() async {
    if (_capturedPhotoPath == null) {
      setState(() {
        _errorMessage = '请先拍摄或选择照片';
      });
      return;
    }
    
    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });
    
    try {
      final syncService = context.read<SyncService>();
      
      // 创建照片记录
      final photo = _photoService.createPhotoRecord(
        projectId: widget.projectId,
        filePath: _capturedPhotoPath!,
        latitude: _currentPosition?.latitude,
        longitude: _currentPosition?.longitude,
        station: _stationValue,
        stationDisplay: _stationController.text.isNotEmpty 
            ? _stationController.text 
            : null,
        description: _descriptionController.text.isNotEmpty 
            ? _descriptionController.text 
            : null,
      );
      
      // 保存到本地数据库
      final db = LocalDatabase.instance;
      await db.then((database) async {
        await database.insertPhoto(photo);
      });
      
      // 如果在线，尝试上传
      if (syncService.isOnline) {
        try {
          await _photoService.uploadPhoto(
            _capturedPhotoPath!,
            projectId: widget.projectId,
          );
        } catch (e) {
          // 上传失败会在下次同步时重试
        }
      }
      
      if (mounted) {
        // 返回成功结果
        Navigator.of(context).pop({
          'success': true,
          'photoPath': _capturedPhotoPath,
          'station': _stationValue,
          'position': _currentPosition,
        });
      }
    } catch (e) {
      setState(() {
        _isSaving = false;
        _errorMessage = '保存失败: $e';
      });
    }
  }
  
  /// 重拍
  void _retake() {
    if (_capturedPhotoPath != null) {
      _photoService.deletePhoto(_capturedPhotoPath!);
    }
    setState(() {
      _capturedPhotoPath = null;
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.issueTitle ?? '拍摄照片'),
        actions: [
          if (_capturedPhotoPath != null)
            TextButton(
              onPressed: _retake,
              child: const Text('重拍'),
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 照片预览/拍摄区域
            _buildPhotoArea(),
            
            const SizedBox(height: 24),
            
            // GPS位置
            _buildLocationSection(),
            
            const SizedBox(height: 24),
            
            // 桩号输入
            _buildStationSection(),
            
            const SizedBox(height: 24),
            
            // 描述
            _buildDescriptionSection(),
            
            const SizedBox(height: 24),
            
            // 错误提示
            if (_errorMessage != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Colors.red.shade700),
                ),
              ),
            
            const SizedBox(height: 24),
            
            // 保存按钮
            _buildSaveButton(),
          ],
        ),
      ),
    );
  }
  
  /// 构建照片区域
  Widget _buildPhotoArea() {
    if (_capturedPhotoPath != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Image.file(
          File(_capturedPhotoPath!),
          height: 300,
          fit: BoxFit.cover,
        ),
      );
    }
    
    return Container(
      height: 300,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.camera_alt_outlined,
            size: 64,
            color: Colors.grey.shade400,
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
                _isLoadingLocation ? '正在获取位置...' : '无法获取位置',
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
                      _photoService.formatStation(_stationValue!),
                      style: TextStyle(color: Colors.green.shade700),
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
                        vertical: 8,
                      ),
                      suffixIcon: IconButton(
                        onPressed: () => _stationController.clear(),
                        icon: const Icon(Icons.clear),
                      ),
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
  
  /// 构建保存按钮
  Widget _buildSaveButton() {
    return ElevatedButton(
      onPressed: _capturedPhotoPath != null && !_isSaving ? _savePhoto : null,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
        backgroundColor: Theme.of(context).primaryColor,
        foregroundColor: Colors.white,
      ),
      child: _isSaving
          ? const SizedBox(
              height: 20,
              width: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : const Text(
              '保存照片',
              style: TextStyle(fontSize: 16),
            ),
    );
  }
  
  /// 构建信息行
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(
            '$label: ',
            style: TextStyle(color: Colors.grey.shade600),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}

/// 便捷函数：打开拍摄屏幕
Future<Map<String, dynamic>?> openCaptureScreen(
  BuildContext context, {
  required String projectId,
  IssueType? issueType,
  String? issueTitle,
}) {
  return Navigator.of(context).push<Map<String, dynamic>>(
    MaterialPageRoute(
      builder: (context) => CaptureScreen(
        projectId: projectId,
        issueType: issueType,
        issueTitle: issueTitle,
      ),
    ),
  );
}
