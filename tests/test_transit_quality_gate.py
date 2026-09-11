from backend.app.domain.recommendation.transit_quality import (
    QUALITY_PROVISIONAL,
    TransitQualityGate,
    classify_bus_stations,
)


def test_bus_stations_are_provisional_and_not_rankable_without_full_provenance():
    rows = [
        {"station_name": "A", "latitude": 31.7, "longitude": 119.9, "active_status": "有效"},
        {"station_name": "B", "latitude": None, "longitude": 119.9, "active_status": "未知状态"},
    ]
    quality = classify_bus_stations(rows, {"source": "demo-masked"})
    assert quality.quality == QUALITY_PROVISIONAL
    assert quality.rankable is False
    assert "invalid_coordinates_present" in quality.reasons
    assert "license_not_recorded" in quality.reasons


def test_quality_gate_blocks_ranking_until_verified():
    gate = TransitQualityGate.from_datasets(
        bus_rows=[{"latitude": 31.7, "longitude": 119.9, "active_status": "有效"}],
        bus_summary={"source": "demo"},
    )
    assert gate.can_rank("bus_stations") is False
    assert "质量门" in gate.ranking_notice() or "直线距离" in gate.ranking_notice()
    payload = gate.quality("bus_stations").to_payload()
    assert payload["rankable"] is False
    assert payload["dataset_id"] == "bus_stations"
