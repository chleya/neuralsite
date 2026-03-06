"""
Test sync engine module
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from offline.storage import OfflineStorage
from offline.sync import SyncEngine, MockSyncEngine


def test_conflict_resolution():
    """Test conflict resolution strategy"""
    print("\n=== Test Conflict Resolution ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        engine = SyncEngine(storage, "http://mock.api")
        
        # Local data older
        local = {
            "id": "conflict001",
            "name": "Local Data",
            "updated_at": "2026-03-06T08:00:00"
        }
        
        # Remote data newer
        remote = {
            "id": "conflict001",
            "name": "Remote Data",
            "updated_at": "2026-03-06T09:00:00"
        }
        
        result = engine.resolve_conflict(local, remote)
        print(f"Conflict result: {result['name']}")
        assert result["name"] == "Remote Data"
        
        # Local data newer
        local_new = {
            "id": "conflict002",
            "name": "Local New Data",
            "updated_at": "2026-03-06T10:00:00"
        }
        
        remote_old = {
            "id": "conflict002",
            "name": "Remote Old Data",
            "updated_at": "2026-03-06T09:00:00"
        }
        
        result2 = engine.resolve_conflict(local_new, remote_old)
        print(f"Conflict result2: {result2['name']}")
        assert result2["name"] == "Local New Data"
        
        print("[PASS] Conflict resolution test passed")
        
    finally:
        os.unlink(db_path)


def test_mock_sync_engine():
    """Test Mock sync engine"""
    print("\n=== Test Mock Sync Engine ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        mock_engine = MockSyncEngine(storage, "http://mock.api")
        
        # Save local data
        test_data = {
            "id": "mock001",
            "name": "Mock Test",
            "value": 42
        }
        storage.save("test_table", test_data)
        
        # Check pending
        pending = storage.get_pending("test_table")
        print(f"Pending: {len(pending)}")
        assert len(pending) == 1
        
        print("[PASS] Mock sync engine test passed")
        
    finally:
        os.unlink(db_path)


def test_sync_status_tracking():
    """Test sync status tracking"""
    print("\n=== Test Sync Status Tracking ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        # Add 5 records (all pending initially)
        for i in range(5):
            storage.save("issues", {
                "id": f"issue{i:03d}",
                "title": f"Issue {i}"
            })
        
        # Mark some as synced
        storage.mark_synced("issues", "issue000")
        storage.mark_synced("issues", "issue001")
        storage.mark_synced("issues", "issue002")
        storage.mark_synced("issues", "issue003")
        
        status = storage.get_sync_status("issues")
        print(f"Status: {status}")
        
        assert status["total"] == 5
        assert status["synced"] == 4
        assert status["pending"] == 1
        
        print("[PASS] Sync status tracking test passed")
        
    finally:
        os.unlink(db_path)


def test_last_sync_time():
    """Test last sync time"""
    print("\n=== Test Last Sync Time ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        engine = SyncEngine(storage, "http://api.test")
        
        # Initial no time
        time1 = engine.get_last_sync_time("issues")
        print(f"Initial last sync time: {time1}")
        assert time1 is None
        
        # Set time
        engine.set_last_sync_time("issues", "2026-03-06T10:00:00")
        
        # Get time
        time2 = engine.get_last_sync_time("issues")
        print(f"After set last sync time: {time2}")
        assert time2 == "2026-03-06T10:00:00"
        
        print("[PASS] Last sync time test passed")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Starting Sync Engine Tests")
    print("=" * 50)
    
    tests = [
        test_conflict_resolution,
        test_mock_sync_engine,
        test_sync_status_tracking,
        test_last_sync_time,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests complete: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
