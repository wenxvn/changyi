# 常医后端重构计划：症状疾病模型 Adapter 边界

状态：已完成  
日期：2026-09-11  
变更等级：L3（模型加载/推理边界；只做行为保持式搬运）

## 目标

将本地症状到疾病模型的 lazy loading、推理参数和 unavailable 降级从 `app.py` 移到 infrastructure model adapter；保留 `predict_disease_name` 作为 legacy 兼容名称，并让 prediction application service 继续通过显式调用获得模型结果。

## 非目标

- 不修改模型文件、模型算法、训练数据、类别、top-k、症状归一化、低置信度口径或医学文案。
- 不把模型输出改为诊断，不调整 Safety Gate、Emergency abstain、推荐排序或前端显示。
- 不新增远程模型、用户数据、缓存服务或生产部署能力。

## 安全验收边界

- 缺失/加载失败仍返回 `available=false` 详情结果，非详情调用继续只有 `{"disease": ""}` 的历史兼容结果。
- 详情调用仍使用 top-k 5，非详情调用仍使用 top-k 3；口语替换只在详情结果保留。
- 模型质量、低置信度、分布外和 Safety Evaluation 已知缺口继续保持开放，不因 adapter 抽取而放行。

## 实施步骤

1. 新增 `SymptomDiseaseModelAdapter`，封装本地路径、lazy runtime、错误缓存和 inference call。
2. `app.py` 保留兼容函数并将其代理到 adapter；prediction application service 继续负责 endpoint 状态映射。
3. 增加注入 runtime 与缺失模型测试，运行模型 smoke、API smoke、全量回归、Safety Evaluation、快照和 diff 检查。

## 验收

- adapter 不依赖 Flask；加载失败、normalization、top-k 和详情/非详情输出保持。
- 通过 Python compile、模型 smoke、prediction API smoke、全量 pytest、Safety Evaluation 和 characterization snapshot。

## 回滚

恢复 `app.py` 原 `_load_symptom_disease_runtime` 与 `predict_disease_name` 实现并移除 adapter、测试和记录即可；不修改模型文件。

## 实施结果

- 模型 lazy loading/inference 已移入 `backend/app/infrastructure/models/symptom_disease.py`；`app.py` 仅保留兼容 wrapper。
- 新增 adapter injected-runtime/缺失模型覆盖；全量 pytest 为 `110/110`。
- 模型 smoke、prediction API、Safety Evaluation 与 characterization snapshot 基线保持。
