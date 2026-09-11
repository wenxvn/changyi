import { apiRequest } from "./client";
import { parseFollowupResponse, parseTriagePayload } from "./schemas";
import type { FollowupAnswer, FollowupResponse, TriagePayload } from "../types/api";

export interface TriageRequest {
  condition: string;
  scenario?: "common" | "complex" | "surgery" | "first_visit";
  district?: string;
  lat?: number;
  lng?: number;
  location_source?: "unknown" | "geolocation" | "district";
  followup_answers?: FollowupAnswer[];
}

export function startTriage(
  payload: TriageRequest,
  signal?: AbortSignal,
): Promise<TriagePayload> {
  return apiRequest<TriagePayload>("/api/v1/triage", {
    method: "POST",
    body: JSON.stringify(payload),
    signal,
    parseData: parseTriagePayload,
  });
}

export function getFollowups(
  payload: TriageRequest,
  signal?: AbortSignal,
): Promise<FollowupResponse> {
  return apiRequest<FollowupResponse>("/api/v1/triage/followups", {
    method: "POST",
    body: JSON.stringify(payload),
    signal,
    parseData: parseFollowupResponse,
  });
}
