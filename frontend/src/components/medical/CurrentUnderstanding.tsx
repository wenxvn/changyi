import { ClipboardList, MapPinned, ShieldCheck, Stethoscope, ArrowRight } from "lucide-react";
import { StatusPill } from "../ui/StatusPill";
import type { FollowupPayload, RecommendationPayload, TriagePayload } from "../../types/api";

interface CurrentUnderstandingProps {
  condition: string;
  result: TriagePayload;
  followup?: FollowupPayload | null;
  recommendations?: RecommendationPayload | null;
  recommendationsLoading?: boolean;
  onNavigate?: (path: string) => void;
}

const statusLabel: Record<TriagePayload["triage_status"], string> = {
  EMERGENCY: "需要优先评估",
  URGENT: "建议尽快评估",
  ROUTINE: "可继续了解路径",
  INSUFFICIENT_INFORMATION: "需要补充信息",
};

const pathNodes = [
  { key: "symptom", label: "症状描述" },
  { key: "safety", label: "安全门" },
  { key: "direction", label: "就医方向" },
  { key: "resources", label: "资源路径" },
] as const;

function pathActiveCount(result: TriagePayload, hasFollowup: boolean, hasRecommendations: boolean): number {
  if (result.triage_status === "EMERGENCY") return 2;
  if (hasFollowup) return 2;
  if (result.matched_department) return hasRecommendations ? 4 : 3;
  return 2;
}

export function CurrentUnderstanding({
  condition,
  result,
  followup,
  recommendations,
  recommendationsLoading,
  onNavigate,
}: CurrentUnderstandingProps) {
  const status = result.triage_status;
  const statusTone = status === "ROUTINE" ? "success" : status === "EMERGENCY" || status === "URGENT" ? "warning" : "neutral";
  const hasFollowup = Boolean(followup?.needed);
  const hasRecommendations = Boolean(recommendations);
  const activeCount = pathActiveCount(result, hasFollowup, hasRecommendations);

  const nextActions: Array<{ icon: typeof ShieldCheck; title: string; detail: string; done?: boolean }> = [];
  if (status === "EMERGENCY") {
    nextActions.push(
      { icon: ShieldCheck, title: "优先急诊 / 急救", detail: "不要继续等待在线推荐。必要时拨打 120。", done: true },
      { icon: MapPinned, title: "查看急诊资源", detail: "在地图上定位附近公开标记含急诊的机构。" },
    );
  } else if (status === "INSUFFICIENT_INFORMATION") {
    nextActions.push(
      { icon: ShieldCheck, title: "安全门已读取", detail: "当前描述不足以支持资源路径。", done: true },
      { icon: ClipboardList, title: "回答补充问题", detail: `还有 ${followup?.questions.length ?? 1} 个问题可完善理解。` },
    );
  } else {
    nextActions.push(
      { icon: ShieldCheck, title: "安全门已读取", detail: status === "URGENT" ? "建议尽快获得专业评估。" : "未提示需要立即急诊。", done: true },
      { icon: Stethoscope, title: "确认就医方向", detail: result.matched_department ? `当前方向：${result.matched_department}` : "继续整理科室方向。", done: Boolean(result.matched_department) },
      { icon: MapPinned, title: "匹配城市资源", detail: hasRecommendations ? "已加载医院与医生路径。" : recommendationsLoading ? "正在读取资源…" : "查看医院、医生与导航入口。", done: hasRecommendations },
    );
  }

  return (
    <aside className="current-understanding" aria-labelledby="understanding-title">
      <div className="current-understanding__header">
        <span className="eyebrow" id="understanding-title"><ClipboardList size={14} aria-hidden="true" /> 当前理解</span>
        <StatusPill tone={statusTone}>{statusLabel[status]}</StatusPill>
      </div>
      <div className="current-understanding__quote">“{condition}”</div>
      <dl className="understanding-facts">
        <div>
          <dt>安全门状态</dt>
          <dd>{statusLabel[status]}</dd>
        </div>
        {result.matched_department ? (
          <div>
            <dt>返回的就医方向</dt>
            <dd>{result.matched_department}</dd>
          </div>
        ) : null}
        {hasFollowup ? (
          <div>
            <dt>下一步</dt>
            <dd>系统建议补足 {followup?.questions.length ?? 0} 个问题</dd>
          </div>
        ) : null}
      </dl>

      <div className="understanding-path" aria-label="就医路径进度">
        {pathNodes.map((node, index) => {
          const reached = index < activeCount;
          const current = index === activeCount - 1;
          return (
            <div
              key={node.key}
              className={`understanding-path__node${reached ? " is-reached" : ""}${current ? " is-current" : ""}`}
            >
              <span className="understanding-path__dot" aria-hidden="true" />
              <span>{node.label}</span>
            </div>
          );
        })}
      </div>

      <div className="understanding-next">
        <span className="eyebrow eyebrow--muted">接下来</span>
        <ul>
          {nextActions.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.title} className={item.done ? "is-done" : ""}>
                <Icon size={15} aria-hidden="true" />
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.detail}</span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {onNavigate && status !== "EMERGENCY" ? (
        <button className="understanding-jump" type="button" onClick={() => onNavigate("/resources")}>
          浏览全部医疗资源 <ArrowRight size={14} aria-hidden="true" />
        </button>
      ) : null}

      <p className="current-understanding__notice"><ShieldCheck size={15} aria-hidden="true" /> 这是系统对当前输入的辅助整理，不是诊断结论。</p>
    </aside>
  );
}
