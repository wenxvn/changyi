"""Pure traffic feature and accessibility score helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .scoring import clamp


def default_traffic_access() -> dict[str, Any]:
    return {
        "station_score": 0.60,
        "taxi_score": 0.60,
        "public_transport_score": 0.60,
        "bike_display_score": 0.0,
        "summary": "暂无交通融合数据",
    }


def index_traffic_rows(
    station_rows: Sequence[Mapping[str, Any]],
    taxi_rows: Sequence[Mapping[str, Any]],
    bike_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[Any, Mapping[str, Any]]]:
    """Index already-computed traffic sample rows by hospital ID.

    The legacy cache keeps the last row for duplicate IDs and retains the
    original row objects. Loading, computing, and caching those rows remain
    outside this pure boundary.
    """

    return {
        "station": {row["hospital_id"]: row for row in station_rows},
        "taxi": {row["hospital_id"]: row for row in taxi_rows},
        "bike": {row["hospital_id"]: row for row in bike_rows},
    }


def hospital_station_access(
    hospitals: Sequence[Mapping[str, Any]],
    stations: Sequence[Mapping[str, Any]],
    distance_fn: Callable[[float, float, float, float], float],
) -> list[dict[str, Any]]:
    """Calculate the legacy bus-station access sample for each hospital."""

    results = []
    for hospital in hospitals:
        distances = []
        for station in stations:
            lat = station.get("latitude")
            lng = station.get("longitude")
            if lat is None or lng is None:
                continue
            distance = distance_fn(hospital["lat"], hospital["lng"], lat, lng)
            distances.append((distance, station))
        distances.sort(key=lambda item: item[0])
        nearest = distances[0] if distances else (None, {})
        nearby_2km = [item for item in distances if item[0] <= 2]
        nearby_3km = [item for item in distances if item[0] <= 3]
        score = 35
        if len(nearby_2km) >= 5:
            score = 95
        elif len(nearby_2km) >= 3:
            score = 85
        elif len(nearby_2km) >= 1:
            score = 70
        elif nearest[0] is not None and nearest[0] <= 5:
            score = 55
        results.append({
            "hospital_id": hospital["id"],
            "hospital_name": hospital["name"],
            "nearest_station_name": nearest[1].get("station_name", "") if nearest[1] else "",
            "nearest_station_distance_km": round(nearest[0], 2) if nearest[0] is not None else None,
            "nearby_station_count_2km": len(nearby_2km),
            "nearby_station_count_3km": len(nearby_3km),
            "transit_station_score": score,
        })
    return sorted(results, key=lambda item: (item["nearest_station_distance_km"] is None, item["nearest_station_distance_km"] or 999))


def hospital_taxi_access(
    hospitals: Sequence[Mapping[str, Any]],
    operations: Sequence[Mapping[str, Any]],
    distance_fn: Callable[[float, float, float, float], float],
) -> list[dict[str, Any]]:
    """Calculate the legacy taxi-operation access sample for each hospital."""

    results = []
    for hospital in hospitals:
        destination_hits = []
        nearest = None
        for operation in operations:
            lat = operation.get("dest_latitude")
            lng = operation.get("dest_longitude")
            if lat is None or lng is None:
                continue
            distance = distance_fn(hospital["lat"], hospital["lng"], lat, lng)
            if nearest is None or distance < nearest[0]:
                nearest = (distance, operation)
            if distance <= 5:
                destination_hits.append((distance, operation))

        within_3km = [item for item in destination_hits if item[0] <= 3]
        fares = [item[1].get("fact_price") for item in destination_hits if item[1].get("fact_price") is not None]
        miles = [item[1].get("drive_mile") for item in destination_hits if item[1].get("drive_mile") is not None]
        score = 40
        if len(within_3km) >= 5:
            score = 92
        elif len(within_3km) >= 3:
            score = 82
        elif len(within_3km) >= 1:
            score = 68
        elif nearest and nearest[0] <= 8:
            score = 55

        results.append({
            "hospital_id": hospital["id"],
            "hospital_name": hospital["name"],
            "nearby_taxi_destination_count_3km": len(within_3km),
            "nearby_taxi_destination_count_5km": len(destination_hits),
            "nearest_taxi_destination_distance_km": round(nearest[0], 2) if nearest else None,
            "avg_nearby_taxi_fare": round(sum(fares) / len(fares), 2) if fares else 0,
            "avg_nearby_taxi_mile": round(sum(miles) / len(miles), 2) if miles else 0,
            "taxi_access_score": score,
        })
    return sorted(results, key=lambda item: (-item["nearby_taxi_destination_count_3km"], item["nearest_taxi_destination_distance_km"] or 999))


def hospital_bike_access(
    hospitals: Sequence[Mapping[str, Any]],
    stations: Sequence[Mapping[str, Any]],
    distance_fn: Callable[[float, float, float, float], float],
) -> list[dict[str, Any]]:
    """Calculate the legacy bike-station display sample for each hospital."""

    results = []
    for hospital in hospitals:
        distances = []
        for station in stations:
            lat = station.get("latitude")
            lng = station.get("longitude")
            if lat is None or lng is None:
                continue
            distance = distance_fn(hospital["lat"], hospital["lng"], lat, lng)
            distances.append((distance, station))
        distances.sort(key=lambda item: item[0])
        nearest = distances[0] if distances else (None, {})
        nearby_1km = [item for item in distances if item[0] <= 1]
        nearby_2km = [item for item in distances if item[0] <= 2]
        bike_supply_2km = sum(int(item[1].get("bike_num") or 0) for item in nearby_2km)
        e_bike_supply_2km = sum(int(item[1].get("e_bike_num") or 0) for item in nearby_2km)
        lock_supply_2km = sum(int(item[1].get("lock_num") or 0) for item in nearby_2km)
        service_level = 35
        if len(nearby_1km) >= 4 or bike_supply_2km >= 120:
            service_level = 92
        elif len(nearby_1km) >= 2 or bike_supply_2km >= 60:
            service_level = 82
        elif len(nearby_2km) >= 1:
            service_level = 68
        elif nearest[0] is not None and nearest[0] <= 4:
            service_level = 55
        results.append({
            "hospital_id": hospital["id"],
            "hospital_name": hospital["name"],
            "nearest_bike_station_name": nearest[1].get("station_name", "") if nearest[1] else "",
            "nearest_bike_station_distance_km": round(nearest[0], 2) if nearest[0] is not None else None,
            "nearby_bike_station_count_1km": len(nearby_1km),
            "nearby_bike_station_count_2km": len(nearby_2km),
            "bike_supply_2km": bike_supply_2km,
            "e_bike_supply_2km": e_bike_supply_2km,
            "lock_supply_2km": lock_supply_2km,
            "bike_service_level": service_level,
        })
    return sorted(results, key=lambda item: (-item["bike_supply_2km"], item["nearest_bike_station_distance_km"] or 999))


def hospital_bike_vehicle_distribution(
    hospitals: Sequence[Mapping[str, Any]],
    vehicles: Sequence[Mapping[str, Any]],
    distance_fn: Callable[[float, float, float, float], float],
) -> list[dict[str, Any]]:
    """Calculate the legacy nearby bike-vehicle display sample."""

    results = []
    for hospital in hospitals:
        nearby_1km = []
        nearby_2km = []
        for vehicle in vehicles:
            lat = vehicle.get("latitude")
            lng = vehicle.get("longitude")
            if lat is None or lng is None:
                continue
            distance = distance_fn(hospital["lat"], hospital["lng"], lat, lng)
            if distance <= 1:
                nearby_1km.append(vehicle)
            if distance <= 2:
                nearby_2km.append(vehicle)
        normal_2km = [vehicle for vehicle in nearby_2km if vehicle.get("bike_state") == "正常"]
        results.append({
            "hospital_id": hospital["id"],
            "hospital_name": hospital["name"],
            "nearby_vehicle_count_1km": len(nearby_1km),
            "nearby_vehicle_count_2km": len(nearby_2km),
            "normal_vehicle_count_2km": len(normal_2km),
        })
    return sorted(results, key=lambda item: -item["normal_vehicle_count_2km"])


def build_traffic_access(
    station: Mapping[str, Any] | None,
    taxi: Mapping[str, Any] | None,
    bike: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build the legacy traffic payload from already-selected sample rows."""

    station = station or {}
    taxi = taxi or {}
    bike = bike or {}
    station_score = clamp((station.get("transit_station_score") or 60) / 100.0)
    taxi_score = clamp((taxi.get("taxi_access_score") or 60) / 100.0)
    public_transport_score = clamp(station_score * 0.55 + taxi_score * 0.45)
    parts = []
    if station.get("nearest_station_name"):
        parts.append(f"最近公交站{station.get('nearest_station_name')}约{station.get('nearest_station_distance_km')}km")
    if station.get("nearby_station_count_2km"):
        parts.append(f"2km内公交站{station.get('nearby_station_count_2km')}个")
    if taxi.get("nearby_taxi_destination_count_3km"):
        parts.append(f"3km内出租车到达样本{taxi.get('nearby_taxi_destination_count_3km')}条")
    return {
        "station_score": round(station_score, 4),
        "taxi_score": round(taxi_score, 4),
        "public_transport_score": round(public_transport_score, 4),
        "nearest_station_name": station.get("nearest_station_name", ""),
        "nearest_station_distance_km": station.get("nearest_station_distance_km"),
        "nearby_station_count_2km": station.get("nearby_station_count_2km", 0),
        "nearby_station_count_3km": station.get("nearby_station_count_3km", 0),
        "nearby_taxi_destination_count_3km": taxi.get("nearby_taxi_destination_count_3km", 0),
        "avg_nearby_taxi_fare": taxi.get("avg_nearby_taxi_fare", 0),
        "avg_nearby_taxi_mile": taxi.get("avg_nearby_taxi_mile", 0),
        "bike_display_score": bike.get("bike_service_level", 0),
        "bike_display_note": "共享骑行仅用于绿色出行展示，不参与医疗推荐排序",
        "summary": "；".join(parts) if parts else "交通样本较少，主要按距离估算可达性",
    }


def accessibility_score_from_context(
    distance: float | None,
    traffic_access: Mapping[str, Any],
    triage_level: str = "routine",
) -> float:
    """Calculate legacy access score from explicit distance and traffic data.

    Traffic samples are provisional (see data quality register). They only
    influence ranking when a hospital has concrete nearby evidence; otherwise
    ranking falls back to straight-line distance so sparse quality-gate-failed
    transit rows cannot silently reorder hospitals.
    """

    if distance is None:
        if not traffic_access.get("used_in_ranking"):
            return 0.6
        return traffic_access["public_transport_score"] * 0.45 + 0.55 * 0.60
    if distance <= 5:
        distance_score = 1.0
    elif distance >= 50:
        distance_score = 0.1
    else:
        distance_score = max(0.1, 1.0 - (distance - 5) * 0.02)
    if triage_level in ("emergency", "urgent"):
        return clamp(distance_score)
    has_traffic_evidence = bool(
        traffic_access.get("nearest_station_name")
        or traffic_access.get("nearby_station_count_2km")
        or traffic_access.get("nearby_taxi_destination_count_3km")
    )
    if not has_traffic_evidence:
        return clamp(distance_score)
    if triage_level == "first_visit":
        return clamp(distance_score * 0.56 + traffic_access["station_score"] * 0.28 + traffic_access["taxi_score"] * 0.16)
    return clamp(distance_score * 0.50 + traffic_access["station_score"] * 0.32 + traffic_access["taxi_score"] * 0.18)
