# NeuralSite Mobile

Flutter mobile app for construction management with offline-first capability.

## Features

- 📍 **Location Tracking** - GPS-based chainage mapping
- 📷 **Issue Reporting** - Photo + text + GPS
- 🔄 **Offline-First** - SQLite local storage, auto-sync
- 🧠 **AI Advisor** - Connect to NeuralSite Core knowledge graph
- 📊 **Progress Tracking** - Daily construction progress

## Architecture

```
lib/
├── main.dart              # App entry
├── db/
│   └── database_helper.dart  # SQLite operations
├── services/
│   ├── api_service.dart      # REST API client
│   └── sync_service.dart    # Offline sync engine
└── models/
    └── ...
```

## Setup

```bash
# Install dependencies
flutter pub get

# Run
flutter run
```

## API Endpoints

The app connects to NeuralSite Core API:

- `POST /api/v1/spatial/point` - Add spatial point
- `POST /api/v1/spatial/nearby` - Query nearby points
- `POST /api/v1/advisor/ask` - Ask advisor
- `POST /api/v1/workflow/run` - Run workflow

## Offline Sync

1. User captures issue (photo + description)
2. Data saved to local SQLite
3. When online, SyncService auto-uploads
4. Conflicts resolved on server

## Dependencies

- `sqflite` - Local SQLite database
- `http` - REST API calls
- `geolocator` - GPS location
- `image_picker` - Camera/photos
- `provider` - State management

## Version

1.0.0
