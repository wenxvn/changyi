import type { RecommendedDoctor, RecommendedHospital } from "../../types/api";

/**
 * Shared display helpers for recommendation resources.
 *
 * These only format fields the v1 API already returns. No score, rating,
 * capacity or quality value is invented here.
 */

export function formatDistance(value: number | null | undefined): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value < 1 ? `${Math.round(value * 1000)} m` : `${value.toFixed(1)} km`;
}

export function hospitalName(item: RecommendedHospital): string {
  return typeof item.hospital.name === "string" && item.hospital.name ? item.hospital.name : "推荐医疗机构";
}

export function doctorName(item: RecommendedDoctor): string {
  return typeof item.doctor.name === "string" && item.doctor.name ? item.doctor.name : "公开医生资料";
}

/** Recommendation reasons, already phrased for users by the ranking pipeline. */
export function recommendationReasons(item: RecommendedHospital, limit = 3): string[] {
  return (item.explanations ?? []).filter(Boolean).slice(0, limit);
}

export function doctorReasons(item: RecommendedDoctor, limit = 2): string[] {
  return (item.reasons ?? []).filter(Boolean).slice(0, limit);
}

export function resourceSourceLabel(source: string | undefined): string {
  if (source === "real" || source === "real_data") return "常州公开资源";
  if (source === "mock") return "演示资源";
  return "公开资源";
}

export function transitDatasetLabel(datasetId: string): string {
  if (datasetId === "bus_stations") return "公交站";
  if (datasetId === "taxi_operations") return "出租车";
  if (datasetId === "bike") return "共享骑行";
  return datasetId;
}

/** Traffic summary, only when it actually carries a usable sentence. */
export function trafficSummary(item: RecommendedHospital): string | null {
  const access = item.traffic_access;
  if (!access || typeof access !== "object") return null;
  const summary = typeof access.summary === "string" ? access.summary : "";
  if (!summary || summary.includes("暂无交通融合数据")) return null;
  return summary;
}

export function trafficUsedInRanking(item: RecommendedHospital): boolean {
  const access = item.traffic_access;
  return Boolean(access && typeof access === "object" && access.used_in_ranking);
}

export function hospitalContextQuery(direction?: string | null, safety?: string | null): string {
  const params = new URLSearchParams({ from: "triage" });
  if (direction) params.set("direction", direction);
  if (safety) params.set("safety", safety);
  return params.toString();
}
