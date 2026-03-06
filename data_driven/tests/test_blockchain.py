from data_driven.blockchain import HashComputer

def test_hash_computation():
    data = {"test": "value"}
    hash1 = HashComputer.compute_data_hash(data, "test")
    hash2 = HashComputer.compute_data_hash(data, "test")
    assert hash1 == hash2
