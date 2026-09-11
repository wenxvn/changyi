# 常医后端重构计划：疾病预测 Application Service 边界

状态：已完成  
日期：2026-09-11  
变更等级：L3（模型输出边界；只做行为保持式编排）

## 目标

将旧 `/api/predict-disease` 的模型结果判定和详情标签 enrichment 移入独立 application service，让 HTTP handler 只负责输入字段选择、状态码/错误映射和响应 envelope。

## 非目标

- 不修改模型文件、训练数据、推理算法、阈值、疾病名称、症状标准化或医学文案。
- 不把模型预测包装成诊断，不调整 v1 Safety-first triage/recommendation 的发布策略。
- 不改变旧 URL、请求字段、成功/400/503 状态码或 response shape。

## 安全验收边界

- `available=false` 仍映射为 503；可用但没有疾病结果仍映射为“症状信息不足”400；详情标签只在可用且有结果时生成。
- 模型结果继续作为辅助信息；低置信度、信息不足和模型不可用仍由既有函数返回，未被 service 默认为安全或临床结论。
- 既有 Safety Evaluation Set 和 characterization snapshot 必须保持；本 slice 不修改红旗规则和分诊策略。

## 实施步骤

1. 新增注入式 `DiseasePredictionApplicationService` 与结果对象。
2. 将旧 prediction route 改为 service 调用，保留原 HTTP 适配。
3. 增加 available/empty/detail unit tests，运行全量回归、模型 smoke、Safety Evaluation、快照和 diff 检查。

## 验收

- service 不依赖 Flask，不加载模型文件，不重新实现推理；route 输出与旧行为一致。
- 通过 Python compile、pytest、模型/API smoke、Safety Evaluation、characterization snapshot。

## 回滚

恢复旧 route 中的 prediction 调用和详情标签 enrichment，移除 service、测试和记录即可；不修改模型或数据。

## 实施结果

- `/api/predict-disease` 已收敛为输入/状态码/响应适配，模型结果编排移入 `DiseasePredictionApplicationService`。
- 新增 available、空结果和 detail enrichment 单测；全量 pytest 为 `102/102`。
- 模型 smoke、Safety Evaluation 和 characterization snapshot 保持既有基线。
