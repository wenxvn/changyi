import { useCallback, useEffect, useState } from "react";

export interface FavoriteDoctorEntry {
  doctor_id: number;
  created_at: string;
}

const STORAGE_KEY = "changyi.favorite_doctors.v1";
const MAX_FAVORITES = 100;

function readFavorites(): FavoriteDoctorEntry[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item): item is FavoriteDoctorEntry => {
        if (!item || typeof item !== "object") return false;
        const record = item as Record<string, unknown>;
        return typeof record.doctor_id === "number" && typeof record.created_at === "string";
      })
      .slice(0, MAX_FAVORITES);
  } catch {
    return [];
  }
}

function writeFavorites(entries: FavoriteDoctorEntry[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_FAVORITES)));
  } catch {
    // localStorage may be unavailable; favorites stay session-only in memory.
  }
}

export function useFavoriteDoctors() {
  const [favorites, setFavorites] = useState<FavoriteDoctorEntry[]>(() => readFavorites());

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) setFavorites(readFavorites());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const isFavorite = useCallback(
    (doctorId: number) => favorites.some((item) => item.doctor_id === doctorId),
    [favorites],
  );

  const toggleFavorite = useCallback((doctorId: number) => {
    setFavorites((previous) => {
      const exists = previous.some((item) => item.doctor_id === doctorId);
      const next = exists
        ? previous.filter((item) => item.doctor_id !== doctorId)
        : [{ doctor_id: doctorId, created_at: new Date().toISOString() }, ...previous].slice(0, MAX_FAVORITES);
      writeFavorites(next);
      return next;
    });
  }, []);

  const favoriteDoctorIds = favorites.map((item) => item.doctor_id);

  return { favorites, favoriteDoctorIds, isFavorite, toggleFavorite };
}
