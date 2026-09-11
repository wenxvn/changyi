from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.traffic import (
    accessibility_score_from_context,
    build_traffic_access,
    default_traffic_access,
    hospital_bike_access,
    hospital_bike_vehicle_distribution,
    hospital_station_access,
    hospital_taxi_access,
    index_traffic_rows,
)


class RecommendationTrafficTests(TestCase):
    def test_default_payload_marks_missing_traffic_as_non_fact(self):
        payload = default_traffic_access()
        self.assertEqual(payload["public_transport_score"], 0.60)
        self.assertEqual(payload["bike_display_score"], 0.0)
        self.assertEqual(payload["summary"], "暂无交通融合数据")

    def test_payload_separates_display_bike_data_from_ranking_scores(self):
        payload = build_traffic_access(
            {"transit_station_score": 90, "nearest_station_name": "人民公园", "nearest_station_distance_km": 0.8, "nearby_station_count_2km": 2},
            {"taxi_access_score": 70, "nearby_taxi_destination_count_3km": 1},
            {"bike_service_level": 92},
        )
        self.assertEqual(payload["station_score"], 0.9)
        self.assertEqual(payload["taxi_score"], 0.7)
        self.assertEqual(payload["public_transport_score"], 0.81)
        self.assertEqual(payload["bike_display_score"], 92)
        self.assertIn("不参与医疗推荐排序", payload["bike_display_note"])
        self.assertIn("人民公园", payload["summary"])

    def test_emergency_and_urgent_use_distance_without_transit_weight(self):
        traffic = {"station_score": 0.0, "taxi_score": 0.0, "public_transport_score": 0.0}
        self.assertEqual(accessibility_score_from_context(3.0, traffic, "emergency"), 1.0)
        self.assertEqual(accessibility_score_from_context(3.0, traffic, "urgent"), 1.0)

    def test_routine_and_first_visit_fuse_distance_and_transit_samples(self):
        traffic = {
            "station_score": 0.8,
            "taxi_score": 0.6,
            "public_transport_score": 0.71,
            "nearest_station_name": "人民公园",
            "nearby_station_count_2km": 3,
            "nearby_taxi_destination_count_3km": 2,
        }
        routine = accessibility_score_from_context(10.0, traffic, "routine")
        first_visit = accessibility_score_from_context(10.0, traffic, "first_visit")
        self.assertGreater(routine, 0.0)
        self.assertGreater(first_visit, 0.0)
        self.assertNotEqual(routine, first_visit)
        # No location: ranking stays neutral instead of inventing transit-driven access.
        self.assertEqual(accessibility_score_from_context(None, traffic, "routine"), 0.6)
        marked = {**traffic, "used_in_ranking": True}
        self.assertAlmostEqual(
            accessibility_score_from_context(None, marked, "routine"),
            0.71 * 0.45 + 0.55 * 0.60,
        )

    def test_sparse_traffic_samples_fall_back_to_distance_only(self):
        sparse = {"station_score": 0.95, "taxi_score": 0.92, "public_transport_score": 0.94}
        self.assertEqual(
            accessibility_score_from_context(10.0, sparse, "routine"),
            accessibility_score_from_context(10.0, sparse, "first_visit"),
        )
        self.assertEqual(accessibility_score_from_context(None, sparse, "routine"), 0.6)

    def test_index_preserves_rows_and_last_duplicate_wins(self):
        station = {"hospital_id": "h1", "transit_station_score": 70}
        station_replacement = {"hospital_id": "h1", "transit_station_score": 95}
        taxi = {"hospital_id": "h2", "taxi_access_score": 82}
        bike = {"hospital_id": "h3", "bike_service_level": 92}
        indexed = index_traffic_rows(
            [station, station_replacement],
            [taxi],
            [bike],
        )
        self.assertIs(indexed["station"]["h1"], station_replacement)
        self.assertIs(indexed["taxi"]["h2"], taxi)
        self.assertIs(indexed["bike"]["h3"], bike)

    def test_index_accepts_empty_sample_sets(self):
        self.assertEqual(index_traffic_rows([], [], []), {"station": {}, "taxi": {}, "bike": {}})

    def test_station_access_keeps_thresholds_and_missing_coordinate_fallback(self):
        hospitals = [{"id": 1, "name": "示例医院", "lat": 0, "lng": 0}]
        stations = [
            {"latitude": 1, "longitude": 0, "station_name": "近站"},
            {"latitude": 2.5, "longitude": 0, "station_name": "中站"},
            {"latitude": None, "longitude": 0, "station_name": "无坐标"},
        ]
        rows = hospital_station_access(hospitals, stations, lambda *_: 1 if _[2] == 1 else 2.5)
        self.assertEqual(rows[0]["nearest_station_name"], "近站")
        self.assertEqual(rows[0]["nearby_station_count_2km"], 1)
        self.assertEqual(rows[0]["nearby_station_count_3km"], 2)
        self.assertEqual(rows[0]["transit_station_score"], 70)

    def test_taxi_access_keeps_distance_counts_and_average_samples(self):
        hospitals = [{"id": 1, "name": "示例医院", "lat": 0, "lng": 0}]
        operations = [
            {"dest_latitude": 2, "dest_longitude": 0, "fact_price": 12, "drive_mile": 3},
            {"dest_latitude": 4, "dest_longitude": 0, "fact_price": 20, "drive_mile": 5},
            {"dest_latitude": 6, "dest_longitude": 0, "fact_price": 40, "drive_mile": 8},
        ]
        rows = hospital_taxi_access(hospitals, operations, lambda *_: _[2])
        self.assertEqual(rows[0]["nearby_taxi_destination_count_3km"], 1)
        self.assertEqual(rows[0]["nearby_taxi_destination_count_5km"], 2)
        self.assertEqual(rows[0]["avg_nearby_taxi_fare"], 16.0)
        self.assertEqual(rows[0]["avg_nearby_taxi_mile"], 4.0)
        self.assertEqual(rows[0]["taxi_access_score"], 68)

    def test_bike_access_and_vehicle_distribution_keep_display_metrics(self):
        hospitals = [{"id": 1, "name": "示例医院", "lat": 0, "lng": 0}]
        stations = [
            {"latitude": 0.5, "longitude": 0, "station_name": "近骑行站", "bike_num": 100, "e_bike_num": 20, "lock_num": 10},
            {"latitude": 1.5, "longitude": 0, "station_name": "远骑行站", "bike_num": 20, "e_bike_num": 5, "lock_num": 2},
        ]
        bikes = hospital_bike_access(hospitals, stations, lambda *_: _[2])
        vehicles = hospital_bike_vehicle_distribution(
            hospitals,
            [
                {"latitude": 0.5, "longitude": 0, "bike_state": "正常"},
                {"latitude": 1.5, "longitude": 0, "bike_state": "故障"},
                {"latitude": 2.5, "longitude": 0, "bike_state": "正常"},
            ],
            lambda *_: _[2],
        )
        self.assertEqual(bikes[0]["bike_supply_2km"], 120)
        self.assertEqual(bikes[0]["bike_service_level"], 92)
        self.assertEqual(vehicles[0]["nearby_vehicle_count_1km"], 1)
        self.assertEqual(vehicles[0]["nearby_vehicle_count_2km"], 2)
        self.assertEqual(vehicles[0]["normal_vehicle_count_2km"], 1)

    def test_traffic_sample_calculators_return_safe_empty_rows(self):
        hospitals = [{"id": 1, "name": "示例医院", "lat": 0, "lng": 0}]
        distance = lambda *_: 999
        self.assertEqual(hospital_station_access(hospitals, [], distance)[0]["transit_station_score"], 35)
        self.assertEqual(hospital_taxi_access(hospitals, [], distance)[0]["taxi_access_score"], 40)
        self.assertEqual(hospital_bike_access(hospitals, [], distance)[0]["bike_service_level"], 35)
        self.assertEqual(hospital_bike_vehicle_distribution(hospitals, [], distance)[0]["normal_vehicle_count_2km"], 0)
