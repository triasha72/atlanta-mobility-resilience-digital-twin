import json

from amrdt.provenance import sha256_file, write_run_manifest


def test_run_manifest_hashes_graph_config_and_outputs(tmp_path):
    graph = tmp_path / "network.graphml"
    graph.write_text("public graph fixture")
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "scenario_summary.csv").write_text("scenario,reachable\nbaseline,1.0\n")

    manifest = write_run_manifest({"study_area": {"name": "Atlanta"}}, graph, outputs)
    payload = json.loads(manifest.read_text())

    assert payload["network_source"] == "OpenStreetMap via OSMnx"
    assert payload["network_license"] == "ODbL-1.0"
    assert payload["graph"]["sha256"] == sha256_file(graph)
    assert payload["outputs"][0]["path"] == "scenario_summary.csv"
    assert "not observed traffic" in payload["interpretation"]
