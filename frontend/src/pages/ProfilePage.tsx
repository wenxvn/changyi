import { useEffect, useState } from "react";
import { ArrowLeft, Check, CircleUserRound, Clock3, History, ShieldCheck, Trash2 } from "lucide-react";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import {
  DEMO_PROFILE_EVENT,
  clearHistory,
  readDemoProfile,
  readHistory,
  setHistoryEnabled,
  type DemoHistoryItem,
  type DemoProfile,
} from "../state/demoProfile";

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "时间未登记";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function statusTone(status: DemoHistoryItem["triageStatus"]): "neutral" | "success" | "warning" | "danger" {
  if (status === "EMERGENCY") return "danger";
  if (status === "URGENT") return "warning";
  if (status === "ROUTINE") return "success";
  return "neutral";
}

function statusLabel(status: DemoHistoryItem["triageStatus"]): string {
  return {
    EMERGENCY: "紧急评估",
    URGENT: "尽快评估",
    ROUTINE: "常规路径",
    INSUFFICIENT_INFORMATION: "信息不足",
  }[status];
}

function HistoryRow({ item }: { item: DemoHistoryItem }) {
  return (
    <li className="profile-history__item">
      <div className="profile-history__item-icon" aria-hidden="true"><Clock3 size={16} strokeWidth={1.6} /></div>
      <div className="profile-history__item-body">
        <div className="profile-history__item-topline">
          <strong>{item.triageLabel}</strong>
          <StatusPill tone={statusTone(item.triageStatus)}>{statusLabel(item.triageStatus)}</StatusPill>
        </div>
        <span>{item.matchedDepartment ? `匹配科室：${item.matchedDepartment}` : "未返回匹配科室"}</span>
      </div>
      <time dateTime={item.createdAt}>{formatTime(item.createdAt)}</time>
    </li>
  );
}

export function ProfilePage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const [profile, setProfile] = useState<DemoProfile>(() => readDemoProfile());
  const [history, setHistory] = useState<DemoHistoryItem[]>(() => readHistory());
  const [clearPending, setClearPending] = useState(false);

  useEffect(() => {
    const refresh = () => {
      setProfile(readDemoProfile());
      setHistory(readHistory());
      setClearPending(false);
    };
    window.addEventListener(DEMO_PROFILE_EVENT, refresh);
    return () => window.removeEventListener(DEMO_PROFILE_EVENT, refresh);
  }, []);

  function handleToggle(enabled: boolean) {
    setProfile(setHistoryEnabled(enabled));
  }

  function handleClear() {
    if (!clearPending) {
      setClearPending(true);
      return;
    }
    clearHistory();
    setHistory([]);
    setClearPending(false);
  }

  return (
    <section className="profile-page page-container">
      <button className="back-link" type="button" onClick={() => onNavigate("/")}>
        <ArrowLeft size={15} aria-hidden="true" /> 返回首页
      </button>

      <div className="profile-page__hero">
        <div>
          <span className="eyebrow">本地偏好 · 最近分析</span>
          <h1>把这次体验，<br /><em>留在你的浏览器里。</em></h1>
          <p>这里可以管理常州示范区的本地偏好与最近分析，不需要登录，也不建立真实用户身份。</p>
        </div>
        <div className="profile-page__identity" aria-label="本地偏好">
          <div className="profile-page__identity-icon"><CircleUserRound size={29} strokeWidth={1.35} aria-hidden="true" /></div>
          <strong>常州本地访客</strong>
          <span>服务区域 · 320400</span>
          <StatusPill tone="neutral">仅保存在本机</StatusPill>
        </div>
      </div>

      <div className="profile-page__notice" role="note">
        <ShieldCheck size={18} aria-hidden="true" />
        <div><strong>隐私边界先说清楚</strong><span>所有历史仅保存在当前浏览器。系统不会在这里保存原始描述、追问答案、姓名、联系方式或账号信息。</span></div>
      </div>

      <div className="profile-page__grid">
        <section className="profile-card profile-card--settings" aria-labelledby="profile-settings-title">
          <div className="profile-card__heading">
            <div><span className="eyebrow">01 · 本地偏好</span><h2 id="profile-settings-title">只记录你主动开启的摘要</h2></div>
            <Check size={19} aria-hidden="true" />
          </div>
          <label className="profile-toggle">
            <span><strong>记录最近分析</strong><small>最多保留 8 条分诊状态摘要，不包含原始输入。</small></span>
            <input type="checkbox" checked={profile.historyEnabled} onChange={(event) => handleToggle(event.target.checked)} />
          </label>
          <p className="profile-card__footnote">关闭后不会新增记录；已有摘要会保留到你手动清除，或由浏览器清理。</p>
        </section>

        <section className="profile-card profile-card--history" aria-labelledby="profile-history-title">
          <div className="profile-card__heading">
            <div><span className="eyebrow">02 · 最近分析</span><h2 id="profile-history-title">最近分析</h2></div>
            <History size={19} aria-hidden="true" />
          </div>
          {history.length > 0 ? (
            <>
              <ul className="profile-history">{history.map((item) => <HistoryRow item={item} key={item.id} />)}</ul>
              <div className="profile-history__actions">
                {clearPending ? <span>确定清除这些本地摘要？</span> : <span>摘要不等于病历，也不能恢复完整会话。</span>}
                <button className="profile-clear-button" type="button" onClick={handleClear}>
                  <Trash2 size={14} aria-hidden="true" /> {clearPending ? "确认清除" : "清除历史"}
                </button>
                {clearPending ? <button className="profile-cancel-button" type="button" onClick={() => setClearPending(false)}>取消</button> : null}
              </div>
            </>
          ) : (
            <div className="profile-history__empty">
              <History size={20} aria-hidden="true" />
              <strong>还没有本地分析摘要</strong>
              <span>开启上方开关并完成一次分析后，这里只会显示状态级摘要。</span>
              <Button variant="secondary" onClick={() => onNavigate("/triage")} icon={<ArrowLeft size={15} aria-hidden="true" />}>去体验智能就医</Button>
            </div>
          )}
        </section>
      </div>

      <p className="profile-page__footer-note">本页面用于管理本地偏好与历史边界，不代表登录、医疗档案、诊断记录或专业医疗建议。</p>
    </section>
  );
}
