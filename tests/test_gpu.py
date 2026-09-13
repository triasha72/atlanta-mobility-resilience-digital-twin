import networkx as nx
import pytest

from amrdt.gpu import coalesced_edge_table


def test_coalesced_edge_table_preserves_least_parallel_cost() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, travel_time=12.0)
    graph.add_edge(1, 2, travel_time=4.0)
    graph.add_edge(2, 1, travel_time=6.0)

    result = coalesced_edge_table(graph)

    assert result.to_dict("records") == [
        {"source": 1, "target": 2, "weight": 4.0},
        {"source": 2, "target": 1, "weight": 6.0},
    ]


def test_coalesced_edge_table_rejects_invalid_weights() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, travel_time=-1)

    with pytest.raises(ValueError, match="non-negative"):
        coalesced_edge_table(graph)
