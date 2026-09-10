import { useCallback, useEffect, useState } from "react";
import { getCitySummary } from "../api/evidence";
import { ApiError } from "../api/client";
import type { CitySummary } from "../types/api";

export function useCitySummary() {
  const [data, setData] = useState<CitySummary | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback((signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    getCitySummary(signal)
      .then(setData)
      .catch((reason: unknown) => {
        if (reason instanceof ApiError && reason.code === "REQUEST_ABORTED") return;
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("NETWORK_ERROR", "城市摘要暂时无法载入。"),
        );
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return { data, error, loading, retry: () => load() };
}
