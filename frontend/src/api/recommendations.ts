import { apiRequest } from "./client";
import { parseRecommendations } from "./schemas";
import type { FollowupAnswer, RecommendationPayload } from "../types/api";

export type ExpertPreference = "system" | "no_expert" | "wish_expert";
export type VisitIntent =
  | "first_visit"
  | "follow_up"
  | "review_results"
  | "procedure_consult"
  | "unsure";

export interface RoutingPreferences {
  district_preference?: "prefer_home_district" | "allow_cross_district" | "any_district";
  distance_preference?: "prefer_nearby" | "allow_farther_for_fit" | "distance_flexible";
  continuity_preference?: boolean;
}

export interface RecommendationRequest {
  condition: string;
  scenario?: "common" | "complex" | "surgery" | "first_visit";
  district?: string;
  lat?: number;
  lng?: number;
  location_source?: "unknown" | "geolocation" | "district";
  followup_answers?: FollowupAnswer[];
  expert_preference?: ExpertPreference;
  visit_intent?: VisitIntent;
  routing_preferences?: RoutingPreferences;
  favorite_doctor_ids?: number[];
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
