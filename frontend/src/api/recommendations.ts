import { apiRequest } from "./client";
import { parseRecommendations } from "./schemas";
import type { FollowupAnswer, RecommendationPayload } from "../types/api";

export interface RecommendationRequest {
  condition: string;
  scenario?: "common" | "complex" | "surgery" | "first_visit";
  district?: string;
  lat?: number;
  lng?: number;
  location_source?: "unknown" | "geolocation" | "district";
  followup_answers?: FollowupAnswer[];
}

export function getRecommendations(
  payload: RecommendationRequest,
  signal?: AbortSignal,
): Promise<RecommendationPayload> {
  return apiRequest<RecommendationPayload>("/api/v1/recommendations", {
    method: "POST",
    body: JSON.stringify(payload),
    signal,
    parseData: parseRecommendations,
  });
}
