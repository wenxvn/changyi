import type { TriagePayload, TriageStatus } from "../types/api";

const PROFILE_STORAGE_KEY = "changyi.demo.profile.v1";
const HISTORY_STORAGE_KEY = "changyi.demo.history.v1";
export const DEMO_PROFILE_EVENT = "changyi:demo-profile";
const MAX_HISTORY_ITEMS = 8;
const VALID_STATUSES: TriageStatus[] = [
  "EMERGENCY",
  "URGENT",
  "ROUTINE",
  "INSUFFICIENT_INFORMATION",
];

export interface DemoProfile {
  historyEnabled: boolean;
}

export interface DemoHistoryItem {
  id: string;
  createdAt: string;
  scenario: "common";
  triageStatus: TriageStatus;
  triageLabel: string;
  matchedDepartment: string | null;
}

function storage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function readValue(key: string): unknown {
  const localStorage = storage();
  if (!localStorage) return null;
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeValue(key: string, value: unknown): boolean {
  const localStorage = storage();
  if (!localStorage) return false;
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function removeValue(key: string): void {
  const localStorage = storage();
  if (!localStorage) return;
  try {
    localStorage.removeItem(key);
  } catch {
    // Browser storage can be disabled or full. The UI remains usable without it.
  }
}

function notify(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(DEMO_PROFILE_EVENT));
}

function isStatus(value: unknown): value is TriageStatus {
  return typeof value === "string" && VALID_STATUSES.includes(value as TriageStatus);
}

function safeText(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback;
  const normalized = value.trim().slice(0, 80);
  return normalized || fallback;
}

function safeDepartment(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.trim().slice(0, 80);
  return normalized || null;
}

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `demo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function readDemoProfile(): DemoProfile {
  const value = readValue(PROFILE_STORAGE_KEY);
  return { historyEnabled: Boolean(value && typeof value === "object" && "historyEnabled" in value && value.historyEnabled === true) };
}

export function setHistoryEnabled(enabled: boolean): DemoProfile {
  const profile = { historyEnabled: enabled } satisfies DemoProfile;
  writeValue(PROFILE_STORAGE_KEY, profile);
  notify();
  return profile;
}

export function readHistory(): DemoHistoryItem[] {
  const value = readValue(HISTORY_STORAGE_KEY);
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object"))
    .filter((item) => typeof item.id === "string" && typeof item.createdAt === "string" && item.scenario === "common" && isStatus(item.triageStatus))
    .map((item) => ({
      id: item.id as string,
      createdAt: item.createdAt as string,
      scenario: "common" as const,
      triageStatus: item.triageStatus as TriageStatus,
      triageLabel: safeText(item.triageLabel, item.triageStatus as string),
      matchedDepartment: safeDepartment(item.matchedDepartment),
    }))
    .slice(0, MAX_HISTORY_ITEMS);
}

export function recordAnalysis(result: Pick<TriagePayload, "triage_status" | "matched_department" | "triage">): void {
  if (!readDemoProfile().historyEnabled || !isStatus(result.triage_status)) return;
  const item: DemoHistoryItem = {
    id: createId(),
    createdAt: new Date().toISOString(),
    scenario: "common",
    triageStatus: result.triage_status,
    triageLabel: safeText(result.triage?.label, result.triage_status),
    matchedDepartment: safeDepartment(result.matched_department),
  };
  writeValue(HISTORY_STORAGE_KEY, [item, ...readHistory()].slice(0, MAX_HISTORY_ITEMS));
  notify();
}

export function clearHistory(): void {
  removeValue(HISTORY_STORAGE_KEY);
  notify();
}
