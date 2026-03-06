# NeuralSite Mobile

Flutter mobile app for construction management with offline-first capability.

## Features

- 📍 **Location Tracking** - GPS-based chainage mapping
- 📷 **Photo Capture** - Camera + GPS auto-tagging, offline caching
- 🔄 **Offline-First** - SQLite local storage, auto-sync when online
- 🧠 **AI Advisor** - Connect to NeuralSite Core knowledge graph
- 📊 **Progress Tracking** - Daily construction progress reports
- ✅ **Conflict Resolution** - Handle sync conflicts gracefully
- 🚨 **Issue Reporting** - Report construction issues with severity levels
- 🛡️ **Safety Checks** - Record safety inspections and audits
- 🤖 **AI Detection** - Submit photos for AI-powered analysis
- ✅ **Approval Workflow** - Review and approve AI detection results
- 📍 **Spatial Queries** - Query spatial data by location or chainage

## Architecture

```
lib/
├── main.dart                    # App entry with Riverpod
├── models/
│   ├── models.dart              # Barrel file
│   ├── photo.dart               # Photo model with sync status
│   ├── project.dart             # Project model
│   ├── issue.dart               # Issue model with severity tracking
│   ├── progress.dart            # Progress report model
│   ├── safety_check.dart       # Safety check/inspection model
│   ├── ai_detection.dart       # AI detection results model
│   └── sync_queue.dart          # Sync queue for offline operations
├── db/
│   ├── database_helper.dart     # SQLite operations
│   └── db.dart                  # Barrel file
├── services/
│   ├── api_service.dart        # REST API client (enhanced)
│   ├── sync_service.dart       # Offline-first sync engine
│   ├── location_service.dart   # GPS location service
│   ├── camera_service.dart      # Camera/photo service
│   └── services.dart            # Barrel file
└── providers/
    └── providers.dart            # Riverpod providers
```

## Mobile App Screens

1. **Dashboard** - Overview of projects, photos, sync status
2. **Issues** - Report and view construction issues
3. **Progress** - Track daily construction progress
4. **Safety** - Record safety inspections
5. **Capture** - Take photos with GPS tagging
6. **Advisor** - Ask questions to knowledge base
7. **Settings** - Configure API server, sync, offline mode

## Offline-First Architecture

### Data Flow
1. **Capture**: User takes photo with GPS
2. **Local Save**: Data saved to SQLite immediately
3. **Queue**: Item added to sync queue with status `pending`
4. **Auto-Sync**: When online, queue processor uploads pending items
5. **Status Update**: Photo status updated to `synced` on success

### Sync States
- `pending`: Waiting to sync
- `uploading`: Currently uploading
- `synced`: Successfully synced
- `conflict`: Conflict detected (requires manual resolution)
- `failed`: Upload failed (will retry)

### Conflict Handling
- Server returns conflict if data was modified
- Conflict resolution options: keep local, keep remote, merge, or manual

## Setup

```bash
# Install dependencies
flutter pub get

# Run
flutter run

# Test
flutter test
```

## API Endpoints

The app connects to NeuralSite Core API:

### Photo Operations
- `POST /api/v1/photos/upload` - Upload photo with metadata
- `DELETE /api/v1/photos/:id` - Delete photo

### Issue Operations
- `POST /api/v1/issues` - Add issue report
- `GET /api/v1/issues` - Get all issues
- `PUT /api/v1/issues/:id` - Update issue status

### Progress Operations
- `POST /api/v1/progress` - Submit progress report
- `POST /api/v1/progress/query` - Query progress reports

### Safety Operations
- `POST /api/v1/safety-checks` - Submit safety check
- `GET /api/v1/safety-checks` - Get safety checks

### AI Detection
- `POST /api/v1/ai/detect` - Submit photo for AI detection
- `GET /api/v1/ai/detection/:id` - Get detection result
- `GET /api/v1/ai/detection/by-photo/:photoId` - Get detection by photo

### Workflow/Approval
- `POST /api/v1/workflow/approval` - Submit for approval
- `PUT /api/v1/workflow/approval/:id` - Process approval
- `GET /api/v1/workflow/approvals/pending` - Get pending approvals

### Spatial Operations
- `POST /api/v1/spatial/point` - Add spatial point
- `POST /api/v1/spatial/nearby` - Query nearby points
- `POST /api/v1/spatial/chainage` - Query by chainage

### Knowledge Base
- `POST /api/v1/advisor/ask` - Ask advisor question
- `POST /api/v1/advisor/search` - Search knowledge base

### Workflow
- `POST /api/v1/workflow/run` - Run workflow pipeline
- `POST /api/v1/calculate` - Calculate coordinates

## Dependencies

- `flutter_riverpod` - State management
- `sqflite` - Local SQLite database
- `http` - REST API calls
- `geolocator` - GPS location
- `image_picker` - Camera/photos
- `path_provider` - File system paths
- `connectivity_plus` - Network status
- `uuid` - Unique ID generation

## Version

1.1.0
