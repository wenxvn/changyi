# 历史记录：症状疾病模型 Adapter

日期：2026-09-11

将症状疾病模型的本地文件检查、lazy runtime、inference 导入、错误缓存和 top-k 参数移入无 Flask 的 `SymptomDiseaseModelAdapter`，保留 `predict_disease_name` 兼容 wrapper 与详情/非详情输出。全量测试达到 110/110，模型 smoke、Safety Evaluation 和 characterization snapshot 未变化；不涉及模型质量或医学策略。
