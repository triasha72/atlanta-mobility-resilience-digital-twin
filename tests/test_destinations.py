from amrdt.destinations import destination_summary, parse_overpass_destinations


def test_parse_overpass_destinations_keeps_supported_routable_facilities():
    payload = {"elements": [
        {"type": "node", "id": 1, "lat": 33.7, "lon": -84.3,
         "tags": {"amenity": "hospital", "name": "Hospital A"}},
        {"type": "way", "id": 2, "center": {"lat": 33.8, "lon": -84.4},
         "tags": {"amenity": "fire_station", "name": "Station 2"}},
        {"type": "node", "id": 3, "lat": 33.9, "lon": -84.5,
         "tags": {"amenity": "restaurant"}},
    ]}
    frame = parse_overpass_destinations(payload)
    assert frame["category"].tolist() == ["fire_station", "hospital"]
    assert frame["opportunity_weight"].tolist() == [1.0, 1.0]
    assert destination_summary(frame)["destination_count"] == 2
