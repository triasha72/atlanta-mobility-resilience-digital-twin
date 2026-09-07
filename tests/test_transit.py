from amrdt.transit import Connection, Stop, earliest_arrival_seconds


def test_schedule_router_uses_a_transfer_and_walks() -> None:
    stops = {
        "A": Stop("A", 33.7500, -84.3900),
        "B": Stop("B", 33.7500, -84.3800),
        "C": Stop("C", 33.7500, -84.3700),
    }
    arrival = earliest_arrival_seconds(
        stops,
        [Connection("A", "B", 8 * 3600 + 300, 8 * 3600 + 600), Connection("B", "C", 8 * 3600 + 780, 8 * 3600 + 960)],
        origin_lat=33.7500,
        origin_lon=-84.3900,
        destination_lat=33.7500,
        destination_lon=-84.3700,
        departure_seconds=8 * 3600,
        max_walk_meters=100,
    )
    assert arrival == 8 * 3600 + 1080


def test_schedule_router_returns_none_without_nearby_stops() -> None:
    assert earliest_arrival_seconds(
        {"A": Stop("A", 33.75, -84.39)}, [], origin_lat=0, origin_lon=0,
        destination_lat=0, destination_lon=0, departure_seconds=0,
    ) is None
