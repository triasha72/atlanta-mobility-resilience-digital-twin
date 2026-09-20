from scripts.audit_event_label_coverage import classification_readiness


def test_label_coverage_requires_explicit_positive_and_negative_records() -> None:
    positives_only = [{"properties": {"Closed": "yes"}}]
    assert not classification_readiness(positives_only, label_field="Closed")[
        "eligible_for_supervised_classification"
    ]
    paired = positives_only + [{"properties": {"Closed": "no"}}]
    result = classification_readiness(paired, label_field="Closed")
    assert result["eligible_for_supervised_classification"]
    assert result["positive_count"] == 1
    assert result["negative_count"] == 1
