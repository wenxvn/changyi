import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowRight,
  CircleUserRound,
  Hospital,
  MapPinned,
  Menu,
  ShieldCheck,
  X,
} from "lucide-react";
import { HomePage } from "../pages/HomePage";
import { TriagePage } from "../pages/TriagePage";
import { ResourcesPage } from "../pages/ResourcesPage";
import { TrustPage } from "../pages/TrustPage";
import { MapPage } from "../pages/MapPage";
import { ProfilePage } from "../pages/ProfilePage";
import { BrandMark } from "../components/ui/BrandMark";
import { Button } from "../components/ui/Button";
import { CoverScreen } from "../components/cover/CoverScreen";
import { LocationProvider } from "../state/locationContext";

type AppRoute = "home" | "triage" | "resources" | "map" | "trust" | "profile";

const navItems: Array<{ route: AppRoute; label: string; path: string }> = [
  { route: "triage", label: "智能就医", path: "/triage" },
  { route: "resources", label: "医疗资源", path: "/resources" },
  { route: "map", label: "就医地图", path: "/map" },
  { route: "trust", label: "可信 AI", path: "/trust" },
];

function routeFromLocation(): AppRoute {
  const path = window.location.pathname;
  if (path.startsWith("/triage")) return "triage";
  if (path.startsWith("/resources")) return "resources";
  if (path.startsWith("/map")) return "map";
  if (path.startsWith("/trust")) return "trust";
  if (path.startsWith("/profile")) return "profile";
  return "home";
}

function pathForRoute(route: AppRoute): string {
  return route === "home" ? "/" : `/${route}`;
}

function scrubConditionFromUrl() {
  const params = new URLSearchParams(window.location.search);
  if (!params.has("condition")) return;
  params.delete("condition");
  const query = params.toString();
  const safePath = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
  window.history.replaceState(window.history.state, "", safePath);
}

function AppShell({
  route,
  onNavigate,
  children,
  inert = false,
}: {
  route: AppRoute;
  onNavigate: (path: string) => void;
  children: ReactNode;
  inert?: boolean;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigate = (path: string) => {
    setMobileOpen(false);
    onNavigate(path);
  };

  return (
    <div className="app-shell" inert={inert || undefined}>
      <a className="skip-link" href="#main-content">跳转到主要内容</a>
      <header className="site-header">
        <button className="brand-lockup" type="button" onClick={() => navigate("/")} aria-label="返回常医智导首页">
          <BrandMark />
          <span className="brand-lockup__copy">
            <strong>常医智导</strong>
            <small>Care Intelligence</small>
          </span>
        </button>

        <nav id="primary-navigation" className={`site-nav${mobileOpen ? " site-nav--open" : ""}`} aria-label="主导航">
          {navItems.map((item) => (
            <button
              type="button"
              className={`site-nav__item${route === item.route ? " site-nav__item--active" : ""}`}
              key={item.route}
              onClick={() => navigate(item.path)}
              aria-current={route === item.route ? "page" : undefined}
            >
              {item.label}
            </button>
          ))}
          <Button
            className="site-nav__cta"
            onClick={() => navigate("/triage")}
            icon={<ArrowRight size={16} strokeWidth={1.8} aria-hidden="true" />}
          >
            开始智能分诊
          </Button>
        </nav>

        <div className="site-header__actions">
          <span className="region-mark"><span /> 常州 · 320400</span>
          <button
            className={`profile-button${route === "profile" ? " profile-button--active" : ""}`}
            type="button"
            onClick={() => navigate("/profile")}
            aria-label="打开本地偏好"
            title="本地偏好"
            aria-current={route === "profile" ? "page" : undefined}
          >
            <CircleUserRound size={20} strokeWidth={1.6} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="mobile-menu-button"
            onClick={() => setMobileOpen((value) => !value)}
            aria-expanded={mobileOpen}
            aria-controls="primary-navigation"
            aria-label={mobileOpen ? "关闭导航" : "打开导航"}
          >
            {mobileOpen ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
          </button>
        </div>
      </header>
      <main id="main-content" tabIndex={-1}>
        <div key={route} className="page-view">
          {children}
        </div>
      </main>
      <footer className="site-footer">
        <div className="site-footer__row">
          <div className="site-footer__brand">
            <BrandMark compact />
            <span>常医智导</span>
          </div>
          <div className="site-footer__links">
            <button type="button" onClick={() => navigate("/trust")}><ShieldCheck size={14} aria-hidden="true" /> 可信 AI</button>
            <button type="button" onClick={() => navigate("/resources")}><Hospital size={14} aria-hidden="true" /> 医疗资源</button>
            <button type="button" onClick={() => navigate("/map")}><MapPinned size={14} aria-hidden="true" /> 就医地图</button>
          </div>
        </div>
        <small>面向常州服务区域的就医方向与资源信息参考，不替代医生诊断、急救或处方。</small>
      </footer>
    </div>
  );
}

export function App() {
  const [route, setRoute] = useState<AppRoute>(routeFromLocation);
  const [initialSubmission, setInitialSubmission] = useState<{ id: number; condition: string } | null>(null);
  const [cover, setCover] = useState<"open" | "leaving" | "closed">(() =>
    routeFromLocation() === "home" ? "open" : "closed",
  );
  const submissionSequence = useRef(0);

  // The cover only exists for the first paint of "/": leaving it is a one-way
  // transition, and an in-app return to home never replays it.
  const dismissCover = () => setCover((current) => (current === "open" ? "leaving" : current));

  useEffect(() => {
    if (cover !== "leaving") return;
    const timer = window.setTimeout(() => {
      setCover("closed");
      document.getElementById("main-content")?.focus({ preventScroll: true });
    }, 460);
    return () => window.clearTimeout(timer);
  }, [cover]);

  useEffect(() => {
    const handlePopState = () => {
      scrubConditionFromUrl();
      setInitialSubmission(null);
      setRoute(routeFromLocation());
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useLayoutEffect(() => { scrubConditionFromUrl(); }, []);

  const navigate = (path: string) => {
    if (!path.startsWith("/triage")) setInitialSubmission(null);
    window.history.pushState({}, "", path);
    setRoute(routeFromLocation());
    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
    window.scrollTo({ top: 0, behavior });
  };

  const startTriageFromHome = (condition: string) => {
    setInitialSubmission({ id: ++submissionSequence.current, condition });
    window.history.pushState({}, "", "/triage");
    setRoute("triage");
    window.scrollTo({ top: 0, behavior: "auto" });
  };

  const content = route === "home" ? (
    <HomePage
      onStart={startTriageFromHome}
      onNavigate={navigate}
    />
  ) : route === "triage" ? (
    <TriagePage onNavigate={navigate} initialSubmission={initialSubmission} />
  ) : route === "resources" ? (
    <ResourcesPage onNavigate={navigate} />
  ) : route === "trust" ? (
    <TrustPage onNavigate={navigate} />
  ) : route === "map" ? (
    <MapPage />
  ) : route === "profile" ? (
    <ProfilePage onNavigate={navigate} />
  ) : null;

  const coverOpen = cover !== "closed";

  return (
    <LocationProvider>
      <AppShell route={route} onNavigate={navigate} inert={coverOpen}>
        {content}
      </AppShell>
      {coverOpen ? (
        <CoverScreen leaving={cover === "leaving"} onEnter={dismissCover} />
      ) : null}
    </LocationProvider>
  );
}
