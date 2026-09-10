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
    title: "先过安全门",
    description: "先检查需要优先关注的信号，再进入普通资源匹配。",
    preview: "Safety Gate · 等待后端评估",
  },
  {
    number: "03",
    title: "补足关键信息",
    description: "当信息不足时，一次只问一个更有帮助的问题。",
    preview: "这个症状大概持续多久了？",
  },
  {
    number: "04",
    title: "找到就医方向",
    description: "从症状线索到科室方向，给出可理解的下一步。",
    preview: "就医方向 · 呼吸与危重症医学科",
  },
  {
    number: "05",
    title: "匹配城市资源",
    description: "把科室方向放回常州的医院、医生与到院路径中。",
    preview: "医疗资源 · 医院 · 医生 · 交通",
  },
  {
    number: "06",
    title: "解释推荐依据",
    description: "把输入事实、数据事实和系统推断分开说明。",
    preview: "推荐依据 · 专科匹配 · 可达性 · 公开专长",
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
        <span className="eyebrow eyebrow--muted">PRODUCT PREVIEW</span>
        <span className="journey-preview__index">{step.number} / 06</span>
      </div>
      <div className="journey-preview__stage">
        <div className="journey-preview__halo" />
        <div className="journey-preview__icon"><Icon size={23} strokeWidth={1.5} aria-hidden="true" /></div>
        <div className="journey-preview__line" />
        <div className="journey-preview__copy">
          <span className="journey-preview__label">CURRENT UNDERSTANDING</span>
          <strong>{step.preview}</strong>
          <span className="journey-preview__note">系统将依据后端返回继续推进</span>
        </div>
      </div>
      <div className="journey-preview__footer">
        <span>从描述到路径</span>
        <ArrowRight size={16} strokeWidth={1.7} aria-hidden="true" />
      </div>
    </div>
  );
}
