import {
  ArrowRight,
  ClipboardList,
  FileSearch,
  Hospital,
  MessageCircleMore,
  ShieldAlert,
  Stethoscope,
} from "lucide-react";

export interface JourneyStep {
  number: string;
  title: string;
  description: string;
  preview: string;
}

export const journeySteps: JourneyStep[] = [
  {
    number: "01",
    title: "理解自然语言",
    description: "把你正在经历的不适，整理成系统可以继续理解的线索。",
    preview: "最近两天胸口有点闷，走快以后更明显……",
  },
  {
    number: "02",
    title: "Safety Gate",
    description: "先检查需要优先关注的危险信号，再进入普通资源匹配。",
    preview: "安全状态 · 正在读取当前描述",
  },
  {
    number: "03",
    title: "就医方向路由",
    description: "Direct Department：从症状线索整理科室方向；信息不足时不硬给答案。",
    preview: "选择性拒答 · 暂不强行给出科室方向",
  },
  {
    number: "04",
    title: "自适应追问",
    description: "Adaptive Inquiry：信息不足时一次只问一个关键问题，回答后路径重算。",
    preview: "这个症状大概持续多久了？",
  },
  {
    number: "05",
    title: "多目标资源路由",
    description: "把科室方向与距离、专科匹配、连续复诊等偏好放回常州资源。",
    preview: "医院 · 医生 · 可达性 · 偏好可调",
  },
  {
    number: "06",
    title: "解释与导航",
    description: "解释为什么排在前面，并衔接地图与高德导航完成到院闭环。",
    preview: "推荐依据 · 地图 · 高德导航",
  },
];

const previewIcons = [
  MessageCircleMore,
  ShieldAlert,
  ClipboardList,
  Stethoscope,
  Hospital,
  FileSearch,
];

interface JourneyPreviewProps {
  step: JourneyStep;
}

export function JourneyPreview({ step }: JourneyPreviewProps) {
  const Icon = previewIcons[Number(step.number) - 1] ?? ArrowRight;
  return (
    <div className="journey-preview" aria-live="polite">
      <div className="journey-preview__topline">
        <span className="eyebrow eyebrow--muted">路径预览</span>
        <span className="journey-preview__index">第 {step.number} 步 / 共 06 步</span>
      </div>
      <div className="journey-preview__stage">
        <div className="journey-preview__halo" />
        <div className="journey-preview__icon"><Icon size={23} strokeWidth={1.5} aria-hidden="true" /></div>
        <div className="journey-preview__line" />
        <div className="journey-preview__copy">
          <span className="journey-preview__label">当前理解</span>
          <strong>{step.preview}</strong>
          <span className="journey-preview__note">系统会根据当前信息继续推进</span>
        </div>
      </div>
      <div className="journey-preview__footer">
        <span>从描述到路径</span>
        <ArrowRight size={16} strokeWidth={1.7} aria-hidden="true" />
      </div>
    </div>
  );
}
