import type { ApiEnvelope } from "../types/api";

export type ApiRequestOptions = Omit<RequestInit, "signal"> & {
  signal?: AbortSignal;
  timeoutMs?: number;
  parseData?: (value: unknown) => unknown;
};

export class ApiError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly requestId: string | null;
  readonly details: unknown;

  constructor(
    code: string,
    message: string,
    options: {
      status?: number | null;
      requestId?: string | null;
      details?: unknown;
    } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = options.status ?? null;
    this.requestId = options.requestId ?? null;
    this.details = options.details;
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function createRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `frontend-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function errorFromUnknown(error: unknown, timedOut: boolean): ApiError {
  if (error instanceof ApiError) return error;
  if (timedOut) {
    return new ApiError("TIMEOUT", "请求超时，请检查网络后重试。");
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return new ApiError("REQUEST_ABORTED", "请求已取消。");
  }
  return new ApiError("NETWORK_ERROR", "暂时无法连接服务，请稍后重试。", {
    details: error,
  });
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    signal: externalSignal,
    timeoutMs = 10_000,
    parseData,
    headers: requestHeaders,
    ...requestInit
  } = options;
  const controller = new AbortController();
  let timedOut = false;
  const timeout = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    externalSignal.addEventListener("abort", () => controller.abort(), {
      once: true,
    });
  }

  const requestId = createRequestId();
  const headers = new Headers(requestHeaders);
  headers.set("Accept", "application/json");
  headers.set("X-Request-ID", requestId);
  if (requestInit.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...requestInit,
      headers,
      signal: controller.signal,
    });
    let envelope: ApiEnvelope<unknown>;
    try {
      envelope = (await response.json()) as ApiEnvelope<unknown>;
    } catch (error) {
      throw new ApiError("INVALID_RESPONSE", "服务返回了无法读取的响应。", {
        status: response.status,
        requestId,
        details: error,
      });
    }

    if (!response.ok || envelope.error) {
      throw new ApiError(
        envelope.error?.code ?? `HTTP_${response.status}`,
        envelope.error?.message ?? "服务暂时不可用，请稍后重试。",
        {
          status: response.status,
          requestId: envelope.meta?.request_id ?? requestId,
          details: envelope.error?.details,
        },
      );
    }
    if (envelope.data === null || envelope.data === undefined) {
      throw new ApiError("EMPTY_RESPONSE", "服务返回了空结果。", {
        status: response.status,
        requestId: envelope.meta?.request_id ?? requestId,
      });
    }
    return (parseData ? parseData(envelope.data) : envelope.data) as T;
  } catch (error) {
    throw errorFromUnknown(error, timedOut);
  } finally {
    window.clearTimeout(timeout);
  }
}
