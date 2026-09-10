import { apiRequest } from "./client";
import { parseMap } from "./schemas";
import type { MapPayload } from "../types/api";

export interface MapRequestOptions {
  lat?: number;
  lng?: number;
  signal?: AbortSignal;
}

export function getMap({ lat, lng, signal }: MapRequestOptions = {}): Promise<MapPayload> {
  const params = new URLSearchParams();
  if (typeof lat === "number") params.set("lat", String(lat));
  if (typeof lng === "number") params.set("lng", String(lng));
  const query = params.toString();
  return apiRequest<MapPayload>(`/api/v1/map${query ? `?${query}` : ""}`, {
    signal,
    parseData: parseMap,
  });
}
