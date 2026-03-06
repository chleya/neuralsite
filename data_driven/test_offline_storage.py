"""
Test offline storage module
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from offline.storage import OfflineStorage


def test_save_and_get():
    """Test save and get data"""
    print("\n=== Test Save and Get ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        test_data = {
            "id": "test001",
            "name": "Test Data",
            "value": 123,
            "updated_at": "2026-03-06T09:00:00"
        }
        
        result = storage.save("users", test_data)
        print(f"Save result: {result}")
        
        records = storage.get("users", {"id": "test001"})
        print(f"Get records: {len(records)}")
        
        if records:
            data = json.loads(records[0]["data"])
            print(f"Data: {data}")
            assert data["name"] == "Test Data"
            print("[PASS] Save and Get test passed")
        
    finally:
        os.unlink(db_path)


def test_update():
    """Test update data"""
    print("\n=== Test Update ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        original = {
            "id": "test002",
            "name": "Original Name",
            "value": 100
        }
        storage.save("items", original)
        
        updated = {
            "id": "test002", 
            "name": "New Name",
            "value": 200,
            "updated_at": "2026-03-06T10:00:00"
        }
        storage.save("items", updated)
        
        records = storage.get("items", {"id": "test002"})
        data = json.loads(records[0]["data"])
        
        print(f"Updated name: {data['name']}")
        assert data["name"] == "New Name"
        print("[PASS] Update test passed")
        
    finally:
        os.unlink(db_path)


def test_delete():
    """Test delete data"""
    print("\n=== Test Delete ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        storage.save("items", {"id": "test003", "name": "To Delete"})
        
        result = storage.delete("items", "test003")
        print(f"Delete result: {result}")
        
        records = storage.get("items", {"id": "test003"})
        print(f"Records after delete: {len(records)}")
        assert len(records) == 0
        print("[PASS] Delete test passed")
        
    finally:
        os.unlink(db_path)


def test_pending_and_mark_synced():
    """Test pending and mark synced"""
    print("\n=== Test Pending and Mark Synced ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        for i in range(3):
            storage.save("tasks", {
                "id": f"task{i:03d}",
                "name": f"Task {i}",
                "synced": False
            })
        
        pending = storage.get_pending("tasks")
        print(f"Pending count: {len(pending)}")
        assert len(pending) == 3
        
        storage.mark_synced("tasks", "task001")
        
        pending = storage.get_pending("tasks")
        print(f"After mark: {len(pending)}")
        assert len(pending) == 2
        
        print("[PASS] Pending test passed")
        
    finally:
        os.unlink(db_path)


def test_sync_status():
    """Test sync status"""
    print("\n=== Test Sync Status ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        storage.save("table1", {"id": "1", "data": "a"})
        storage.save("table1", {"id": "2", "data": "b"})
        storage.mark_synced("table1", "1")
        
        storage.save("table2", {"id": "3", "data": "c"})
        
        status = storage.get_sync_status()
        print(f"Sync status: {json.dumps(status, indent=2)}")
        
        table1_status = storage.get_sync_status("table1")
        print(f"table1 status: {table1_status}")
        
        assert table1_status["total"] == 2
        assert table1_status["synced"] == 1
        assert table1_status["pending"] == 1
        
        print("[PASS] Sync status test passed")
        
    finally:
        os.unlink(db_path)


def test_batch_mark_synced():
    """Test batch mark synced"""
    print("\n=== Test Batch Mark Synced ===")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        storage = OfflineStorage(db_path)
        
        ids = ["b1", "b2", "b3", "b4", "b5"]
        for id in ids:
            storage.save("batch", {"id": id, "data": f"data_{id}"})
        
        count = storage.mark_synced_batch("batch", ["b1", "b2", "b3"])
        print(f"Batch mark count: {count}")
        
        pending = storage.get_pending("batch")
        print(f"Remaining pending: {len(pending)}")
        
        assert count == 3
        assert len(pending) == 2
        
        print("[PASS] Batch mark test passed")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Starting Offline Storage Tests")
    print("=" * 50)
    
    tests = [
        test_save_and_get,
        test_update,
        test_delete,
        test_pending_and_mark_synced,
        test_sync_status,
        test_batch_mark_synced,
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
