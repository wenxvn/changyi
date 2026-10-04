import { useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { getRecommendations, type VisitIntent, type RoutingPreferences } from "../api/recommendations";
import type { FollowupAnswer, RecommendationPayload } from "../types/api";

export interface RecommendationLocationInput {
  source: "unknown" | "district" | "geolocation";
  district?: string | null;
  lat?: number | null;
  lng?: number | null;
}

export interface RecommendationInput {
  condition: string;
  /** v1 request field: structured question_id/value pairs, never free text in condition. */
  followup_answers: FollowupAnswer[];
  expertPreference: "system" | "wish_expert" | "no_expert";
  visitIntent: VisitIntent | "";
  routingPreferences: RoutingPreferences;
  favoriteDoctorIds: number[];
  location: RecommendationLocationInput;
}

/**
 * Identity of a recommendation request. Every input that can change the server
 * response is part of the key, so one key maps to exactly one request.
 */
function requestKey(input: RecommendationInput): string {
  const { location } = input;
  return [
    input.condition,
    location.source,
    location.source === "district" ? location.district ?? "" : "",
    location.source === "geolocation" ? `${location.lat ?? ""},${location.lng ?? ""}` : "",
    input.expertPreference,
    input.visitIntent,
    input.routingPreferences.district_preference,
    input.routingPreferences.distance_preference,
    String(Boolean(input.routingPreferences.continuity_preference)),
    input.favoriteDoctorIds.join(","),
    input.followup_answers.map((answer) => `${answer.question_id}=${answer.value ?? answer.text_answer ?? ""}`).join(";"),
  ].join("|");
}

/**
 * Single owner of the recommendation request lifecycle for the triage workspace.
 *
 * State updates never re-fire an active or settled identity. Explicit retry,
 * re-enabling routing, and development effect replay can start a new attempt;
 * only the current attempt may publish data or finish its loading state.
 */
export function useRecommendations(
  enabled: boolean,
  suspended: boolean,
  input: RecommendationInput,
) {
  const [data, setData] = useState<RecommendationPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const key = requestKey(input);
  const inFlightRef = useRef<{ key: string } | null>(null);
  const settledRef = useRef<string | null>(null);
  const mountedRef = useRef(true);
  const currentRef = useRef({ key, enabled });
  currentRef.current = { key, enabled };

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      inFlightRef.current = null;
    };
  }, []);

  // Drop stale results as soon as the request identity changes.
  useEffect(() => {
    if (enabled && (settledRef.current === key || inFlightRef.current?.key === key)) return;
    inFlightRef.current = null;
    settledRef.current = null;
    setLoading(false);
    setData(null);
    setError(null);
  }, [key, enabled]);

  useEffect(() => {
    if (!enabled || suspended) return;
    if (!input.condition.trim()) return;
    if (settledRef.current === key || inFlightRef.current?.key === key) return;
    void load();
    // `load` reads the same key; the guard above keeps this idempotent per identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, suspended, key]);

  async function load() {
    if (!enabled || !input.condition.trim() || inFlightRef.current?.key === key) return;
    // A unique attempt token also distinguishes A → B → A from the first A.
    const attempt = { key };
    inFlightRef.current = attempt;
    setLoading(true);
    setError(null);
    const { location } = input;
    try {
      const payload = await getRecommendations({
        condition: input.condition.trim(),
        scenario: "common",
        ...(location.source === "district" && location.district ? { district: location.district } : {}),
        ...(location.source === "geolocation" && typeof location.lat === "number" && typeof location.lng === "number"
          ? { lat: location.lat, lng: location.lng }
          : {}),
        location_source: location.source,
        followup_answers: input.followup_answers,
        expert_preference: input.expertPreference,
        ...(input.visitIntent ? { visit_intent: input.visitIntent } : {}),
        routing_preferences: input.routingPreferences,
        ...(input.routingPreferences.continuity_preference && input.favoriteDoctorIds.length
          ? { favorite_doctor_ids: input.favoriteDoctorIds.slice(0, 50) }
          : {}),
      });
      if (!mountedRef.current || inFlightRef.current !== attempt || !currentRef.current.enabled || currentRef.current.key !== key) return;
      settledRef.current = key;
      setData(payload);
    } catch (reason) {
      if (!mountedRef.current || inFlightRef.current !== attempt || !currentRef.current.enabled || currentRef.current.key !== key) return;
      setError(reason instanceof ApiError ? reason : new ApiError("NETWORK_ERROR", "资源推荐暂时无法连接。"));
    } finally {
      if (inFlightRef.current === attempt) {
        inFlightRef.current = null;
        if (mountedRef.current) setLoading(false);
      }
    }
  }

  /** Retry the current request identity after a failure. */
  function reload() {
    if (inFlightRef.current?.key === key) return;
    settledRef.current = null;
    void load();
  }

  return { data, loading, error, reload };
}
