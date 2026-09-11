from __future__ import annotations

from unittest import TestCase

from backend.app.application.transit import TransitCatalogApplicationService


class TransitCatalogApplicationServiceTests(TestCase):
    def make_service(self) -> TransitCatalogApplicationService:
        return TransitCatalogApplicationService(
            routes=lambda: {
                "summary": {"source": "sample"},
                "routes": [
                    {"company": "A", "line_type": "常规", "bus_count": 4, "ticket": 2},
                    {"company": "A", "line_type": "快线", "bus_count": 6, "ticket": 3},
                ],
            },
            stations=lambda: {"summary": {"count": 1}, "stations": [{"id": "s1"}]},
            taxi_operations=lambda: {"summary": {"count": 2}, "operations": [{"id": "t1"}]},
            bike_stations=lambda: {"summary": {"count": 3}, "stations": [{"id": "b1"}]},
            bike_vehicles=lambda: {"summary": {"count": 4}, "vehicles": [{"id": "v1"}]},
            hospital_station_access=lambda: [{"hospital_id": 1}],
            hospital_taxi_access=lambda: [{"hospital_id": 1}],
            hospital_bike_access=lambda: [{"hospital_id": 1}],
            hospital_bike_vehicle_distribution=lambda: [{"hospital_id": 1}],
        )

    def test_dataset_payloads_preserve_collection_and_summary(self):
        service = self.make_service()

        self.assertEqual(service.routes_payload(), {
            "items": [
                {"company": "A", "line_type": "常规", "bus_count": 4, "ticket": 2},
                {"company": "A", "line_type": "快线", "bus_count": 6, "ticket": 3},
            ],
            "summary": {"source": "sample"},
        })
        self.assertEqual(service.stations_payload()["summary"]["count"], 1)
        self.assertEqual(service.taxi_operations_payload()["items"][0]["id"], "t1")
        self.assertEqual(service.bike_stations_payload()["items"][0]["id"], "b1")
        self.assertEqual(service.bike_vehicles_payload()["items"][0]["id"], "v1")

    def test_stats_keeps_legacy_derived_summary(self):
        stats = self.make_service().stats()

        self.assertEqual(stats["source"], "sample")
        self.assertEqual(stats["total_routes"], 2)
        self.assertEqual(stats["total_bus_count"], 10)
        self.assertEqual(stats["company_route_counts"], {"A": 2})
        self.assertEqual(stats["line_type_counts"], {"常规": 1, "快线": 1})
        self.assertEqual(stats["avg_ticket"], 2.5)
        self.assertEqual(stats["max_bus_route"]["bus_count"], 6)
        self.assertEqual(stats["hospital_station_access"], [{"hospital_id": 1}])
