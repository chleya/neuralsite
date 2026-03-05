import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as path;
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';

/// Camera service for photo capture
class CameraService {
  static final CameraService instance = CameraService._();
  
  final ImagePicker _picker = ImagePicker();
  final Uuid _uuid = const Uuid();
  
  CameraService._();

  /// Take a photo with the camera
  Future<CapturedPhoto?> takePhoto({
    ImageSource source = ImageSource.camera,
    int maxWidth = 1920,
    int maxHeight = 1080,
    int imageQuality = 85,
  }) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        maxWidth: maxWidth.toDouble(),
        maxHeight: maxHeight.toDouble(),
        imageQuality: imageQuality,
        preferredCameraDevice: CameraDevice.rear,
      );

      if (image == null) return null;

      // Save to app documents directory for persistence
      final savedPath = await _saveToDocuments(image);
      
      return CapturedPhoto(
        path: savedPath,
        originalPath: image.path,
        capturedAt: DateTime.now(),
      );
    } catch (e) {
      print('Error taking photo: $e');
      return null;
    }
  }

  /// Pick a photo from gallery
  Future<CapturedPhoto?> pickFromGallery({
    int maxWidth = 1920,
    int maxHeight = 1080,
    int imageQuality = 85,
  }) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: maxWidth.toDouble(),
        maxHeight: maxHeight.toDouble(),
        imageQuality: imageQuality,
      );

      if (image == null) return null;

      final savedPath = await _saveToDocuments(image);
      
      return CapturedPhoto(
        path: savedPath,
        originalPath: image.path,
        capturedAt: DateTime.now(),
      );
    } catch (e) {
      print('Error picking photo: $e');
      return null;
    }
  }

  /// Pick multiple photos from gallery
  Future<List<CapturedPhoto>> pickMultipleFromGallery({
    int maxWidth = 1920,
    int maxHeight = 1080,
    int imageQuality = 85,
    int maxImages = 10,
  }) async {
    try {
      final List<XFile> images = await _picker.pickMultiImage(
        maxWidth: maxWidth.toDouble(),
        maxHeight: maxHeight.toDouble(),
        imageQuality: imageQuality,
        limit: maxImages,
      );

      final List<CapturedPhoto> photos = [];
      for (final image in images) {
        final savedPath = await _saveToDocuments(image);
        photos.add(CapturedPhoto(
          path: savedPath,
          originalPath: image.path,
          capturedAt: DateTime.now(),
        ));
      }
      
      return photos;
    } catch (e) {
      print('Error picking photos: $e');
      return [];
    }
  }

  /// Generate unique filename
  String _generateFilename() {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final uuid = _uuid.v4().substring(0, 8);
    return 'photo_${timestamp}_$uuid.jpg';
  }

  /// Save image to app documents directory
  Future<String> _saveToDocuments(XFile image) async {
    // Get documents directory
    final documentsDir = await _getPhotosDirectory();
    
    // Generate unique filename
    final filename = _generateFilename();
    final newPath = path.join(documentsDir.path, filename);
    
    // Copy file to documents directory
    final File newFile = await File(image.path).copy(newPath);
    
    return newFile.path;
  }

  /// Get photos directory, create if not exists
  Future<Directory> _getPhotosDirectory() async {
    final appDir = await getApplicationDocumentsDirectory();
    final photosDir = Directory(path.join(appDir.path, 'photos'));
    
    if (!await photosDir.exists()) {
      await photosDir.create(recursive: true);
    }
    
    return photosDir;
  }

  /// Delete a photo
  Future<bool> deletePhoto(String photoPath) async {
    try {
      final file = File(photoPath);
      if (await file.exists()) {
        await file.delete();
        return true;
      }
      return false;
    } catch (e) {
      print('Error deleting photo: $e');
      return false;
    }
  }

  /// Check if photo exists
  Future<bool> photoExists(String photoPath) async {
    final file = File(photoPath);
    return await file.exists();
  }

  /// Get file size in bytes
  Future<int> getFileSize(String photoPath) async {
    final file = File(photoPath);
    if (await file.exists()) {
      return await file.length();
    }
    return 0;
  }

  /// Get all photos in documents directory
  Future<List<String>> getAllLocalPhotos() async {
    try {
      final photosDir = await _getPhotosDirectory();
      final files = await photosDir.list().toList();
      
      return files
          .whereType<File>()
          .where((f) => f.path.endsWith('.jpg') || f.path.endsWith('.png'))
          .map((f) => f.path)
          .toList();
    } catch (e) {
      print('Error listing photos: $e');
      return [];
    }
  }

  /// Clean up old photos (older than specified days)
  Future<int> cleanupOldPhotos({int olderThanDays = 30}) async {
    try {
      final photosDir = await _getPhotosDirectory();
      final files = await photosDir.list().toList();
      final cutoff = DateTime.now().subtract(Duration(days: olderThanDays));
      
      int deleted = 0;
      for (final entity in files) {
        if (entity is File) {
          final stat = await entity.stat();
          if (stat.modified.isBefore(cutoff)) {
            await entity.delete();
            deleted++;
          }
        }
      }
      
      return deleted;
    } catch (e) {
      print('Error cleaning up photos: $e');
      return 0;
    }
  }
}

/// Captured photo data
class CapturedPhoto {
  final String path;
  final String originalPath;
  final DateTime capturedAt;

  CapturedPhoto({
    required this.path,
    required this.originalPath,
    required this.capturedAt,
  });

  /// Get filename
  String get filename => path.split('/').last;

  @override
  String toString() => 'CapturedPhoto(path: $path, capturedAt: $capturedAt)';
}
