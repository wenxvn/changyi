import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export type LocationSource = "unknown" | "geolocation" | "district";

export interface LocationState {
  source: LocationSource;
  district: string | null;
  lat: number | null;
  lng: number | null;
  message: string;
  error: string | null;
  requesting: boolean;
}

export const CHANGZHOU_DISTRICTS = [
  { code: "320402", name: "天宁区", lat: 31.776, lng: 119.96 },
  { code: "320404", name: "钟楼区", lat: 31.785, lng: 119.945 },
  { code: "320412", name: "武进区", lat: 31.73, lng: 119.95 },
  { code: "320411", name: "新北区", lat: 31.82, lng: 119.97 },
  { code: "320413", name: "金坛区", lat: 31.72, lng: 119.58 },
  { code: "320481", name: "溧阳市", lat: 31.41, lng: 119.48 },
  { code: "320452", name: "经开区", lat: 31.724, lng: 120.058 },
] as const;

const UNKNOWN_LOCATION: LocationState = {
  source: "unknown",
  district: null,
  lat: null,
  lng: null,
  message: "未使用用户位置；距离和交通可达性不会影响推荐排序。",
  error: null,
  requesting: false,
};

interface LocationContextValue {
  location: LocationState;
  chooseDistrict: (district: string) => void;
  requestPreciseLocation: () => void;
  clearLocation: () => void;
}

const LocationContext = createContext<LocationContextValue | null>(null);

export function LocationProvider({ children }: { children: ReactNode }) {
  const [location, setLocation] = useState<LocationState>(UNKNOWN_LOCATION);

  const value = useMemo<LocationContextValue>(() => ({
    location,
    chooseDistrict: (district) => {
      const selected = CHANGZHOU_DISTRICTS.find((item) => item.name === district);
      if (!selected) {
        setLocation(UNKNOWN_LOCATION);
        return;
      }
      setLocation({
        source: "district",
        district: selected.name,
        lat: selected.lat,
        lng: selected.lng,
        message: `已选择${selected.name}；地图和距离使用该区域参考点估算，不代表你的精确位置。`,
        error: null,
        requesting: false,
      });
    },
    requestPreciseLocation: () => {
      if (!navigator.geolocation) {
        setLocation({ ...UNKNOWN_LOCATION, error: "当前浏览器不支持定位，请选择所在区域。" });
        return;
      }
      setLocation((current) => ({ ...current, requesting: true, error: null, message: "正在请求本次会话的精确位置…" }));
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            source: "geolocation",
            district: null,
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            message: "已获得本次会话的精确位置；不会保存到本地。",
            error: null,
            requesting: false,
          });
        },
        (error) => {
          const message = error.code === error.PERMISSION_DENIED
            ? "你拒绝了定位权限；可以选择所在区域，或继续不提供位置。"
            : "这次没有获得定位；可以选择所在区域，或继续不提供位置。";
          setLocation({ ...UNKNOWN_LOCATION, error: message });
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 },
      );
    },
    clearLocation: () => setLocation(UNKNOWN_LOCATION),
  }), [location]);

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}

export function useLocationContext(): LocationContextValue {
  const context = useContext(LocationContext);
  if (!context) throw new Error("useLocationContext must be used inside LocationProvider");
  return context;
}
