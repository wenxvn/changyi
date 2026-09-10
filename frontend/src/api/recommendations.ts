import { apiRequest } from "./client";
import { parseRecommendations } from "./schemas";
import type { RecommendationPayload } from "../types/api";

export interface RecommendationRequest {
  condition: string;
  scenario?: "common" | "complex" | "surgery" | "first_visit";
  district?: string;
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
