import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleAlert,
  Database,
  MapPinned,
  Mic2,
  MoveUpRight,
  Network,
  ShieldCheck,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import { CarePath } from "../components/visualization/CarePath";
import { JourneyPreview, journeySteps } from "../components/visualization/JourneyPreview";
import { useCitySummary } from "../hooks/useCitySummary";

interface HomePageProps {
  onStart: (condition: string) => void;
  onNavigate: (path: string) => void;
}

const principles = [
  {
    label: "安全优先",
    title: "先确认安全，再谈推荐。",
    text: "系统首先判断是否存在需要优先处理的危险信号，安全优先于任何医院或医生排序。",
  },
  {
    label: "资源匹配",
    title: "资源要适合当前情况。",
    text: "普通病例不盲目推向高级资源；疑难和重症才提高相应专科与医院能力的优先级。",
  },
  {
    label: "城市可达",
    title: "路径要能真正抵达。",
    text: "推荐不仅考虑医疗方向，也把常州的距离、区域和实际到院成本纳入解释。",
  },
];

function formatMetric(value: number): string {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export function HomePage({ onStart, onNavigate }: HomePageProps) {
  const [condition, setCondition] = useState("");
  const [journeyIndex, setJourneyIndex] = useState(0);
  const journeyTabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const summary = useCitySummary();

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (condition.trim()) onStart(condition.trim());
  };

  const currentJourney = journeySteps[journeyIndex];
  const cityName = summary.data?.region.name ?? "常州";
  const metrics = summary.data?.metrics;

  const focusJourneyStep = (index: number) => {
    setJourneyIndex(index);
    window.requestAnimationFrame(() => journeyTabRefs.current[index]?.focus());
  };

  const handleJourneyKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = (index + 1) % journeySteps.length;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = (index - 1 + journeySteps.length) % journeySteps.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = journeySteps.length - 1;
    if (nextIndex === null) return;
    event.preventDefault();
    focusJourneyStep(nextIndex);
  };

  return (
    <>
      <section className="hero page-container">
        <div className="hero__copy">
          <div className="hero__eyebrow">
            <span className="eyebrow">可信智能就医 · {cityName} 示范区</span>
            <StatusPill tone="success"><span className="status-dot" /> 系统在线</StatusPill>
          </div>
          <h1>
            把症状，<br />
            <em>变成一条更清晰的</em><br />
            就医路径。
          </h1>
          <p className="hero__lede">
            从危险信号识别，到科室、医院、医生与实际到院路径，
            让每一步推荐都有依据。
          </p>

          <form className="symptom-composer" onSubmit={handleSubmit}>
            <label htmlFor="symptom-input" className="symptom-composer__label">从这里开始</label>
            <textarea
              id="symptom-input"
              value={condition}
              onChange={(event) => setCondition(event.target.value)}
              placeholder={"现在有什么不舒服？\n例如：昨天晚上开始右下腹疼，今天越来越明显，还有一点恶心。"}
              rows={3}
              maxLength={2000}
            />
            <div className="symptom-composer__footer">
              <button className="voice-button" type="button" disabled title="语音输入将在后续切片接入">
                <Mic2 size={17} strokeWidth={1.7} aria-hidden="true" />
                <span>语音描述</span>
              </button>
              <Button
                type="submit"
                disabled={!condition.trim()}
                icon={<ArrowRight size={17} strokeWidth={1.8} aria-hidden="true" />}
              >
                开始分析
              </Button>
            </div>
          </form>

          <div className="hero__promise">
            <div><ShieldCheck size={15} aria-hidden="true" /><span>先安全，后推荐</span></div>
            <div><Network size={15} aria-hidden="true" /><span>解释每一步依据</span></div>
            <div><MapPinned size={15} aria-hidden="true" /><span>理解你所在的城市</span></div>
          </div>
        </div>
        <div className="hero__visual">
          <CarePath />
          <div className="hero__visual-note">
            <span>01</span>
            <p>从你的描述出发，逐步建立就医路径。</p>
          </div>
        </div>
      </section>

      <section className="philosophy page-container section-block">
        <div className="section-kicker"><span>01</span><span>我们的方式</span></div>
        <div className="philosophy__grid">
          <h2>我们不是在寻找<br /><em>“最好的医院”。</em><br />而是在寻找<br /><strong>更适合当前情况的<br />就医路径。</strong></h2>
          <div className="principles-list">
            {principles.map((principle, index) => (
              <article className="principle" key={principle.label}>
                <div className="principle__index">0{index + 1}</div>
                <div>
                  <span className="eyebrow eyebrow--muted">{principle.label}</span>
                  <h3>{principle.title}</h3>
                  <p>{principle.text}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="journey section-block">
        <div className="page-container">
          <div className="section-kicker"><span>02</span><span>就医路径</span></div>
          <div className="journey__intro">
            <div>
              <h2>一次只走<br /><em>下一步。</em></h2>
              <p>系统把复杂的就医判断拆成可理解的步骤。滚动查看每一步如何把描述，慢慢变成行动。</p>
            </div>
            <div className="journey__controls" role="tablist" aria-label="AI Journey 步骤">
              {journeySteps.map((step, index) => (
                <button
                  type="button"
                  key={step.number}
                  role="tab"
                  id={`journey-tab-${step.number}`}
                  aria-controls="journey-step-panel"
                  aria-selected={journeyIndex === index}
                  tabIndex={journeyIndex === index ? 0 : -1}
                  ref={(element) => { journeyTabRefs.current[index] = element; }}
                  className={journeyIndex === index ? "is-active" : ""}
                  onClick={() => setJourneyIndex(index)}
                  onKeyDown={(event) => handleJourneyKeyDown(event, index)}
                >
                  <span>{step.number}</span>
                  <span>{step.title}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="journey__stage">
            <div className="journey__steps-list">
              {journeySteps.map((step, index) => (
                <button
                  type="button"
                  className={`journey__step${journeyIndex === index ? " is-active" : ""}`}
                  key={step.number}
                  onClick={() => setJourneyIndex(index)}
                >
                  <span>{step.number}</span>
                  <strong>{step.title}</strong>
                  <ChevronRight size={16} aria-hidden="true" />
                </button>
              ))}
            </div>
            <div
              className="journey__tabpanel"
              id="journey-step-panel"
              role="tabpanel"
              aria-labelledby={`journey-tab-${currentJourney.number}`}
              tabIndex={0}
            >
              <JourneyPreview step={currentJourney} />
            </div>
          </div>
        </div>
      </section>

      <section className="city-layer page-container section-block">
        <div className="section-kicker"><span>03</span><span>常州资源图景</span></div>
        <div className="city-layer__heading">
          <div>
            <h2>AI 不只理解病情，<br /><em>还理解你所在的城市。</em></h2>
            <p>以常州为示范区，把医疗资源和到院路径放进同一张可解释的城市图景里。</p>
          </div>
          <span className="city-layer__code">服务区域<br /><strong>{summary.data?.region.code ?? "320400"}</strong></span>
        </div>
        <div className="city-layer__content">
          <div className="city-map-sketch" aria-label={`${cityName}区域关系示意`} role="img">
            <div className="city-map-sketch__wash city-map-sketch__wash--one" />
            <div className="city-map-sketch__wash city-map-sketch__wash--two" />
            <svg viewBox="0 0 600 420" aria-hidden="true">
              <path className="city-map-sketch__contour" d="M84 328c38-61 35-141 95-183 53-37 91-21 133-62 45-44 94-47 137-20 31 20 50 56 86 69 24 9 47 9 65 29" />
              <path className="city-map-sketch__contour city-map-sketch__contour--soft" d="M42 254c80-26 99-87 166-105 78-22 111 18 172-26 58-42 101-20 170 13" />
              <path className="city-map-sketch__route" d="M110 320 222 236 342 257 438 152 530 101" />
              <path className="city-map-sketch__route city-map-sketch__route--soft" d="M222 236 266 102 438 152" />
              {[
                [110, 320, "南部"],
                [222, 236, "中心"],
                [342, 257, "东部"],
                [438, 152, "新北"],
                [530, 101, "金坛"],
              ].map(([x, y, label]) => (
                <g key={label as string} className="city-map-sketch__node" transform={`translate(${x} ${y})`}>
                  <circle r="7" />
                  <circle className="city-map-sketch__node-ring" r="13" />
                  <text x="14" y="4">{label}</text>
                </g>
              ))}
            </svg>
            <span className="city-map-sketch__caption">常州区域关系示意</span>
          </div>
          <div className="city-metrics">
            <div className="city-metrics__intro">
              <Database size={18} strokeWidth={1.5} aria-hidden="true" />
              <span>数据摘要</span>
              <p>以下数据来自当前已接入的常州医疗与交通资源。</p>
            </div>
            <div className="city-metrics__grid">
              {metrics ? (
                [metrics.hospitals, metrics.doctors, metrics.bus_routes, metrics.districts].map((metric) => (
                  <div className="metric" key={metric.label}>
                    <strong>{formatMetric(metric.value)}</strong>
                    <span>{metric.label}</span>
                    <small>{metric.status === "migration_pending" ? "资料核验中" : "公开来源"}</small>
                  </div>
                ))
              ) : (
                ["医疗机构", "医生公开资料", "公交线路", "城市区域"].map((label) => (
                  <div className="metric metric--loading" key={label}>
                    <strong>—</strong><span>{label}</span><small>{summary.error ? "暂未载入" : "读取中"}</small>
                  </div>
                ))
              )}
            </div>
            {summary.error ? (
              <div className="city-metrics__error" role="status">
                <CircleAlert size={15} aria-hidden="true" />
                <span>城市摘要暂时无法载入。</span>
                <button type="button" onClick={summary.retry}>重试</button>
              </div>
            ) : null}
            <div className="city-metrics__source">
              <span>当前区域</span>
              <strong>{summary.data?.region.code ? `${summary.data.region.name} ${summary.data.region.code}` : "常州服务区域"}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="trust-section section-block">
        <div className="page-container trust-section__inner">
          <div className="trust-section__visual" aria-hidden="true">
            <div className="trust-section__ring trust-section__ring--outer" />
            <div className="trust-section__ring trust-section__ring--inner" />
            <ShieldCheck size={39} strokeWidth={1.25} />
            <span>可信<br />设计</span>
          </div>
          <div className="trust-section__copy">
            <div className="section-kicker section-kicker--light"><span>04</span><span>可信信息</span></div>
            <h2>AI 应该知道<br /><em>什么时候不该给出答案。</em></h2>
            <p>安全分诊、低置信度降级、数据来源和推荐解释，应该成为产品的一部分，而不是藏在技术说明里。</p>
            <Button onClick={() => onNavigate("/trust")} variant="secondary" icon={<MoveUpRight size={16} aria-hidden="true" />}>
              了解系统如何做出判断
            </Button>
            <div className="trust-section__notes">
              <span><Check size={14} aria-hidden="true" /> 安全门优先</span>
              <span><Check size={14} aria-hidden="true" /> 来源可追溯</span>
              <span><Check size={14} aria-hidden="true" /> 版本可复核</span>
            </div>
          </div>
        </div>
      </section>

      <section className="home-cta page-container">
        <div>
          <span className="eyebrow eyebrow--muted">随时开始</span>
          <h2>从一句话开始，<br /><em>让下一步更清楚。</em></h2>
        </div>
        <Button onClick={() => document.getElementById("symptom-input")?.focus()} icon={<ArrowRight size={17} aria-hidden="true" />}>
          描述现在的不适
        </Button>
      </section>
    </>
  );
}
