import networkx as nx
import pytest

from amrdt.ml import edge_learning_frame


def test_edge_learning_frame_requires_official_label_and_keeps_spatial_groups() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("a", x=-84.4, y=33.7)
    graph.add_node("b", x=-84.39, y=33.71)
    graph.add_edge("a", "b", length=100, travel_time=10, speed_kph=30, flood_exposed=True, observed_closed=True)
    result = edge_learning_frame(graph)
    assert result.loc[0, "observed_closed"] == 1
    assert result.loc[0, "flood_exposed"] == 1
    assert result.loc[0, "spatial_block"]


def test_edge_learning_frame_rejects_missing_labels() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("a", x=0, y=0)
    graph.add_node("b", x=1, y=1)
    graph.add_edge("a", "b")
    with pytest.raises(ValueError, match="observed_closed"):
        edge_learning_frame(graph)
