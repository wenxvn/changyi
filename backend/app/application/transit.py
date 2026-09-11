"""Application read models for the legacy transit data endpoints."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


DatasetSupplier = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class TransitCatalogApplicationService:
    """Compose transit datasets and derived summaries without Flask concerns."""

    routes: DatasetSupplier
    stations: DatasetSupplier
    taxi_operations: DatasetSupplier
    bike_stations: DatasetSupplier
    bike_vehicles: DatasetSupplier
    hospital_station_access: Callable[[], Sequence[Mapping[str, Any]]]
    hospital_taxi_access: Callable[[], Sequence[Mapping[str, Any]]]
    hospital_bike_access: Callable[[], Sequence[Mapping[str, Any]]]
    hospital_bike_vehicle_distribution: Callable[[], Sequence[Mapping[str, Any]]]

    @staticmethod
    def _collection(dataset: Mapping[str, Any], key: str) -> list[Any]:
        value = dataset.get(key, [])
        return list(value) if isinstance(value, list) else []

    @staticmethod
    def _summary(dataset: Mapping[str, Any]) -> dict[str, Any]:
        value = dataset.get("summary", {})
        return dict(value) if isinstance(value, Mapping) else {}

    def routes_payload(self) -> dict[str, Any]:
        dataset = self.routes()
        return {"items": self._collection(dataset, "routes"), "summary": self._summary(dataset)}

    def stations_payload(self) -> dict[str, Any]:
        dataset = self.stations()
        return {"items": self._collection(dataset, "stations"), "summary": self._summary(dataset)}

    def taxi_operations_payload(self) -> dict[str, Any]:
        dataset = self.taxi_operations()
        return {"items": self._collection(dataset, "operations"), "summary": self._summary(dataset)}

    def bike_stations_payload(self) -> dict[str, Any]:
        dataset = self.bike_stations()
        return {"items": self._collection(dataset, "stations"), "summary": self._summary(dataset)}

    def bike_vehicles_payload(self) -> dict[str, Any]:
        dataset = self.bike_vehicles()
        return {"items": self._collection(dataset, "vehicles"), "summary": self._summary(dataset)}

    def stats(self) -> dict[str, Any]:
        route_dataset = self.routes()
        routes = self._collection(route_dataset, "routes")
        company_counts: dict[str, int] = {}
        company_bus_counts: dict[str, int] = {}
        line_type_counts: dict[str, int] = {}
        ticket_counts: dict[str, int] = {}
        total_bus = 0
        tickets: list[float] = []

        for route in routes:
            company = route.get("company") or "未知分公司"
            line_type = route.get("line_type") or "未知类型"
            bus_count = int(route.get("bus_count") or 0)
            ticket = route.get("ticket") or 0

            company_counts[company] = company_counts.get(company, 0) + 1
            company_bus_counts[company] = company_bus_counts.get(company, 0) + bus_count
            line_type_counts[line_type] = line_type_counts.get(line_type, 0) + 1
            total_bus += bus_count

            if ticket:
                tickets.append(float(ticket))
                ticket_key = f"{ticket:g}元"
                ticket_counts[ticket_key] = ticket_counts.get(ticket_key, 0) + 1

        summary = self._summary(route_dataset)
        summary.update({
            "total_routes": len(routes),
            "total_bus_count": total_bus,
            "company_count": len(company_counts),
            "line_type_count": len(line_type_counts),
            "avg_ticket": round(sum(tickets) / len(tickets), 2) if tickets else 0,
            "max_bus_route": max(routes, key=lambda route: int(route.get("bus_count") or 0), default={}),
            "company_route_counts": company_counts,
            "company_bus_counts": company_bus_counts,
            "line_type_counts": line_type_counts,
            "ticket_counts": ticket_counts,
            "routes_preview": routes[:8],
            "station_summary": self._summary(self.stations()),
            "taxi_summary": self._summary(self.taxi_operations()),
            "bike_summary": self._summary(self.bike_stations()),
            "bike_vehicle_summary": self._summary(self.bike_vehicles()),
            "hospital_station_access": list(self.hospital_station_access()),
            "hospital_taxi_access": list(self.hospital_taxi_access()),
            "hospital_bike_access": list(self.hospital_bike_access()),
            "hospital_bike_vehicle_distribution": list(self.hospital_bike_vehicle_distribution()),
        })
        return summary
