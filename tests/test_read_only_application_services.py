from types import SimpleNamespace
from unittest.mock import patch

from backend.app.application.evidence import EvidenceApplicationService
from backend.app.application.map_view import MapViewApplicationService
from backend.app.application.summary import SummaryApplicationService


def test_summary_service_composes_runtime_metrics_from_suppliers():
    region = SimpleNamespace(
        code="320400",
        name="常州市",
        status="ready",
        version="region-pack-v1",
        manifest={"districts": ["天宁区", "钟楼区"]},
        datasets={
            "hospitals": {"source": "curated", "status": "available"},
            "transit": {"bus_routes": {"source_class": "synthetic_demo"}},
        },
    )
    service = SummaryApplicationService(
        region=lambda code: region if code == "320400" else None,
        hospitals=lambda: [{"id": 1}, {"id": 2}],
        real_doctors=lambda: [{"id": 3}],
        fallback_doctors=lambda: [{"id": 4}, {"id": 5}],
        transit=lambda: {"routes": [{"id": "1"}, {"id": "2"}]},
    )

    payload = service.build("320400")

    assert payload["region"]["region_pack_version"] == "region-pack-v1"
    assert payload["metrics"]["hospitals"] == {
        "value": 2,
        "label": "医疗机构",
        "source_class": "curated",
        "status": "available",
    }
    assert payload["metrics"]["doctors"]["value"] == 1
    assert payload["metrics"]["bus_routes"]["source_class"] == "synthetic_demo"
    assert payload["metrics"]["districts"]["value"] == 2


def test_summary_service_preserves_region_fallback_shape():
    service = SummaryApplicationService(
        region=lambda _: None,
        hospitals=lambda: [],
        real_doctors=lambda: [],
        fallback_doctors=lambda: [{"id": 1}],
        transit=lambda: {"routes": []},
    )

    payload = service.build("320499")

    assert payload["region"] == {
        "code": "320499",
        "name": "常州市",
        "status": "not_ready",
        "region_pack_version": "unknown",
    }
    assert payload["metrics"]["doctors"]["status"] == "fallback"


def test_evidence_service_delegates_with_fixed_project_and_triage_dependency(tmp_path):
    triage_fn = lambda condition: {"condition": condition}
    service = EvidenceApplicationService(tmp_path, triage_fn)

    with patch("backend.app.application.evidence.build_evidence_payload", return_value={"status": "provisional"}) as builder:
        payload = service.build(
            app_version="app",
            ranking_version="ranking",
            triage_rules_version="triage",
            model_version="model",
            dataset_version="dataset",
            region_pack_version="region",
            region_code="320400",
        )

    assert payload == {"status": "provisional"}
    builder.assert_called_once_with(
        tmp_path,
        app_version="app",
        ranking_version="ranking",
        triage_rules_version="triage",
        model_version="model",
        dataset_version="dataset",
        region_pack_version="region",
        region_code="320400",
        triage_fn=triage_fn,
    )


def test_map_service_uses_active_region_and_hospital_supplier():
    region = SimpleNamespace(name="测试市", version="pack-test")
    service = MapViewApplicationService(
        hospitals=lambda: [
            {"id": 1, "name": "测试医院", "lat": 31.0, "lng": 119.0, "emergency": True},
        ],
        region=lambda _: region,
    )

    payload = service.build(region_code="999999", user_lat=31.0, user_lng=119.0)

    assert payload["region"] == {
        "code": "999999",
        "name": "测试市",
        "region_pack_version": "pack-test",
    }
    assert payload["count"] == 1
    assert payload["items"][0]["marker_type"] == "EMERGENCY_CAPABLE"
    assert payload["items"][0]["distance_km"] == 0.0
