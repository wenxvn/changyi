import { apiRequest } from "./client";
import { parseCitySummary, parseEvidence } from "./schemas";
import type { CitySummary, EvidencePayload } from "../types/api";

export function getCitySummary(signal?: AbortSignal): Promise<CitySummary> {
  return apiRequest<CitySummary>("/api/v1/summary", {
    signal,
    parseData: parseCitySummary,
  });
}

export function getEvidence(signal?: AbortSignal): Promise<EvidencePayload> {
  return apiRequest<EvidencePayload>("/api/v1/evidence", {
    signal,
    parseData: parseEvidence,
  });
}
