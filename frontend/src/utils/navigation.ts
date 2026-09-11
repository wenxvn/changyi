export interface AmapNavigationTarget {
  name?: string;
  address?: string;
  lat?: number;
  lng?: number;
}

function clean(value: string | undefined): string {
  return value?.trim() ?? "";
}

function hasCoordinates(target: AmapNavigationTarget): boolean {
  return typeof target.lat === "number"
    && Number.isFinite(target.lat)
    && typeof target.lng === "number"
    && Number.isFinite(target.lng);
}

/** Build the same low-dependency AMap URI used by the legacy hospital action. */
export function buildAmapNavigationUrl(target: AmapNavigationTarget): string | null {
  const name = clean(target.name);
  const address = clean(target.address);
  if (hasCoordinates(target)) {
    const destination = [target.lng, target.lat, name].filter((value) => value !== "").join(",");
    const params = new URLSearchParams({
      to: destination,
      mode: "car",
      policy: "1",
      callnative: "0",
    });
    return `https://uri.amap.com/navigation?${params.toString()}`;
  }
  if (!name && !address) return null;
  return `https://www.amap.com/search?query=${encodeURIComponent([name, address].filter(Boolean).join(" "))}`;
}

/** Open AMap without embedding an SDK or requiring a project API key. */
export function openAmapNavigation(target: AmapNavigationTarget): string | null {
  const url = buildAmapNavigationUrl(target);
  if (!url) return null;
  window.open(url, "_blank", "noopener,noreferrer");
  return url;
}
