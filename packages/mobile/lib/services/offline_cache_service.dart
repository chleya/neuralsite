import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../db/database_helper.dart';
import 'api_service.dart';

/// Offline cache service for preloading drawings and specifications
/// Enables construction site workers to access data without internet
class OfflineCacheService {
  static final OfflineCacheService instance = OfflineCacheService._();
  
  final DatabaseHelper _db = DatabaseHelper.instance;
  final Connectivity _connectivity = Connectivity();
  
  // Cache expiration time (7 days)
  static const Duration cacheExpiration = Duration(days: 7);
  
  // Max cache size (500MB)
  static const int maxCacheSizeBytes = 500 * 1024 * 1024;

  OfflineCacheService._();

  /// Check if device is online
  Future<bool> get isOnline async {
    final results = await _connectivity.checkConnectivity();
    return results.isNotEmpty && results.first != ConnectivityResult.none;
  }

  // ==================== DRAWING CACHE ====================
  
  /// Preload all drawings for a project
  Future<void> preloadDrawings(String projectId) async {
    if (!await isOnline) {
      print('Offline, skipping drawings preload');
      return;
    }

    try {
      print('Preloading drawings for project: $projectId');
      
      final result = await ApiService.downloadDrawings(projectId: projectId);
      
      if (result['status'] == 'success' && result['drawings'] != null) {
        final drawings = result['drawings'] as List<dynamic>;
        
        for (final drawing in drawings) {
          await _cacheDrawing(projectId, drawing as Map<String, dynamic>);
        }
        
        print('Cached ${drawings.length} drawings');
      }
    } catch (e) {
      print('Error preloading drawings: $e');
    }
  }

  /// Cache a single drawing
  Future<void> _cacheDrawing(String projectId, Map<String, dynamic> drawing) async {
    // Get app documents directory
    final appDir = await getApplicationDocumentsDirectory();
    final drawingsDir = Directory('${appDir.path}/drawings/$projectId');
    
    if (!await drawingsDir.exists()) {
      await drawingsDir.create(recursive: true);
    }

    // Download the file
    final fileUrl = drawing['file_url'] as String?;
    if (fileUrl == null) return;

    final fileName = fileUrl.split('/').last;
    final localPath = '${drawingsDir.path}/$fileName';

    // Download if not already cached
    final file = File(localPath);
    if (!await file.exists()) {
      try {
        // Simple download - in production use Dio for progress
        final response = await _downloadFile(fileUrl, localPath);
        if (!response) {
          print('Failed to download drawing: $fileName');
          return;
        }
      } catch (e) {
        print('Error downloading drawing: $e');
        return;
      }
    }

    // Get file size
    final fileSize = await file.length();

    // Save to database
    final cachedDrawing = {
      'id': drawing['id'],
      'project_id': projectId,
      'name': drawing['name'],
      'file_path': localPath,
      'file_type': drawing['file_type'] ?? 'pdf',
      'file_size': fileSize,
      'version': drawing['version'] ?? 1,
      'downloaded_at': DateTime.now().toIso8601String(),
      'expires_at': DateTime.now().add(cacheExpiration).toIso8601String(),
      'created_at': DateTime.now().toIso8601String(),
    };

    await _db.cacheDrawing(cachedDrawing);
  }

  /// Get cached drawings for a project
  Future<List<Map<String, dynamic>>> getCachedDrawings(String projectId) async {
    return await _db.getCachedDrawings(projectId);
  }

  /// Get a specific cached drawing
  Future<String?> getCachedDrawingPath(String drawingId) async {
    final drawings = await _db.getCachedDrawings('');
    final drawing = drawings.where((d) => d['id'] == drawingId).firstOrNull;
    
    if (drawing != null) {
      final path = drawing['file_path'] as String?;
      if (path != null) {
        final file = File(path);
        if (await file.exists()) {
          return path;
        }
      }
    }
    return null;
  }

  // ==================== SPECIFICATION CACHE ====================
  
  /// Preload specifications for a project
  Future<void> preloadSpecifications(String projectId, {String? category}) async {
    if (!await isOnline) {
      print('Offline, skipping specifications preload');
      return;
    }

    try {
      print('Preloading specifications for project: $projectId');
      
      final result = await ApiService.downloadSpecifications(
        projectId: projectId,
        category: category,
      );
      
      if (result['status'] == 'success' && result['specifications'] != null) {
        final specifications = result['specifications'] as List<dynamic>;
        
        for (final spec in specifications) {
          await _cacheSpecification(projectId, spec as Map<String, dynamic>);
        }
        
        print('Cached ${specifications.length} specifications');
      }
    } catch (e) {
      print('Error preloading specifications: $e');
    }
  }

  /// Cache a single specification
  Future<void> _cacheSpecification(String projectId, Map<String, dynamic> spec) async {
    final cachedSpec = {
      'id': spec['id'],
      'project_id': projectId,
      'title': spec['title'],
      'content': spec['content'],
      'category': spec['category'],
      'version': spec['version'] ?? 1,
      'downloaded_at': DateTime.now().toIso8601String(),
      'expires_at': DateTime.now().add(cacheExpiration).toIso8601String(),
      'created_at': DateTime.now().toIso8601String(),
    };

    await _db.cacheSpecification(cachedSpec);
  }

  /// Get cached specifications for a project
  Future<List<Map<String, dynamic>>> getCachedSpecifications(String projectId, {String? category}) async {
    return await _db.getCachedSpecifications(projectId, category: category);
  }

  /// Search cached specifications by keyword
  Future<List<Map<String, dynamic>>> searchSpecifications(String projectId, String query) async {
    final specs = await _db.getCachedSpecifications(projectId);
    final lowercaseQuery = query.toLowerCase();
    
    return specs.where((spec) {
      final title = (spec['title'] as String?)?.toLowerCase() ?? '';
      final content = (spec['content'] as String?)?.toLowerCase() ?? '';
      final category = (spec['category'] as String?)?.toLowerCase() ?? '';
      
      return title.contains(lowercaseQuery) || 
             content.contains(lowercaseQuery) || 
             category.contains(lowercaseQuery);
    }).toList();
  }

  // ==================== BATCH OPERATIONS ====================
  
  /// Preload all offline data for a project
  /// Called when user selects a project for offline work
  Future<void> preloadProjectData(String projectId) async {
    print('Starting full preload for project: $projectId');
    
    // Parallel preload
    await Future.wait([
      preloadDrawings(projectId),
      preloadSpecifications(projectId),
      // Could add more: spatial points, issues, etc.
    ]);
    
    // Clean up expired cache
    await _db.clearExpiredCache();
    
    print('Preload complete for project: $projectId');
  }

  /// Clear all cached data for a project
  Future<void> clearProjectCache(String projectId) async {
    // Delete cached files
    final appDir = await getApplicationDocumentsDirectory();
    final drawingsDir = Directory('${appDir.path}/drawings/$projectId');
    
    if (await drawingsDir.exists()) {
      await drawingsDir.delete(recursive: true);
    }
    
    // Database cleanup is handled by clearExpiredCache
  }

  /// Get cache size for a project
  Future<int> getCacheSize(String projectId) async {
    int totalSize = 0;
    
    final drawings = await _db.getCachedDrawings(projectId);
    for (final drawing in drawings) {
      final path = drawing['file_path'] as String?;
      if (path != null) {
        final file = File(path);
        if (await file.exists()) {
          totalSize += await file.length();
        }
      }
    }
    
    return totalSize;
  }

  /// Check if cache is getting too large and clean up if needed
  Future<void> ensureCacheSizeLimit() async {
    // This is a simplified implementation
    // In production, you'd track total cache size across all projects
    
    // Clear expired cache
    await _db.clearExpiredCache();
  }

  // ==================== UTILITY ====================
  
  /// Download a file from URL to local path
  Future<bool> _downloadFile(String url, String localPath) async {
    try {
      final client = HttpClient();
      final request = await client.getUrl(Uri.parse(url));
      final response = await request.close();
      
      final file = File(localPath);
      final sink = file.openWrite();
      
      await for (final chunk in response) {
        sink.add(chunk);
      }
      
      await sink.close();
      await client.close();
      
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Get cache info
  Future<Map<String, dynamic>> getCacheInfo(String projectId) async {
    final drawings = await _db.getCachedDrawings(projectId);
    final specs = await _db.getCachedSpecifications(projectId);
    final cacheSize = await getCacheSize(projectId);
    
    return {
      'project_id': projectId,
      'drawings_count': drawings.length,
      'specifications_count': specs.length,
      'cache_size_bytes': cacheSize,
      'cache_size_mb': (cacheSize / (1024 * 1024)).toStringAsFixed(2),
    };
  }
}
