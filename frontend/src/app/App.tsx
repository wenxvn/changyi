import { useEffect, useState, type ReactNode } from "react";
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
import { BrandMark } from "../components/ui/BrandMark";
import { Button } from "../components/ui/Button";

type AppRoute = "home" | "triage" | "resources" | "map" | "trust";

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
  return "home";
}

function pathForRoute(route: AppRoute): string {
  return route === "home" ? "/" : `/${route}`;
}

function AppShell({
  route,
  onNavigate,
  children,
}: {
  route: AppRoute;
  onNavigate: (path: string) => void;
  children: ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigate = (path: string) => {
    setMobileOpen(false);
    onNavigate(path);
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <button className="brand-lockup" onClick={() => navigate("/")} aria-label="返回常医智导首页">
          <BrandMark />
          <span className="brand-lockup__copy">
            <strong>常医智导</strong>
            <small>Care Intelligence</small>
          </span>
        </button>

        <nav className={`site-nav${mobileOpen ? " site-nav--open" : ""}`} aria-label="主导航">
          {navItems.map((item) => (
            <button
              className={`site-nav__item${route === item.route ? " site-nav__item--active" : ""}`}
              key={item.route}
              onClick={() => navigate(item.path)}
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
          <button className="profile-button" aria-label="本地演示资料" title="本地演示资料">
            <CircleUserRound size={20} strokeWidth={1.6} aria-hidden="true" />
          </button>
          <button
            className="mobile-menu-button"
            onClick={() => setMobileOpen((value) => !value)}
            aria-expanded={mobileOpen}
            aria-label={mobileOpen ? "关闭导航" : "打开导航"}
          >
            {mobileOpen ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
          </button>
        </div>
      </header>
      <main>{children}</main>
      <footer className="site-footer">
        <div className="site-footer__brand">
          <BrandMark compact />
          <span>常医智导</span>
        </div>
        <p>面向常州示范区的可信智能就医决策辅助体验。</p>
        <div className="site-footer__links">
          <button onClick={() => navigate("/trust")}><ShieldCheck size={14} aria-hidden="true" /> 可信 AI</button>
          <button onClick={() => navigate("/resources")}><Hospital size={14} aria-hidden="true" /> 医疗资源</button>
          <button onClick={() => navigate("/map")}><MapPinned size={14} aria-hidden="true" /> 就医地图</button>
        </div>
        <small>本系统提供就医方向与资源信息参考，不替代医生诊断、急救或处方。</small>
      </footer>
    </div>
  );
}

function PlaceholderPage({ route, onNavigate }: { route: AppRoute; onNavigate: (path: string) => void }) {
  const details = {
    resources: {
      eyebrow: "RESOURCE LAYER",
      title: "把城市资源，放回你的就医路径。",
      text: "医院、科室与医生资源页正在接入新的可解释检索体验。",
      icon: Hospital,
    },
    map: {
      eyebrow: "CITY LAYER",
      title: "从地图上，看见更实际的到院选择。",
      text: "地图与资源列表同步能力将在下一切片接入。",
      icon: MapPinned,
    },
    trust: {
      eyebrow: "TRUST LAYER",
      title: "AI 应该知道，什么时候不该给出答案。",
      text: "安全评估、数据来源与版本证据正在汇入可信 AI 中心。",
      icon: ShieldCheck,
    },
  } as const;
  const content = details[route as keyof typeof details] ?? details.trust;
  const Icon = content.icon;
  return (
    <section className="placeholder-page page-container">
      <div className="placeholder-page__icon"><Icon size={24} strokeWidth={1.5} aria-hidden="true" /></div>
      <span className="eyebrow">{content.eyebrow}</span>
      <h1>{content.title}</h1>
      <p>{content.text}</p>
      <Button onClick={() => onNavigate("/")} variant="secondary" icon={<ArrowRight size={16} aria-hidden="true" />}>
        返回首页
      </Button>
    </section>
  );
}

export function App() {
  const [route, setRoute] = useState<AppRoute>(routeFromLocation);

  useEffect(() => {
    const handlePopState = () => setRoute(routeFromLocation());
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, "", path);
    setRoute(routeFromLocation());
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const content = route === "home" ? (
    <HomePage
      onStart={(condition) => navigate(`/triage?condition=${encodeURIComponent(condition)}`)}
      onNavigate={navigate}
    />
  ) : route === "triage" ? (
    <TriagePage onNavigate={navigate} />
  ) : route === "resources" ? (
    <ResourcesPage onNavigate={navigate} />
  ) : route === "trust" ? (
    <TrustPage onNavigate={navigate} />
  ) : route === "map" ? (
    <MapPage />
  ) : (
    <PlaceholderPage route={route} onNavigate={navigate} />
  );

  return <AppShell route={route} onNavigate={navigate}>{content}</AppShell>;
}
