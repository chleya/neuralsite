import 'dart:io' as io;
import 'package:flutter/material.dart';
import '../services/services.dart';
import '../models/models.dart';

/// Data Collection Home Screen
/// Main entry point for field data collection
class DataCollectionScreen extends StatefulWidget {
  const DataCollectionScreen({super.key});

  @override
  State<DataCollectionScreen> createState() => _DataCollectionScreenState();
}

class _DataCollectionScreenState extends State<DataCollectionScreen> {
  int _pendingCount = 0;
  bool _isOnline = true;

  @override
  void initState() {
    super.initState();
    _loadSyncStatus();
  }

  Future<void> _loadSyncStatus() async {
    final count = await LocalDataService.instance.getPendingSyncCount();
    if (mounted) {
      setState(() {
        _pendingCount = count;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('数据采集'),
        actions: [
          // Sync status indicator
          StreamBuilder<SyncStatus>(
            stream: SyncService.instance.syncStatusStream,
            builder: (context, snapshot) {
              final isOnline = snapshot.data?.isOnline ?? true;
              final pending = snapshot.data?.pendingCount ?? _pendingCount;
              
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Row(
                  children: [
                    Icon(
                      isOnline ? Icons.cloud_done : Icons.cloud_off,
                      color: isOnline ? Colors.green : Colors.grey,
                      size: 20,
                    ),
                    if (pending > 0) ...[
                      const SizedBox(width: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.orange,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '$pending',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              );
            },
          ),
          // Manual sync button
          IconButton(
            icon: const Icon(Icons.sync),
            onPressed: () async {
              final result = await SyncService.instance.syncNow();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(result.message),
                    backgroundColor: result.success ? Colors.green : Colors.red,
                  ),
                );
                _loadSyncStatus();
              }
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Progress Report Card
            _buildMenuCard(
              icon: Icons.trending_up,
              title: '进度上报',
              subtitle: 'Report construction progress',
              color: Colors.blue,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ProgressReportScreen()),
              ),
            ),
            const SizedBox(height: 16),
            
            // Quality Issue Card
            _buildMenuCard(
              icon: Icons.warning_amber,
              title: '质量问题',
              subtitle: 'Report quality issues',
              color: Colors.orange,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const IssueReportScreen()),
              ),
            ),
            const SizedBox(height: 16),
            
            // Safety Check Card
            _buildMenuCard(
              icon: Icons.security,
              title: '安全检�?,
              subtitle: 'Safety inspection',
              color: Colors.red,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SafetyCheckScreen()),
              ),
            ),
            const SizedBox(height: 16),
            
            // Data History Card
            _buildMenuCard(
              icon: Icons.history,
              title: '历史记录',
              subtitle: 'View submitted data',
              color: Colors.grey,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const DataHistoryScreen()),
              ),
            ),
            
            const Spacer(),
            
            // Offline mode indicator
            if (!_isOnline)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.cloud_off, color: Colors.orange),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '离线模式 - 数据将在联网后自动同�?,
                        style: TextStyle(color: Colors.orange.shade800),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 32),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: Colors.grey.shade400),
            ],
          ),
        ),
      ),
    );
  }
}

/// Progress Report Screen
/// Allows workers to report construction progress
class ProgressReportScreen extends StatefulWidget {
  const ProgressReportScreen({super.key});

  @override
  State<ProgressReportScreen> createState() => _ProgressReportScreenState();
}

class _ProgressReportScreenState extends State<ProgressReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _chainageController = TextEditingController();
  final _quantityController = TextEditingController();
  final _noteController = TextEditingController();
  
  String? _selectedWorkType;
  String? _selectedUnit;
  ProgressStatus _selectedStatus = ProgressStatus.inProgress;
  
  double? _latitude;
  double? _longitude;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _getLocation();
  }

  Future<void> _getLocation() async {
    final position = await LocationService.instance.getCurrentPosition();
    if (position != null && mounted) {
      setState(() {
        _latitude = position.latitude;
        _longitude = position.longitude;
      });
    }
  }

  @override
  void dispose() {
    _chainageController.dispose();
    _quantityController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      final result = await LocalDataService.instance.submitProgress(
        chainage: _chainageController.text,
        status: _selectedStatus,
        note: _noteController.text.isNotEmpty ? _noteController.text : null,
        latitude: _latitude,
        longitude: _longitude,
        workType: _selectedWorkType,
        quantity: double.tryParse(_quantityController.text),
        unit: _selectedUnit,
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? '提交成功'),
            backgroundColor: result['status'] == 'success' ? Colors.green : Colors.orange,
          ),
        );
        
        if (result['status'] == 'success') {
          Navigator.pop(context);
        }
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('进度上报'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Chainage input
            TextFormField(
              controller: _chainageController,
              decoration: const InputDecoration(
                labelText: '施工桩号 (Chainage)',
                hintText: '例如: K12+345',
                prefixIcon: Icon(Icons.location_on),
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return '请输入桩�?;
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            
            // Work type dropdown
            DropdownButtonFormField<String>(
              value: _selectedWorkType,
              decoration: const InputDecoration(
                labelText: '施工类型 (Work Type)',
                prefixIcon: Icon(Icons.category),
                border: OutlineInputBorder(),
              ),
              items: WorkTypes.all.map((type) {
                return DropdownMenuItem(value: type, child: Text(type));
              }).toList(),
              onChanged: (value) => setState(() => _selectedWorkType = value),
              validator: (value) {
                if (value == null) return '请选择施工类型';
                return null;
              },
            ),
            const SizedBox(height: 16),
            
            // Status dropdown
            DropdownButtonFormField<ProgressStatus>(
              value: _selectedStatus,
              decoration: const InputDecoration(
                labelText: '进度状�?(Status)',
                prefixIcon: Icon(Icons.flag),
                border: OutlineInputBorder(),
              ),
              items: ProgressStatus.values.map((status) {
                return DropdownMenuItem(
                  value: status,
                  child: Text(status.displayName),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) setState(() => _selectedStatus = value);
              },
            ),
            const SizedBox(height: 16),
            
            // Quantity and Unit row
            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: _quantityController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: '完成工程�?,
                      prefixIcon: Icon(Icons.numbers),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _selectedUnit,
                    decoration: const InputDecoration(
                      labelText: '单位',
                      border: OutlineInputBorder(),
                    ),
                    items: ProgressUnits.all.map((unit) {
                      return DropdownMenuItem(value: unit, child: Text(unit));
                    }).toList(),
                    onChanged: (value) => setState(() => _selectedUnit = value),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Note
            TextFormField(
              controller: _noteController,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: '备注 (Note)',
                hintText: '添加任何额外说明...',
                prefixIcon: Icon(Icons.note),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            
            // Location display
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.gps_fixed, color: Colors.grey),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _latitude != null && _longitude != null
                          ? '位置: ${_latitude!.toStringAsFixed(6)}, ${_longitude!.toStringAsFixed(6)}'
                          : '正在获取位置...',
                      style: TextStyle(color: Colors.grey.shade700),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: _getLocation,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Submit button
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('提交进度', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Issue Report Screen
/// Allows workers to report quality issues with photos
class IssueReportScreen extends StatefulWidget {
  const IssueReportScreen({super.key});

  @override
  State<IssueReportScreen> createState() => _IssueReportScreenState();
}

class _IssueReportScreenState extends State<IssueReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _chainageController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  IssueSeverity _selectedSeverity = IssueSeverity.medium;
  String? _imagePath;
  double? _latitude;
  double? _longitude;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _getLocation();
  }

  Future<void> _getLocation() async {
    final position = await LocationService.instance.getCurrentPosition();
    if (position != null && mounted) {
      setState(() {
        _latitude = position.latitude;
        _longitude = position.longitude;
      });
    }
  }

  Future<void> _takePhoto() async {
    final photo = await CameraService.instance.takePhoto();
    if (photo != null && mounted) {
      setState(() => _imagePath = photo.path);
    }
  }

  Future<void> _pickPhoto() async {
    final photo = await CameraService.instance.pickFromGallery();
    if (photo != null && mounted) {
      setState(() => _imagePath = photo.path);
    }
  }

  @override
  void dispose() {
    _chainageController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    
    if (_imagePath == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请拍摄或选择照片')),
      );
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      final result = await LocalDataService.instance.submitIssue(
        chainage: _chainageController.text,
        description: _descriptionController.text,
        severity: _selectedSeverity,
        latitude: _latitude,
        longitude: _longitude,
        imagePath: _imagePath,
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? '提交成功'),
            backgroundColor: result['status'] == 'success' ? Colors.green : Colors.orange,
          ),
        );
        
        if (result['status'] == 'success') {
          Navigator.pop(context);
        }
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('质量问题上报'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Chainage input
            TextFormField(
              controller: _chainageController,
              decoration: const InputDecoration(
                labelText: '桩号 (Chainage)',
                hintText: '例如: K12+345',
                prefixIcon: Icon(Icons.location_on),
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return '请输入桩�?;
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            
            // Severity dropdown
            DropdownButtonFormField<IssueSeverity>(
              value: _selectedSeverity,
              decoration: const InputDecoration(
                labelText: '严重程度 (Severity)',
                prefixIcon: Icon(Icons.warning_amber),
                border: OutlineInputBorder(),
              ),
              items: IssueSeverity.values.map((severity) {
                return DropdownMenuItem(
                  value: severity,
                  child: Text(severity.displayName),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) setState(() => _selectedSeverity = value);
              },
            ),
            const SizedBox(height: 16),
            
            // Description
            TextFormField(
              controller: _descriptionController,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: '问题描述 (Description)',
                hintText: '详细描述发现的质量问�?..',
                prefixIcon: Icon(Icons.description),
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return '请输入问题描�?;
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            
            // Photo section
            const Text(
              '现场照片',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            
            if (_imagePath != null)
              Stack(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.file(
                      io.File(_imagePath!),
                      height: 200,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        height: 200,
                        color: Colors.grey.shade200,
                        child: const Icon(Icons.broken_image, size: 50),
                      ),
                    ),
                  ),
                  Positioned(
                    top: 8,
                    right: 8,
                    child: IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      style: IconButton.styleFrom(backgroundColor: Colors.black54),
                      onPressed: () => setState(() => _imagePath = null),
                    ),
                  ),
                ],
              )
            else
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _takePhoto,
                      icon: const Icon(Icons.camera_alt),
                      label: const Text('拍照'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.all(16),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _pickPhoto,
                      icon: const Icon(Icons.photo_library),
                      label: const Text('相册'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.all(16),
                      ),
                    ),
                  ),
                ],
              ),
            const SizedBox(height: 16),
            
            // Location display
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.gps_fixed, color: Colors.grey),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _latitude != null && _longitude != null
                          ? '位置: ${_latitude!.toStringAsFixed(6)}, ${_longitude!.toStringAsFixed(6)}'
                          : '正在获取位置...',
                      style: TextStyle(color: Colors.grey.shade700),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: _getLocation,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Submit button
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('提交问题', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Safety Check Screen
/// Allows workers to perform safety inspections
class SafetyCheckScreen extends StatefulWidget {
  const SafetyCheckScreen({super.key});

  @override
  State<SafetyCheckScreen> createState() => _SafetyCheckScreenState();
}

class _SafetyCheckScreenState extends State<SafetyCheckScreen> {
  final _formKey = GlobalKey<FormState>();
  final _chainageController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _findingsController = TextEditingController();
  final _inspectorController = TextEditingController();
  
  SafetyCheckType _selectedCheckType = SafetyCheckType.routine;
  SafetyStatus _selectedStatus = SafetyStatus.pending;
  String? _imagePath;
  double? _latitude;
  double? _longitude;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _getLocation();
  }

  Future<void> _getLocation() async {
    final position = await LocationService.instance.getCurrentPosition();
    if (position != null && mounted) {
      setState(() {
        _latitude = position.latitude;
        _longitude = position.longitude;
      });
    }
  }

  Future<void> _takePhoto() async {
    final photo = await CameraService.instance.takePhoto();
    if (photo != null && mounted) {
      setState(() => _imagePath = photo.path);
    }
  }

  @override
  void dispose() {
    _chainageController.dispose();
    _descriptionController.dispose();
    _findingsController.dispose();
    _inspectorController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      final result = await LocalDataService.instance.submitSafetyCheck(
        chainage: _chainageController.text,
        checkType: _selectedCheckType,
        status: _selectedStatus,
        description: _descriptionController.text.isNotEmpty ? _descriptionController.text : null,
        findings: _findingsController.text.isNotEmpty ? _findingsController.text : null,
        inspector: _inspectorController.text.isNotEmpty ? _inspectorController.text : null,
        latitude: _latitude,
        longitude: _longitude,
        imagePath: _imagePath,
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? '提交成功'),
            backgroundColor: result['status'] == 'success' ? Colors.green : Colors.orange,
          ),
        );
        
        if (result['status'] == 'success') {
          Navigator.pop(context);
        }
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('安全检�?),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Chainage input
            TextFormField(
              controller: _chainageController,
              decoration: const InputDecoration(
                labelText: '检查位置桩�?(Chainage)',
                hintText: '例如: K12+345',
                prefixIcon: Icon(Icons.location_on),
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return '请输入桩�?;
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            
            // Check type dropdown
            DropdownButtonFormField<SafetyCheckType>(
              value: _selectedCheckType,
              decoration: const InputDecoration(
                labelText: '检查类�?(Check Type)',
                prefixIcon: Icon(Icons.checklist),
                border: OutlineInputBorder(),
              ),
              items: SafetyCheckType.values.map((type) {
                return DropdownMenuItem(
                  value: type,
                  child: Text(type.displayName),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) setState(() => _selectedCheckType = value);
              },
            ),
            const SizedBox(height: 16),
            
            // Inspector name
            TextFormField(
              controller: _inspectorController,
              decoration: const InputDecoration(
                labelText: '检查人 (Inspector)',
                prefixIcon: Icon(Icons.person),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            
            // Description
            TextFormField(
              controller: _descriptionController,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: '检查描�?(Description)',
                prefixIcon: Icon(Icons.description),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            
            // Findings
            TextFormField(
              controller: _findingsController,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: '检查发�?(Findings)',
                hintText: '记录发现的安全隐�?..',
                prefixIcon: Icon(Icons.report_problem),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            
            // Status selection
            const Text(
              '检查结�?,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: SafetyStatus.values.map((status) {
                final isSelected = _selectedStatus == status;
                return ChoiceChip(
                  label: Text(status.displayName),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedStatus = status);
                  },
                  selectedColor: _getStatusColor(status).withOpacity(0.3),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            
            // Photo section
            const Text(
              '隐患照片 (如有)',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            
            if (_imagePath != null)
              Stack(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.file(
                      io.File(_imagePath!),
                      height: 200,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        height: 200,
                        color: Colors.grey.shade200,
                        child: const Icon(Icons.broken_image, size: 50),
                      ),
                    ),
                  ),
                  Positioned(
                    top: 8,
                    right: 8,
                    child: IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      style: IconButton.styleFrom(backgroundColor: Colors.black54),
                      onPressed: () => setState(() => _imagePath = null),
                    ),
                  ),
                ],
              )
            else
              OutlinedButton.icon(
                onPressed: _takePhoto,
                icon: const Icon(Icons.camera_alt),
                label: const Text('拍摄隐患照片'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                ),
              ),
            const SizedBox(height: 16),
            
            // Location display
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.gps_fixed, color: Colors.grey),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _latitude != null && _longitude != null
                          ? '位置: ${_latitude!.toStringAsFixed(6)}, ${_longitude!.toStringAsFixed(6)}'
                          : '正在获取位置...',
                      style: TextStyle(color: Colors.grey.shade700),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: _getLocation,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            
            // Submit button
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('提交检�?, style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Color _getStatusColor(SafetyStatus status) {
    switch (status) {
      case SafetyStatus.pass:
        return Colors.green;
      case SafetyStatus.fail:
        return Colors.red;
      case SafetyStatus.needsAttention:
        return Colors.orange;
      case SafetyStatus.pending:
        return Colors.grey;
      case SafetyStatus.resolved:
        return Colors.blue;
    }
  }
}

/// Data History Screen
/// Shows all submitted data
class DataHistoryScreen extends StatefulWidget {
  const DataHistoryScreen({super.key});

  @override
  State<DataHistoryScreen> createState() => _DataHistoryScreenState();
}

class _DataHistoryScreenState extends State<DataHistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  List<Progress> _progressList = [];
  List<Issue> _issueList = [];
  List<SafetyCheck> _safetyCheckList = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    
    try {
      final progress = await LocalDataService.instance.getAllProgress();
      final issues = await LocalDataService.instance.getAllIssues();
      final safetyChecks = await LocalDataService.instance.getAllSafetyChecks();
      
      if (mounted) {
        setState(() {
          _progressList = progress;
          _issueList = issues;
          _safetyCheckList = safetyChecks;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('历史记录'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '进度'),
            Tab(text: '质量问题'),
            Tab(text: '安全检�?),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildProgressList(),
                _buildIssueList(),
                _buildSafetyCheckList(),
              ],
            ),
    );
  }

  Widget _buildProgressList() {
    if (_progressList.isEmpty) {
      return const Center(child: Text('暂无进度记录'));
    }
    
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: _progressList.length,
        itemBuilder: (context, index) {
          final item = _progressList[index];
          return Card(
            child: ListTile(
              leading: Icon(
                item.synced ? Icons.cloud_done : Icons.cloud_off,
                color: item.synced ? Colors.green : Colors.orange,
              ),
              title: Text('${item.chainage} - ${item.status.displayName}'),
              subtitle: Text(
                '${item.workType ?? ""} ${item.quantity != null ? "${item.quantity} ${item.unit}" : ""}',
              ),
              trailing: Text(
                _formatDate(item.timestamp),
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildIssueList() {
    if (_issueList.isEmpty) {
      return const Center(child: Text('暂无质量问题记录'));
    }
    
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: _issueList.length,
        itemBuilder: (context, index) {
          final item = _issueList[index];
          return Card(
            child: ListTile(
              leading: Icon(
                item.synced ? Icons.cloud_done : Icons.cloud_off,
                color: item.synced ? Colors.green : Colors.orange,
              ),
              title: Text('${item.chainage} - ${item.severity.displayName}'),
              subtitle: Text(item.description, maxLines: 2, overflow: TextOverflow.ellipsis),
              trailing: Text(
                _formatDate(item.timestamp),
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSafetyCheckList() {
    if (_safetyCheckList.isEmpty) {
      return const Center(child: Text('暂无安全检查记�?));
    }
    
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: _safetyCheckList.length,
        itemBuilder: (context, index) {
          final item = _safetyCheckList[index];
          return Card(
            child: ListTile(
              leading: Icon(
                item.synced ? Icons.cloud_done : Icons.cloud_off,
                color: item.synced ? Colors.green : Colors.orange,
              ),
              title: Text('${item.chainage} - ${item.checkType.displayName}'),
              subtitle: Text(item.status.displayName),
              trailing: Text(
                _formatDate(item.timestamp),
                style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
              ),
            ),
          );
        },
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.month}/${date.day} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
}
