import networkx as nx

from amrdt.transit import Connection, Stop, trace_itinerary
from amrdt.walking import (
    load_walk_graph,
    walk_seconds_from_stops_to_point,
    walk_seconds_to_points,
    walk_seconds_to_stops,
)


def test_walk_network_respects_direction_and_edge_length(tmp_path) -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("origin", x=-84.3900, y=33.7500)
    graph.add_node("stop", x=-84.3890, y=33.7500)
    graph.add_edge("origin", "stop", length=240)
    graph.add_edge("stop", "origin", length=240)
    path = tmp_path / "walk.graphml"
    nx.write_graphml(graph, path)
    loaded = load_walk_graph(path)
    stops = {"s": Stop("s", 33.7500, -84.3890)}
    assert walk_seconds_to_stops(
        loaded, lat=33.7500, lon=-84.3900, stops=stops, max_walk_meters=500
    ) == {"s": 180.0}
    assert walk_seconds_from_stops_to_point(
        loaded, stops=stops, lat=33.7500, lon=-84.3900, max_walk_meters=500
    ) == {"s": 180.0}
    assert walk_seconds_to_points(
        loaded,
        lat=33.7500,
        lon=-84.3900,
        points={"destination": (33.7500, -84.3890)},
        max_walk_meters=500,
    ) == {"destination": 180.0}


def test_trace_itinerary_records_access_ride_and_egress() -> None:
    stops = {"a": Stop("a", 0, 0), "b": Stop("b", 0, 0)}
    legs = trace_itinerary(
        stops, [Connection("a", "b", 120, 300, "trip")], origin_lat=0, origin_lon=0,
        destination_lat=0, destination_lon=0, departure_seconds=0,
        initial_walk_seconds={"a": 60}, destination_walk_seconds={"b": 90},
    )
    assert legs is not None
    assert [(leg.kind, leg.from_stop, leg.to_stop) for leg in legs] == [
        ("access_walk", None, "a"), ("ride", "a", "b"), ("egress_walk", "b", None),
    ]


def test_trace_itinerary_records_nearby_stop_transfer_walk() -> None:
    stops = {"a": Stop("a", 0, 0), "b": Stop("b", 0, 0), "c": Stop("c", 0, 0)}
    legs = trace_itinerary(
        stops, [Connection("b", "c", 300, 480, "trip")], origin_lat=0, origin_lon=0,
        destination_lat=0, destination_lon=0, departure_seconds=0,
        initial_walk_seconds={"a": 60}, destination_walk_seconds={"c": 90},
        walking_transfers={"a": [("b", 120)]},
    )
    assert legs is not None
    assert [leg.kind for leg in legs] == ["access_walk", "transfer_walk", "ride", "egress_walk"]
