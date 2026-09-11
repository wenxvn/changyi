from types import SimpleNamespace

from backend.app.application.regions import RegionReadApplicationService


def test_region_read_service_reports_active_region_readiness():
    active = [SimpleNamespace(code="320400"), SimpleNamespace(code="310000")]
    registry = SimpleNamespace(active=lambda: active)
    service = RegionReadApplicationService(lambda: registry)

    assert service.readiness("320400") == (True, 2)
    assert service.readiness("999999") == (False, 2)


def test_region_read_service_exposes_active_public_summaries():
    summaries = [{"code": "320400", "name": "常州市", "status": "active"}]
    registry = SimpleNamespace(public_summaries=lambda *, active_only: summaries if active_only else [])
    service = RegionReadApplicationService(lambda: registry)

    assert service.public_summaries() == summaries
