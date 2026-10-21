import { useCallback, useEffect, useRef } from "react";
import { ArrowRight, Compass, MapPinned, ShieldCheck } from "lucide-react";
import { BrandMark } from "../ui/BrandMark";

interface CoverScreenProps {
  /** True while the cover is fading out; it stops receiving pointer events immediately. */
  leaving: boolean;
  /** Called on the first click, key press or explicit enter action. */
  onEnter: () => void;
}

const pillars = [
  {
    icon: ShieldCheck,
    title: "安全优先",
    text: "红旗症状先于任何医院与医生排序。",
  },
  {
    icon: Compass,
    title: "方向可解释",
    text: "每个就医方向都给出依据与不确定之处。",
  },
  {
    icon: MapPinned,
    title: "城市可达",
    text: "把常州的距离与到院成本一起纳入参考。",
  },
];

/**
 * Big-screen entry surface for the home route. It is a single dismissable
 * layer: click anywhere, press Enter/Space/Escape, or use the visible enter
 * button to reveal the existing product UI underneath. It never reads or
 * writes medical state and owns no data fetching.
 */
export function CoverScreen({ leaving, onEnter }: CoverScreenProps) {
  const enterRef = useRef<HTMLButtonElement | null>(null);
  const entered = useRef(false);

  const enter = useCallback(() => {
    if (entered.current) return;
    entered.current = true;
    onEnter();
  }, [onEnter]);

  useEffect(() => {
    enterRef.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Enter" || event.key === " " || event.key === "Spacebar" || event.key === "Escape") {
        event.preventDefault();
        enter();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enter]);

  return (
    <div
      className={`cover${leaving ? " cover--leaving" : ""}`}
      data-testid="cover-screen"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cover-title"
      aria-describedby="cover-lede"
      onClick={enter}
    >
      <div className="cover__aurora" aria-hidden="true" />
      <div className="cover__grid" aria-hidden="true" />
      <div className="cover__beam" aria-hidden="true" />

      <div className="cover__frame">
        <header className="cover__top">
          <span className="cover__brand">
            <BrandMark />
            <span className="cover__brand-copy">
              <strong>常医智导</strong>
              <small>Care Intelligence</small>
            </span>
          </span>
          <span className="cover__region"><span className="cover__region-dot" /> 常州 · 320400</span>
        </header>

        <div className="cover__core">
          <p className="cover__eyebrow">可信智能就医 · 常州服务区域</p>
          <h1 className="cover__title" id="cover-title">常医智导</h1>
          <p className="cover__lede" id="cover-lede">
            一句话说清不舒服，先看<em>安全</em>，再看<em>方向</em>，最后看<em>怎么到</em>。
          </p>

          <ul className="cover__pillars">
            {pillars.map((pillar) => (
              <li key={pillar.title}>
                <pillar.icon size={18} strokeWidth={1.5} aria-hidden="true" />
                <strong>{pillar.title}</strong>
                <span>{pillar.text}</span>
              </li>
            ))}
          </ul>
        </div>

        <footer className="cover__foot">
          <button
            type="button"
            className="cover__enter"
            ref={enterRef}
            onClick={enter}
          >
            <span className="cover__enter-ring" aria-hidden="true" />
            <span>点击任意处进入</span>
            <ArrowRight size={18} strokeWidth={1.8} aria-hidden="true" />
          </button>
          <p className="cover__notice">
            提供就医方向与公开资源参考，不替代医生诊断、急救或处方
          </p>
        </footer>
      </div>
    </div>
  );
}
