import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'models/models.dart';
import 'providers/providers.dart';
import 'services/offline_data_initializer.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 初始化示例离线数据（首次启动时）
  await OfflineDataInitializer.instance.initializeSampleData();
  
  runApp(const ProviderScope(child: NeuralSiteApp()));
}

class NeuralSiteApp extends ConsumerWidget {
  const NeuralSiteApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'NeuralSite Mobile',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    // Start periodic sync
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(syncServiceProvider).startPeriodicSync();
    });
  }

  final List<Widget> _screens = [
    const DashboardScreen(),
    const IssuesScreen(),
    const ProgressScreen(),
    const SafetyCheckScreen(),
    const CaptureScreen(),
    const AdvisorScreen(),
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final syncStatus = ref.watch(syncStatusProvider);
    final isOnline = syncStatus.when(
      data: (status) => status.isOnline,
      loading: () => true,
      error: (_, __) => false,
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('NeuralSite'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          // Online/Offline indicator
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: Row(
              children: [
                Icon(
                  isOnline ? Icons.cloud_done : Icons.cloud_off,
                  size: 18,
                  color: isOnline ? Colors.green : Colors.grey,
                ),
                const SizedBox(width: 4),
                Text(
                  isOnline ? 'Online' : 'Offline',
                  style: TextStyle(
                    fontSize: 12,
                    color: isOnline ? Colors.green : Colors.grey,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          const NavigationDestination(
            icon: Icon(Icons.report_problem),
            label: 'Issues',
          ),
          const NavigationDestination(
            icon: Icon(Icons.trending_up),
            label: 'Progress',
          ),
          const NavigationDestination(
            icon: Icon(Icons.health_and_safety),
            label: 'Safety',
          ),
          const NavigationDestination(
            icon: Icon(Icons.add_a_photo),
            label: 'Capture',
          ),
          const NavigationDestination(
            icon: Icon(Icons.lightbulb),
            label: 'Advisor',
          ),
          const NavigationDestination(
            icon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

// ==================== Dashboard Screen ====================

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectsAsync = ref.watch(projectsProvider);
    final photosAsync = ref.watch(photosProvider);
    final syncStatusAsync = ref.watch(syncStatusProvider);
    final pendingCount = ref.watch(pendingSyncCountProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(projectsProvider);
        ref.invalidate(photosProvider);
        ref.invalidate(pendingSyncCountProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Icon(Icons.architecture, size: 60, color: Colors.blue),
                  const SizedBox(height: 12),
                  const Text(
                    'NeuralSite Mobile',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  const Text('Construction Management', style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 16),
                  syncStatusAsync.when(
                    data: (status) => Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          status.isSyncing ? Icons.sync : Icons.check_circle,
                          size: 16,
                          color: status.isSyncing ? Colors.orange : Colors.green,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          status.isSyncing ? 'Syncing...' : 'Connected',
                          style: TextStyle(
                            fontSize: 12,
                            color: status.isSyncing ? Colors.orange : Colors.green,
                          ),
                        ),
                      ],
                    ),
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Stats Row
          Row(
            children: [
              Expanded(
                child: projectsAsync.when(
                  data: (projects) => _StatCard(
                    'Projects',
                    '${projects.length}',
                    Icons.folder,
                    Colors.blue,
                  ),
                  loading: () => _StatCard('Projects', '...', Icons.folder, Colors.blue),
                  error: (_, __) => _StatCard('Projects', '0', Icons.folder, Colors.blue),
                ),
              ),
              Expanded(
                child: photosAsync.when(
                  data: (photos) => _StatCard(
                    'Photos',
                    '${photos.length}',
                    Icons.photo_camera,
                    Colors.orange,
                  ),
                  loading: () => _StatCard('Photos', '...', Icons.photo_camera, Colors.orange),
                  error: (_, __) => _StatCard('Photos', '0', Icons.photo_camera, Colors.orange),
                ),
              ),
              Expanded(
                child: pendingCount.when(
                  data: (count) => _StatCard(
                    'Pending',
                    '$count',
                    Icons.cloud_upload,
                    count > 0 ? Colors.red : Colors.green,
                  ),
                  loading: () => _StatCard('Pending', '...', Icons.cloud_upload, Colors.grey),
                  error: (_, __) => _StatCard('Pending', '0', Icons.cloud_upload, Colors.green),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Recent Photos
          const Text('Recent Photos', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          photosAsync.when(
            data: (photos) {
              if (photos.isEmpty) {
                return const Card(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(
                      child: Text('No photos yet. Go to Capture to take one!'),
                    ),
                  ),
                );
              }
              return SizedBox(
                height: 120,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: photos.length > 5 ? 5 : photos.length,
                  itemBuilder: (context, index) {
                    final photo = photos[index];
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: _PhotoThumbnail(photo: photo),
                    );
                  },
                ),
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => const Center(child: Text('Error loading photos')),
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard(this.title, this.value, this.icon, this.color);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, size: 28, color: color),
            const SizedBox(height: 8),
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            Text(title, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}

class _PhotoThumbnail extends StatelessWidget {
  final Photo photo;

  const _PhotoThumbnail({required this.photo});

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        width: 120,
        height: 120,
        child: Stack(
          fit: StackFit.expand,
          children: [
            photo.localPath != null
                ? Image.file(
                    File(photo.localPath!),
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, size: 40),
                  )
                : const Icon(Icons.photo, size: 40),
            Positioned(
              bottom: 0,
              left: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.all(4),
                color: Colors.black54,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      photo.chainage ?? 'N/A',
                      style: const TextStyle(color: Colors.white, fontSize: 10),
                    ),
                    Icon(
                      photo.syncStatus == PhotoSyncStatus.synced
                          ? Icons.cloud_done
                          : Icons.cloud_upload,
                      size: 12,
                      color: photo.syncStatus == PhotoSyncStatus.synced
                          ? Colors.green
                          : Colors.orange,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ==================== Issues Screen ====================

class IssuesScreen extends ConsumerWidget {
  const IssuesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issuesAsync = ref.watch(issuesProvider);

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(issuesProvider);
      },
      child: issuesAsync.when(
        data: (issues) {
          if (issues.isEmpty) {
            return const Center(
              child: Text('No issues reported yet'),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: issues.length,
            itemBuilder: (context, index) {
              final issue = issues[index];
              return _IssueCard(issue: issue);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _IssueCard extends StatelessWidget {
  final Map<String, dynamic> issue;

  const _IssueCard({required this.issue});

  @override
  Widget build(BuildContext context) {
    final severity = issue['severity'] as String? ?? 'Info';
    final color = severity == 'Critical' ? Colors.red : severity == 'Warning' ? Colors.orange : Colors.blue;
    
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color,
          child: Text(severity[0], style: const TextStyle(color: Colors.white)),
        ),
        title: Text(issue['chainage'] as String? ?? 'N/A'),
        subtitle: Text(issue['description'] as String? ?? ''),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              severity,
              style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
            ),
            Icon(
              (issue['synced'] as int?) == 1 ? Icons.cloud_done : Icons.cloud_upload,
              size: 14,
              color: (issue['synced'] as int?) == 1 ? Colors.green : Colors.orange,
            ),
          ],
        ),
      ),
    );
  }
}

// ==================== Capture Screen ====================

class CaptureScreen extends ConsumerWidget {
  const CaptureScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final captureState = ref.watch(photoCaptureProvider);
    final locationPermission = ref.watch(locationPermissionProvider);

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Location status
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  const Icon(Icons.location_on, size: 40, color: Colors.blue),
                  const SizedBox(height: 8),
                  locationPermission.when(
                    data: (status) => Column(
                      children: [
                        Text(
                          status.displayName,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: status.isGranted ? Colors.green : Colors.red,
                          ),
                        ),
                        if (!status.isGranted)
                          ElevatedButton(
                            onPressed: () async {
                              await ref.read(locationServiceProvider).requestPermission();
                              ref.invalidate(locationPermissionProvider);
                            },
                            child: const Text('Grant Permission'),
                          ),
                      ],
                    ),
                    loading: () => const Text('Checking...'),
                    error: (_, __) => const Text('Error checking permission'),
                  ),
                  if (captureState.position != null) ...[
                    const Divider(),
                    Text(
                      'Lat: ${captureState.position!.latitude.toStringAsFixed(6)}',
                      style: const TextStyle(fontSize: 12),
                    ),
                    Text(
                      'Lng: ${captureState.position!.longitude.toStringAsFixed(6)}',
                      style: const TextStyle(fontSize: 12),
                    ),
                    if (captureState.chainage != null)
                      Text(
                        'Chainage: ${captureState.chainage}',
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                      ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Error message
          if (captureState.error != null)
            Card(
              color: Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const Icon(Icons.error, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(child: Text(captureState.error!)),
                  ],
                ),
              ),
            ),

          const Spacer(),

          // Capture button
          SizedBox(
            width: double.infinity,
            height: 80,
            child: ElevatedButton.icon(
              onPressed: captureState.isCapturing
                  ? null
                  : () => ref.read(photoCaptureProvider.notifier).capturePhoto(),
              icon: captureState.isCapturing
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.camera_alt, size: 32),
              label: Text(
                captureState.isCapturing ? 'Capturing...' : 'Take Photo',
                style: const TextStyle(fontSize: 18),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Quick actions
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () async {
                    final cameraService = ref.read(cameraServiceProvider);
                    await cameraService.pickFromGallery();
                  },
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Gallery'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    ref.invalidate(photosProvider);
                    ref.read(photoCaptureProvider.notifier).reset();
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reset'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ==================== Advisor Screen ====================

class AdvisorScreen extends ConsumerStatefulWidget {
  const AdvisorScreen({super.key});

  @override
  ConsumerState<AdvisorScreen> createState() => _AdvisorScreenState();
}

class _AdvisorScreenState extends ConsumerState<AdvisorScreen> {
  final _controller = TextEditingController();
  String? _answer;
  bool _isLoading = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _askAdvisor() async {
    if (_controller.text.isEmpty) return;

    setState(() {
      _isLoading = true;
      _answer = null;
    });

    try {
      final result = await ApiService.askAdvisor(_controller.text);
      setState(() {
        _answer = result['answer'] ?? result['message'] ?? 'No answer received';
      });
    } catch (e) {
      setState(() {
        _answer = 'Error: ${e.toString()}';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Ask the Advisor',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Ask questions about construction standards, specifications, or get guidance on issues.',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            decoration: const InputDecoration(
              hintText: 'e.g., "minimum curve radius for 100km/h"',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: _isLoading ? null : _askAdvisor,
            child: _isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Ask'),
          ),
          if (_answer != null) ...[
            const SizedBox(height: 20),
            Card(
              color: Colors.blue.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.lightbulb, color: Colors.amber),
                        const SizedBox(width: 8),
                        const Text(
                          'Answer',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const Divider(),
                    Text(_answer!),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ==================== Settings Screen ====================

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final apiUrl = ref.watch(apiServerUrlProvider);
    final offlineMode = ref.watch(offlineModeProvider);
    final autoSync = ref.watch(autoSyncProvider);
    final syncStatus = ref.watch(syncStatusProvider);

    return ListView(
      children: [
        // Connection Status
        ListTile(
          leading: Icon(
            syncStatus.when(
              data: (s) => s.isOnline ? Icons.cloud_done : Icons.cloud_off,
              loading: () => Icons.cloud,
              error: (_, __) => Icons.cloud_off,
            ),
            color: syncStatus.when(
              data: (s) => s.isOnline ? Colors.green : Colors.red,
              loading: () => Colors.grey,
              error: (_, __) => Colors.red,
            ),
          ),
          title: const Text('Connection Status'),
          subtitle: syncStatus.when(
            data: (s) => Text(s.isOnline ? 'Connected' : 'Offline'),
            loading: () => const Text('Checking...'),
            error: (_, __) => const Text('Unknown'),
          ),
        ),
        const Divider(),

        // API Server
        ListTile(
          leading: const Icon(Icons.dns),
          title: const Text('API Server'),
          subtitle: Text(apiUrl),
          trailing: const Icon(Icons.chevron_right),
          onTap: () {
            // Show edit dialog
          },
        ),
        const Divider(),

        // Offline Mode
        SwitchListTile(
          secondary: const Icon(Icons.wifi_off),
          title: const Text('Offline Mode'),
          subtitle: const Text('Enable offline data collection'),
          value: offlineMode,
          onChanged: (value) {
            ref.read(offlineModeProvider.notifier).state = value;
          },
        ),

        // Auto Sync
        SwitchListTile(
          secondary: const Icon(Icons.sync),
          title: const Text('Auto Sync'),
          subtitle: const Text('Automatically sync when online'),
          value: autoSync,
          onChanged: (value) {
            ref.read(autoSyncProvider.notifier).state = value;
            if (value) {
              ref.read(syncServiceProvider).startPeriodicSync();
            } else {
              ref.read(syncServiceProvider).stopPeriodicSync();
            }
          },
        ),

        // Sync Now
        ListTile(
          leading: const Icon(Icons.cloud_sync),
          title: const Text('Sync Now'),
          subtitle: const Text('Manually trigger sync'),
          onTap: () async {
            final result = await ref.read(syncServiceProvider).syncNow();
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(result.message),
                  backgroundColor: result.success ? Colors.green : Colors.red,
                ),
              );
            }
          },
        ),
        const Divider(),

        // Clear Data
        ListTile(
          leading: const Icon(Icons.delete_forever, color: Colors.red),
          title: const Text('Clear Local Data', style: TextStyle(color: Colors.red)),
          subtitle: const Text('Remove all local data'),
          onTap: () {
            showDialog(
              context: context,
              builder: (context) => AlertDialog(
                title: const Text('Clear Data?'),
                content: const Text('This will delete all local data. This action cannot be undone.'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Cancel'),
                  ),
                  TextButton(
                    onPressed: () async {
                      final db = ref.read(databaseProvider);
                      await db.clearAllData();
                      ref.invalidate(photosProvider);
                      ref.invalidate(issuesProvider);
                      if (context.mounted) {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Data cleared')),
                        );
                      }
                    },
                    child: const Text('Clear', style: TextStyle(color: Colors.red)),
                  ),
                ],
              ),
            );
          },
        ),
        const Divider(),

        // Version
        const ListTile(
          leading: Icon(Icons.info),
          title: Text('Version'),
          subtitle: Text('1.0.0'),
        ),
      ],
    );
  }
}

// ==================== Progress Screen ====================

class ProgressScreen extends ConsumerWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final progressAsync = ref.watch(progressProvider);

    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddProgressDialog(context, ref),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(progressProvider);
        },
        child: progressAsync.when(
          data: (progressList) {
            if (progressList.isEmpty) {
              return const Center(
                child: Text('No progress reports yet'),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: progressList.length,
              itemBuilder: (context, index) {
                final progress = progressList[index];
                return _ProgressCard(progress: progress);
              },
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Error: $e')),
        ),
      ),
    );
  }

  void _showAddProgressDialog(BuildContext context, WidgetRef ref) {
    final chainageController = TextEditingController();
    final noteController = TextEditingController();
    String selectedStatus = 'inProgress';
    String selectedWorkType = 'Earthwork';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Progress Report'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: chainageController,
                decoration: const InputDecoration(
                  labelText: 'Chainage (e.g., K1+500)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: const InputDecoration(
                  labelText: 'Status',
                  border: OutlineInputBorder(),
                ),
                items: ['planned', 'inProgress', 'completed', 'delayed', 'blocked']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => selectedStatus = v!,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedWorkType,
                decoration: const InputDecoration(
                  labelText: 'Work Type',
                  border: OutlineInputBorder(),
                ),
                items: ['Earthwork', 'Pavement', 'Bridge', 'Tunnel', 'Drainage', 'Utility', 'Other']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => selectedWorkType = v!,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: noteController,
                decoration: const InputDecoration(
                  labelText: 'Note',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (chainageController.text.isEmpty) return;

              final db = ref.read(databaseProvider);
              await db.insertProgress({
                'id': const Uuid().v4(),
                'chainage': chainageController.text,
                'status': selectedStatus,
                'work_type': selectedWorkType,
                'note': noteController.text,
                'timestamp': DateTime.now().toIso8601String(),
                'synced': 0,
                'created_at': DateTime.now().toIso8601String(),
              });

              ref.invalidate(progressProvider);
              if (context.mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Progress added')),
                );
              }
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
}

class _ProgressCard extends StatelessWidget {
  final Map<String, dynamic> progress;

  const _ProgressCard({required this.progress});

  @override
  Widget build(BuildContext context) {
    final status = progress['status'] as String? ?? 'unknown';
    final statusColor = status == 'completed' ? Colors.green 
        : status == 'inProgress' ? Colors.blue 
        : status == 'delayed' ? Colors.orange 
        : status == 'blocked' ? Colors.red 
        : Colors.grey;

    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: statusColor,
          child: Icon(
            status == 'completed' ? Icons.check : Icons.trending_up,
            color: Colors.white,
          ),
        ),
        title: Text(progress['chainage'] as String? ?? 'N/A'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(progress['work_type'] as String? ?? ''),
            Text(
              progress['note'] as String? ?? '',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              status,
              style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12),
            ),
            Icon(
              (progress['synced'] as int?) == 1 ? Icons.cloud_done : Icons.cloud_upload,
              size: 14,
              color: (progress['synced'] as int?) == 1 ? Colors.green : Colors.orange,
            ),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }
}

// ==================== Safety Check Screen ====================

class SafetyCheckScreen extends ConsumerWidget {
  const SafetyCheckScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final safetyAsync = ref.watch(safetyChecksProvider);

    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddSafetyCheckDialog(context, ref),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(safetyChecksProvider);
        },
        child: safetyAsync.when(
          data: (checks) {
            if (checks.isEmpty) {
              return const Center(
                child: Text('No safety checks recorded yet'),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: checks.length,
              itemBuilder: (context, index) {
                final check = checks[index];
                return _SafetyCheckCard(check: check);
              },
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Error: $e')),
        ),
      ),
    );
  }

  void _showAddSafetyCheckDialog(BuildContext context, WidgetRef ref) {
    final chainageController = TextEditingController();
    final descriptionController = TextEditingController();
    final findingsController = TextEditingController();
    final inspectorController = TextEditingController();
    String selectedType = 'routine';
    String selectedStatus = 'pending';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Safety Check'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: chainageController,
                decoration: const InputDecoration(
                  labelText: 'Chainage (e.g., K1+500)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedType,
                decoration: const InputDecoration(
                  labelText: 'Check Type',
                  border: OutlineInputBorder(),
                ),
                items: ['routine', 'focused', 'incident', 'compliance', 'emergency']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => selectedType = v!,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedStatus,
                decoration: const InputDecoration(
                  labelText: 'Status',
                  border: OutlineInputBorder(),
                ),
                items: ['pending', 'pass', 'fail', 'needsAttention', 'resolved']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => selectedStatus = v!,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: inspectorController,
                decoration: const InputDecoration(
                  labelText: 'Inspector Name',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description',
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: findingsController,
                decoration: const InputDecoration(
                  labelText: 'Findings',
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (chainageController.text.isEmpty) return;

              final db = ref.read(databaseProvider);
              await db.insertSafetyCheck({
                'id': const Uuid().v4(),
                'chainage': chainageController.text,
                'check_type': selectedType,
                'status': selectedStatus,
                'description': descriptionController.text,
                'findings': findingsController.text,
                'inspector': inspectorController.text,
                'timestamp': DateTime.now().toIso8601String(),
                'synced': 0,
                'created_at': DateTime.now().toIso8601String(),
              });

              ref.invalidate(safetyChecksProvider);
              if (context.mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Safety check added')),
                );
              }
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
}

class _SafetyCheckCard extends StatelessWidget {
  final Map<String, dynamic> check;

  const _SafetyCheckCard({required this.check});

  @override
  Widget build(BuildContext context) {
    final status = check['status'] as String? ?? 'pending';
    final checkType = check['check_type'] as String? ?? 'routine';
    
    final statusColor = status == 'pass' ? Colors.green 
        : status == 'fail' ? Colors.red 
        : status == 'needsAttention' ? Colors.orange 
        : status == 'resolved' ? Colors.blue 
        : Colors.grey;

    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: statusColor,
          child: Icon(
            status == 'pass' ? Icons.check_circle : Icons.warning,
            color: Colors.white,
          ),
        ),
        title: Text(check['chainage'] as String? ?? 'N/A'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Type: $checkType'),
            Text(
              check['findings'] as String? ?? check['description'] as String? ?? '',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
            if (check['inspector'] != null)
              Text(
                'Inspector: ${check['inspector']}',
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              ),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              status,
              style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12),
            ),
            Icon(
              (check['synced'] as int?) == 1 ? Icons.cloud_done : Icons.cloud_upload,
              size: 14,
              color: (check['synced'] as int?) == 1 ? Colors.green : Colors.orange,
            ),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }
}

// ==================== AI Detection & Approval Screen ====================

class DetectionScreen extends ConsumerWidget {
  const DetectionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detectionsAsync = ref.watch(detectionsProvider);
    final pendingApprovalsAsync = ref.watch(pendingApprovalsProvider);

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('AI Detection'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Detections'),
              Tab(text: 'Pending Approvals'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            // Detections Tab
            RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(detectionsProvider);
              },
              child: detectionsAsync.when(
                data: (detections) {
                  if (detections.isEmpty) {
                    return const Center(
                      child: Text('No AI detections yet'),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: detections.length,
                    itemBuilder: (context, index) {
                      final detection = detections[index];
                      return _DetectionCard(detection: detection);
                    },
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => Center(child: Text('Error: $e')),
              ),
            ),
            // Approvals Tab
            RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(pendingApprovalsProvider);
              },
              child: pendingApprovalsAsync.when(
                data: (approvals) {
                  if (approvals.isEmpty) {
                    return const Center(
                      child: Text('No pending approvals'),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: approvals.length,
                    itemBuilder: (context, index) {
                      final approval = approvals[index];
                      return _ApprovalCard(approval: approval, ref: ref);
                    },
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => Center(child: Text('Error: $e')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DetectionCard extends StatelessWidget {
  final Map<String, dynamic> detection;

  const _DetectionCard({required this.detection});

  @override
  Widget build(BuildContext context) {
    final status = detection['status'] as String? ?? 'pending';
    final confidence = (detection['confidence'] as num?)?.toDouble() ?? 0.0;

    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: status == 'completed' ? Colors.green : Colors.orange,
          child: const Icon(Icons.analytics, color: Colors.white),
        ),
        title: Text('Detection ${detection['id']?.toString().substring(0, 8) ?? 'N/A'}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Confidence: ${(confidence * 100).toStringAsFixed(1)}%'),
            Text(
              detection['summary'] as String? ?? '',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
          ],
        ),
        trailing: Text(
          status,
          style: TextStyle(
            color: status == 'completed' ? Colors.green : Colors.orange,
            fontWeight: FontWeight.bold,
            fontSize: 12,
          ),
        ),
        isThreeLine: true,
      ),
    );
  }
}

class _ApprovalCard extends StatelessWidget {
  final Map<String, dynamic> approval;
  final WidgetRef ref;

  const _ApprovalCard({required this.approval, required this.ref});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Detection ID: ${approval['detection_id']?.toString().substring(0, 8) ?? 'N/A'}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text('Approver: ${approval['approver'] ?? 'N/A'}'),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () async {
                    await ref.read(aiDetectionProvider.notifier).rejectDetection(
                      approval['id'] as String,
                      comment: 'Rejected via mobile',
                    );
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Rejected')),
                      );
                    }
                  },
                  child: const Text('Reject', style: TextStyle(color: Colors.red)),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: () async {
                    await ref.read(aiDetectionProvider.notifier).approveDetection(
                      approval['id'] as String,
                      comment: 'Approved via mobile',
                    );
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Approved')),
                      );
                    }
                  },
                  child: const Text('Approve'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
