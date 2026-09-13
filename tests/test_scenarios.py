import networkx as nx
from shapely.geometry import LineString, Polygon

from amrdt.hazards import annotate_exposed_edges
from amrdt.scenarios import apply_scenario


def make_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, key=0, travel_time=1.0)
    graph.add_edge(2, 1, key=0, travel_time=1.0)
    graph.add_edge(2, 3, key=0, travel_time=1.0)
    graph.add_edge(3, 2, key=0, travel_time=1.0)
    return graph


def test_random_edge_scenario_removes_requested_edges() -> None:
    graph = make_graph()
    result = apply_scenario(
        graph,
        {"name": "random", "type": "random_edges", "n_edges": 1},
        random_seed=7,
    )
    assert len(result.removed_edges) == 1
    assert result.graph.number_of_edges() == graph.number_of_edges() - 1


def test_baseline_does_not_change_graph() -> None:
    graph = make_graph()
    result = apply_scenario(graph, {"name": "baseline", "type": "baseline"})
    assert result.graph.number_of_edges() == graph.number_of_edges()
    assert result.removed_edges == []


def test_sampled_betweenness_scenario_is_reproducible() -> None:
    graph = make_graph()
    scenario = {
        "name": "centrality",
        "type": "high_betweenness_edges",
        "n_edges": 1,
        "betweenness_sample_nodes": 2,
    }
    assert apply_scenario(graph, scenario, random_seed=8).removed_edges == apply_scenario(
        graph, scenario, random_seed=8
    ).removed_edges


def test_flood_scenario_removes_only_annotated_edges() -> None:
    graph = make_graph()
    graph[1][2][0]["flood_exposed"] = True
    result = apply_scenario(graph, {"name": "flood", "type": "flood_exposed_edges"})
    assert result.removed_edges == [(1, 2, 0)]


def test_hazard_annotation_uses_edge_geometry() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("a", x=0, y=0)
    graph.add_node("b", x=2, y=0)
    graph.add_edge("a", "b", key=0, geometry=LineString([(0, 0), (2, 0)]))
    graph.add_edge("b", "a", key=0, geometry=LineString([(2, 1), (0, 1)]))
    annotated = annotate_exposed_edges(graph, [Polygon([(0.5, -0.5), (1.5, -0.5), (1.5, 0.5), (0.5, 0.5)])])
    assert annotated["a"]["b"][0]["flood_exposed"] is True
    assert annotated["b"]["a"][0]["flood_exposed"] is False
