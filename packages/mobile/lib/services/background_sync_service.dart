import 'dart:convert';
import 'package:workmanager/workmanager.dart';
import 'sync_service.dart';
import 'offline_cache_service.dart';

/// Background sync service using WorkManager
/// Handles periodic sync tasks even when app is in background
class BackgroundSyncService {
  static const String syncTaskName = 'neuralsite_periodic_sync';
  static const String uploadTaskName = 'neuralsite_upload_task';
  
  static final BackgroundSyncService instance = BackgroundSyncService._();
  
  BackgroundSyncService._();

  /// Initialize WorkManager and register tasks
  static Future<void> initialize() async {
    await Workmanager().initialize(
      _callbackDispatcher,
      isInDebugMode: false,
    );
  }

  /// Register periodic sync task
  static Future<void> registerPeriodicSync({
    Duration frequency = const Duration(minutes: 15),
  }) async {
    await Workmanager().registerPeriodicTask(
      syncTaskName,
      syncTaskName,
      frequency: frequency,
      constraints: Constraints(
        networkType: NetworkType.connected,
      ),
      inputData: {
        'task_type': 'sync',
      },
      existingWorkPolicy: ExistingWorkPolicy.replace,
    );
  }

  /// Register immediate sync task (for when coming online)
  static Future<void> registerImmediateSync() async {
    await Workmanager().registerOneOffTask(
      '${syncTaskName}_immediate',
      syncTaskName,
      constraints: Constraints(
        networkType: NetworkType.connected,
      ),
      inputData: {
        'task_type': 'sync_immediate',
      },
    );
  }

  /// Cancel all sync tasks
  static Future<void> cancelAll() async {
    await Workmanager().cancelAll();
  }

  /// Cancel periodic sync only
  static Future<void> cancelPeriodicSync() async {
    await Workmanager().cancelByUniqueName(syncTaskName);
  }
}

/// WorkManager callback dispatcher
@pragma('vm:entry-point')
void _callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    print('Background task started: $task');
    
    try {
      switch (task) {
        case BackgroundSyncService.syncTaskName:
          await _handleSyncTask(inputData);
          break;
        default:
          print('Unknown task: $task');
      }
      
      return true;
    } catch (e) {
      print('Background task error: $e');
      return false;
    }
  });
}

/// Handle sync task
Future<void> _handleSyncTask(Map<String, dynamic>? inputData) async {
  final taskType = inputData?['task_type'] as String?;
  
  switch (taskType) {
    case 'sync':
    case 'sync_immediate':
      // Run sync
      final result = await SyncService.instance.syncNow();
      print('Background sync result: ${result.message}');
      break;
      
    case 'upload':
      // Handle pending uploads
      await _handleUploadTask(inputData);
      break;
      
    case 'preload':
      // Preload offline data
      await _handlePreloadTask(inputData);
      break;
      
    default:
      // Default sync behavior
      final result = await SyncService.instance.syncNow();
      print('Background sync result: ${result.message}');
  }
}

/// Handle upload task
Future<void> _handleUploadTask(Map<String, dynamic>? inputData) async {
  final entityId = inputData?['entity_id'] as String?;
  final filePath = inputData?['file_path'] as String?;
  
  if (entityId != null && filePath != null) {
    print('Uploading: $entityId');
    // Trigger upload through sync service
  }
}

/// Handle preload task
Future<void> _handlePreloadTask(Map<String, dynamic>? inputData) async {
  final projectId = inputData?['project_id'] as String?;
  
  if (projectId != null) {
    print('Preloading data for project: $projectId');
    await OfflineCacheService.instance.preloadProjectData(projectId);
  }
}

/// Constraints for WorkManager tasks
class Constraints {
  final NetworkType networkType;
  final bool requiresBatteryNotLow;
  final bool requiresCharging;
  final bool requiresDeviceIdle;
  final bool requiresStorageNotLow;

  Constraints({
    this.networkType = NetworkType.connected,
    this.requiresBatteryNotLow = false,
    this.requiresCharging = false,
    this.requiresDeviceIdle = false,
    this.requiresStorageNotLow = false,
  });

  Map<String, dynamic> toMap() => {
    'networkType': networkType.index,
    'requiresBatteryNotLow': requiresBatteryNotLow,
    'requiresCharging': requiresCharging,
    'requiresDeviceIdle': requiresDeviceIdle,
    'requiresStorageNotLow': requiresStorageNotLow,
  };
}

/// Network type for constraints
enum NetworkType {
  notRequired,
  connected,
  unmetered,
}
