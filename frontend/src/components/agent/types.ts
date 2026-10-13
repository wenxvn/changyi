export type AgentStage =
  | "idle"
  | "composing"
  | "submitting"
  | "waiting"
  | "result_ready"
  | "needs_followup"
  | "emergency"
  | "error";

export const AGENT_STAGE_LABEL: Record<AgentStage, string> = {
  idle: "就医路径助手已准备好",
  composing: "正在接收你的文字输入",
  submitting: "正在提交描述",
  waiting: "请求已发出，正在等待系统响应",
  result_ready: "系统已返回安全状态和下一步",
  needs_followup: "系统需要补充一项信息",
  emergency: "紧急提示已返回，请优先查看安全行动",
  error: "请求未完成，请查看错误提示后重试",
};
