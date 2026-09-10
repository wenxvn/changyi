# Safety-first 发布边界计划

状态：已完成

## 目标

把 Safety Gate 之后的疾病候选/模型预测/追问降级和公共 payload 发布逻辑提取为无 Flask 依赖的 triage domain 函数，保持现有 v1 急症与信息不足输出字段、文案和人工复核语义不变。

## 非目标

- 不修改红旗规则、四态判定、模型推理、阈值或 Safety Evaluation 口径。
- 不改变 legacy `/api/*` 输出；只复用当前 v1 safety-first 发布调用。
- 不新增诊断、处方、急救指令或实时医疗承诺。

## 步骤

- [x] 新增 triage safety-first publication 纯函数。
- [x] 用显式 htriage payload builder 接入 `app.py` 的 v1 发布与推荐路径。
- [x] 增加 EMERGENCY、INSUFFICIENT_INFORMATION 和普通状态的发布测试。
- [x] 更新进度、历史、复核、状态、架构、Safety Card 和风险记录。

## 验收与回滚

- 急症仍隐藏疾病候选和普通追问，保留急诊行动、红旗和免责声明。
- 信息不足仍隐藏疾病候选并保留人工复核路径；普通状态 payload 不变。
- 全量 pytest、API 烟雾、Safety Eval、数据校验、编译检查和快照检查通过。
- 回滚方式：恢复 `app.py` 内联发布函数并移除本切片模块、测试和记录。

## 验证记录

- 目标回归：Safety publication、Safety Gate、候选和推荐相关测试 22/22 通过。
- 全量验证结果已记录在 `docs/progress/2026-09-10-safety-publication-boundary.md`。

## 风险

这是 L3 安全相关的行为保持重构。发布逻辑只消费 Safety Gate decision，不重新实现医学规则；已知 Safety Evaluation 缺口继续保留为 review_required，不因本切片视为修复。
