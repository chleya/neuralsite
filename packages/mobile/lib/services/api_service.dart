import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Change this to your server IP in production
  static const String baseUrl = 'http://localhost:8000';
  
  // Headers
  static Map<String, String> get _headers => {
    'Content-Type': 'application/json',
  };

  // Test connection
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

  // ==================== Photo Operations ====================

  /// Upload photo to server
  static Future<Map<String, dynamic>> uploadPhoto({
    required String localPath,
    required Map<String, dynamic> metadata,
  }) async {
    try {
      final file = File(localPath);
      if (!await file.exists()) {
        return {'status': 'error', 'message': 'File not found'};
      }

      // Create multipart request
      final uri = Uri.parse('$baseUrl/api/v1/photos/upload');
      final request = http.MultipartRequest('POST', uri);
      
      // Add file
      request.files.add(await http.MultipartFile.fromPath(
        'photo',
        localPath,
      ));
      
      // Add metadata as JSON
      request.fields['metadata'] = jsonEncode(metadata);
      
      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          'url': jsonDecode(response.body)['url'] ?? '',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Upload failed: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Delete photo from server
  static Future<Map<String, dynamic>> deletePhoto(String photoId) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/api/v1/photos/$photoId'),
        headers: _headers,
      );
      
      if (response.statusCode == 200 || response.statusCode == 204) {
        return {'status': 'success'};
      } else {
        return {'status': 'error', 'message': 'Delete failed: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Issue Operations ====================

  /// Add issue
  static Future<Map<String, dynamic>> addIssue({
    required String chainage,
    required String description,
    String? severity,
    double? latitude,
    double? longitude,
    String? imageUrl,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/issues'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'description': description,
          'severity': severity,
          'latitude': latitude,
          'longitude': longitude,
          'image_url': imageUrl,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to add issue: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get all issues
  static Future<Map<String, dynamic>> getIssues({String? projectId}) async {
    try {
      final queryParams = projectId != null ? '?project_id=$projectId' : '';
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/issues$queryParams'),
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

  /// Update issue status
  static Future<Map<String, dynamic>> updateIssue({
    required String issueId,
    String? status,
    String? description,
    String? severity,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/v1/issues/$issueId'),
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
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to update issue: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Progress Operations ====================

  /// Submit progress report
  static Future<Map<String, dynamic>> submitProgress({
    required String chainage,
    required String status,
    String? note,
    double? latitude,
    double? longitude,
    String? workType,
    double? quantity,
    String? unit,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/progress'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'status': status,
          'note': note,
          'latitude': latitude,
          'longitude': longitude,
          'work_type': workType,
          'quantity': quantity,
          'unit': unit,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to submit progress: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get progress reports
  static Future<Map<String, dynamic>> getProgress({String? projectId, DateTime? from, DateTime? to}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/progress/query'),
        headers: _headers,
        body: jsonEncode({
          if (projectId != null) 'project_id': projectId,
          if (from != null) 'from': from.toIso8601String(),
          if (to != null) 'to': to.toIso8601String(),
        }),
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

  // ==================== Safety Check Operations ====================

  /// Submit safety check
  static Future<Map<String, dynamic>> submitSafetyCheck({
    required String chainage,
    required String checkType,
    String? description,
    String? findings,
    double? latitude,
    double? longitude,
    String? inspector,
    String? imagePath,
  }) async {
    try {
      // If there's an image, upload it first
      String? imageUrl;
      if (imagePath != null) {
        final imageResult = await uploadPhoto(
          localPath: imagePath,
          metadata: {'type': 'safety_check', 'chainage': chainage},
        );
        if (imageResult['status'] == 'success') {
          imageUrl = imageResult['url'];
        }
      }

      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/safety-checks'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'check_type': checkType,
          'description': description,
          'findings': findings,
          'latitude': latitude,
          'longitude': longitude,
          'inspector': inspector,
          'image_url': imageUrl,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to submit safety check: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get safety checks
  static Future<Map<String, dynamic>> getSafetyChecks({String? projectId}) async {
    try {
      final queryParams = projectId != null ? '?project_id=$projectId' : '';
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/safety-checks$queryParams'),
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

  // ==================== AI Detection Operations ====================

  /// Submit photo for AI detection
  static Future<Map<String, dynamic>> submitForDetection({
    required String localPath,
    required String photoId,
    String? detectionType,
    Map<String, dynamic>? options,
  }) async {
    try {
      final file = File(localPath);
      if (!await file.exists()) {
        return {'status': 'error', 'message': 'File not found'};
      }

      final uri = Uri.parse('$baseUrl/api/v1/ai/detect');
      final request = http.MultipartRequest('POST', uri);
      
      // Add file
      request.files.add(await http.MultipartFile.fromPath(
        'image',
        localPath,
      ));
      
      // Add metadata
      request.fields['photo_id'] = photoId;
      if (detectionType != null) {
        request.fields['detection_type'] = detectionType;
      }
      if (options != null) {
        request.fields['options'] = jsonEncode(options);
      }
      
      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Detection failed: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get detection result by ID
  static Future<Map<String, dynamic>> getDetectionResult(String detectionId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/ai/detection/$detectionId'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to get detection: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Query detection results by photo ID
  static Future<Map<String, dynamic>> getDetectionByPhotoId(String photoId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/ai/detection/by-photo/$photoId'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to get detection: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Workflow/Approval Operations ====================

  /// Submit detection for approval workflow
  static Future<Map<String, dynamic>> submitForApproval({
    required String detectionId,
    required String approver,
    String? notes,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/workflow/approval'),
        headers: _headers,
        body: jsonEncode({
          'detection_id': detectionId,
          'approver': approver,
          'notes': notes,
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'status': 'success',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to submit for approval: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Approve or reject detection result
  static Future<Map<String, dynamic>> processApproval({
    required String approvalId,
    required String status,
    String? comment,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/v1/workflow/approval/$approvalId'),
        headers: _headers,
        body: jsonEncode({
          'status': status,
          'comment': comment,
        }),
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          ...jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to process approval: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  /// Get pending approvals
  static Future<Map<String, dynamic>> getPendingApprovals({String? approver}) async {
    try {
      final queryParams = approver != null ? '?approver=$approver' : '';
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/workflow/approvals/pending$queryParams'),
        headers: _headers,
      );
      
      if (response.statusCode == 200) {
        return {
          'status': 'success',
          'data': jsonDecode(response.body),
        };
      } else {
        return {'status': 'error', 'message': 'Failed to get approvals: ${response.statusCode}'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Spatial Operations ====================

  // Spatial: Add point
  static Future<Map<String, dynamic>> addSpatialPoint({
    required int projectId,
    required String chainage,
    required String pointType,
    required double x,
    required double y,
    double z = 0,
    double azimuth = 0,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/spatial/point'),
        headers: _headers,
        body: jsonEncode({
          'project_id': projectId,
          'chainage': chainage,
          'point_type': pointType,
          'x': x,
          'y': y,
          'z': z,
          'azimuth': azimuth,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to add point: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // Spatial: Query nearby
  static Future<Map<String, dynamic>> queryNearby({
    required double x,
    required double y,
    double radius = 100,
    int? projectId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/spatial/nearby'),
        headers: _headers,
        body: jsonEncode({
          'x': x,
          'y': y,
          'radius': radius,
          'project_id': projectId,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to query nearby: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // Spatial: Query by chainage
  static Future<Map<String, dynamic>> queryByChainage({
    required String chainage,
    int? projectId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/spatial/chainage'),
        headers: _headers,
        body: jsonEncode({
          'chainage': chainage,
          'project_id': projectId,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to query by chainage: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Knowledge Graph / Advisor Operations ====================

  // Advisor: Ask question
  static Future<Map<String, dynamic>> askAdvisor(String question) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/advisor/ask'),
        headers: _headers,
        body: jsonEncode({
          'question': question,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get answer: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // Advisor: Search knowledge base
  static Future<Map<String, dynamic>> searchKnowledgeBase({
    required String query,
    String? category,
    int limit = 10,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/advisor/search'),
        headers: _headers,
        body: jsonEncode({
          'query': query,
          if (category != null) 'category': category,
          'limit': limit,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to search: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Workflow Operations ====================

  // Workflow: Run pipeline
  static Future<Map<String, dynamic>> runWorkflow(Map<String, dynamic> routeData) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/workflow/run'),
        headers: _headers,
        body: jsonEncode({
          'route_data': routeData,
          'start': 0,
          'end': 1000,
          'interval': 50,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to run workflow: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // ==================== Calculate Operations ====================

  // Calculate: Get coordinates
  static Future<Map<String, dynamic>> calculateCoordinate({
    required String routeId,
    required double station,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/calculate'),
        headers: _headers,
        body: jsonEncode({
          'route_id': routeId,
          'station': station,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to calculate: ${response.statusCode}');
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }
}
