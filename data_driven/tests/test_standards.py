from data_driven.standards import StationFormat

def test_station_parse():
    assert StationFormat.parse("K5+800") == 5800.0

def test_station_format():
    assert StationFormat.format(5800.0) == "K5+800"
