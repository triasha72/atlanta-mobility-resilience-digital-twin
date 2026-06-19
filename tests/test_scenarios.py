import networkx as nx

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
