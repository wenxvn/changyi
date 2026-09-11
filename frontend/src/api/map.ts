import { apiRequest } from "./client";
import { parseMap } from "./schemas";
import type { MapPayload } from "../types/api";

export interface MapRequestOptions {
  lat?: number;
  lng?: number;
  district?: string;
  location_source?: "unknown" | "geolocation" | "district";
  signal?: AbortSignal;
}

export function getMap({ lat, lng, district, location_source, signal }: MapRequestOptions = {}): Promise<MapPayload> {
  const params = new URLSearchParams();
  if (typeof lat === "number") params.set("lat", String(lat));
  if (typeof lng === "number") params.set("lng", String(lng));
  if (district) params.set("district", district);
  if (location_source) params.set("location_source", location_source);
  const query = params.toString();
  return apiRequest<MapPayload>(`/api/v1/map${query ? `?${query}` : ""}`, {
    signal,
    parseData: parseMap,
  });
}
