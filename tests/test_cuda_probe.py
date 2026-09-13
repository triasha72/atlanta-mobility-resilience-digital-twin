from scripts.probe_cuda_runtime import optional_torch_details


def test_cuda_probe_always_reports_boolean_availability() -> None:
    result = optional_torch_details()
    assert isinstance(result["torch_available"], bool)
    assert isinstance(result["torch_cuda_available"], bool)
