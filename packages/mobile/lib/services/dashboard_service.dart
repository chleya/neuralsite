import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// Dashboard API Service - handles all dashboard-related API calls
/// Endpoints:
/// - /api/v1/dashboard/progress - Progress reports
/// - /api/v1/dashboard/quality/issue - Quality issues
/// - /api/v1/dashboard/safety - Safety checks
class DashboardService {
  // Change this to your server IP in production
  static const String baseUrl = 'http://localhost:8000';
  
  // Headers
  static Map<String, String> get _headers => {
    'Content-Type': 'application/json',
  };

  // ==================== PROGRESS API ====================
  
  /// Submit progress report to dashboard API
  /// POST /api/v1/dashboard/progress
  static Future<Map<String, dynamic>> submitProgress({
    required String chainage,
    required String status,
    String? note,
    double? latitude,
    double? longitude,
    String? workType,
    double? quantity,
    String? unit,
    String? projectId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/dashboard/progress'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'status': status,
          if (note != null) 'note': note,
          if (latitude != null) 'latitude': latitude,
          if (longitude != null) 'longitude': longitude,
          if (workType != null) 'work_type': workType,
          if (quantity != null) 'quantity': quantity,
          if (unit != null) 'unit': unit,
          if (projectId != null) 'project_id': projectId,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {
          'status': 'error', 
          'message': 'Failed to submit progress: ${response.statusCode}',
          'details': response.body,
        };
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get progress reports from dashboard
  /// GET /api/v1/dashboard/progress
  static Future<Map<String, dynamic>> getProgress({
    String? projectId,
    String? chainage,
    DateTime? fromDate,
    DateTime? toDate,
  }) async {
    try {
      final queryParams = <String>[];
      if (projectId != null) queryParams.add('project_id=$projectId');
      if (chainage != null) queryParams.add('chainage=$chainage');
      if (fromDate != null) queryParams.add('from_date=${fromDate.toIso8601String()}');
      if (toDate != null) queryParams.add('to_date=${toDate.toIso8601String()}');
      
      final queryString = queryParams.isNotEmpty ? '?${queryParams.join('&')}' : '';
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/dashboard/progress$queryString'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to get progress: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Update progress report
  /// PUT /api/v1/dashboard/progress/{id}
  static Future<Map<String, dynamic>> updateProgress({
    required String progressId,
    String? status,
    String? note,
    double? quantity,
    String? unit,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/v1/dashboard/progress/$progressId'),
        headers: _headers,
        body: jsonEncode({
          if (status != null) 'status': status,
          if (note != null) 'note': note,
          if (quantity != null) 'quantity': quantity,
          if (unit != null) 'unit': unit,
        }),
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to update progress: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== QUALITY ISSUE API ====================
  
  /// Submit quality issue to dashboard API
  /// POST /api/v1/dashboard/quality/issue
  static Future<Map<String, dynamic>> submitQualityIssue({
    required String chainage,
    required String description,
    String? severity,
    double? latitude,
    double? longitude,
    String? imagePath,
    String? projectId,
  }) async {
    try {
      // If there's an image, upload it first
      String? imageUrl;
      if (imagePath != null) {
        final imageResult = await _uploadImage(
          localPath: imagePath,
          metadata: {'type': 'quality_issue', 'chainage': chainage},
        );
        if (imageResult['status'] == 'success') {
          imageUrl = imageResult['url'];
        }
      }

      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/dashboard/quality/issue'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'description': description,
          if (severity != null) 'severity': severity,
          if (latitude != null) 'latitude': latitude,
          if (longitude != null) 'longitude': longitude,
          if (imageUrl != null) 'image_url': imageUrl,
          if (projectId != null) 'project_id': projectId,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {
          'status': 'error', 
          'message': 'Failed to submit issue: ${response.statusCode}',
          'details': response.body,
        };
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get quality issues from dashboard
  /// GET /api/v1/dashboard/quality/issue
  static Future<Map<String, dynamic>> getQualityIssues({
    String? projectId,
    String? chainage,
    String? severity,
    String? status,
  }) async {
    try {
      final queryParams = <String>[];
      if (projectId != null) queryParams.add('project_id=$projectId');
      if (chainage != null) queryParams.add('chainage=$chainage');
      if (severity != null) queryParams.add('severity=$severity');
      if (status != null) queryParams.add('status=$status');
      
      final queryString = queryParams.isNotEmpty ? '?${queryParams.join('&')}' : '';
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/dashboard/quality/issue$queryString'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to get issues: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Update quality issue status
  /// PUT /api/v1/dashboard/quality/issue/{id}
  static Future<Map<String, dynamic>> updateQualityIssue({
    required String issueId,
    String? status,
    String? description,
    String? severity,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/v1/dashboard/quality/issue/$issueId'),
        headers: _headers,
        body: jsonEncode({
          if (status != null) 'status': status,
          if (description != null) 'description': description,
          if (severity != null) 'severity': severity,
        }),
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to update issue: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== SAFETY CHECK API ====================
  
  /// Submit safety check to dashboard API
  /// POST /api/v1/dashboard/safety
  static Future<Map<String, dynamic>> submitSafetyCheck({
    required String chainage,
    required String checkType,
    String? description,
    String? findings,
    double? latitude,
    double? longitude,
    String? inspector,
    String? imagePath,
    String? projectId,
  }) async {
    try {
      // If there's an image, upload it first
      String? imageUrl;
      if (imagePath != null) {
        final imageResult = await _uploadImage(
          localPath: imagePath,
          metadata: {'type': 'safety_check', 'chainage': chainage},
        );
        if (imageResult['status'] == 'success') {
          imageUrl = imageResult['url'];
        }
      }

      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/dashboard/safety'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'check_type': checkType,
          if (description != null) 'description': description,
          if (findings != null) 'findings': findings,
          if (latitude != null) 'latitude': latitude,
          if (longitude != null) 'longitude': longitude,
          if (inspector != null) 'inspector': inspector,
          if (imageUrl != null) 'image_url': imageUrl,
          if (projectId != null) 'project_id': projectId,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {
          'status': 'error', 
          'message': 'Failed to submit safety check: ${response.statusCode}',
          'details': response.body,
        };
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get safety checks from dashboard
  /// GET /api/v1/dashboard/safety
  static Future<Map<String, dynamic>> getSafetyChecks({
    String? projectId,
    String? chainage,
    String? checkType,
    String? status,
  }) async {
    try {
      final queryParams = <String>[];
      if (projectId != null) queryParams.add('project_id=$projectId');
      if (chainage != null) queryParams.add('chainage=$chainage');
      if (checkType != null) queryParams.add('check_type=$checkType');
      if (status != null) queryParams.add('status=$status');
      
      final queryString = queryParams.isNotEmpty ? '?${queryParams.join('&')}' : '';
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/dashboard/safety$queryString'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to get safety checks: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Update safety check
  /// PUT /api/v1/dashboard/safety/{id}
  static Future<Map<String, dynamic>> updateSafetyCheck({
    required String checkId,
    String? status,
    String? findings,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/v1/dashboard/safety/$checkId'),
        headers: _headers,
        body: jsonEncode({
          if (status != null) 'status': status,
          if (findings != null) 'findings': findings,
        }),
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to update safety check: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== HELPER METHODS ====================
  
  /// Upload image to server
  static Future<Map<String, dynamic>> _uploadImage({
    required String localPath,
    required Map<String, dynamic> metadata,
  }) async {
    try {
      final file = File(localPath);
      if (!await file.exists()) {
        return {'status': 'error', 'message': 'File not found'};
      }

      final uri = Uri.parse('$baseUrl/api/v1/photos/upload');
      final request = http.MultipartRequest('POST', uri);
      
      request.files.add(await http.MultipartFile.fromPath('photo', localPath));
      request.fields['metadata'] = jsonEncode(metadata);
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          'url': jsonDecode(response.body)['url'] ?? '',
        };
      } else {
        return {'status': 'error', 'message': 'Upload failed: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Test connection to dashboard API
  static Future<bool> testConnection() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/'),
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
