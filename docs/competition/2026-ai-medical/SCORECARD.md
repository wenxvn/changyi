# 竞赛评分卡

| 评分项 | 当前证据 | 当前问题 | 计划改进 | 对应代码 | 对应实验 | 完成状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 安全分诊 | 旧版含红旗规则和急症分支 | 状态枚举不统一，缺独立 Safety Set | Safety Gate 服务、反例集、Recall/under-triage | `app.py` → `backend/app/domain/triage` | `evaluation/safety` | 进行中 |
| 模型可信度 | 41 类 NB 模型文件与训练报告 | 小数据、单次切分、存在潜在重复泄漏 | fingerprint split、abstain、校准、baseline 对比 | `data/symptom_disease_model` | `evaluation/model` | 进行中 |
| 推荐质量 | 已有多目标医院/医生排序 | 逻辑在单体内，权重和事实语义混杂 | candidate/scoring/rerank/explain 分层与消融 | `app.py` → `backend/app/domain/recommendation` | `evaluation/recommendation` | 进行中 |
| 数据可信度 | 交通数据有部分来源/隐私说明 | 医院常量无统一 manifest，医生 schema 不一 | Region Pack、manifest、质量报告 | `data/regions/320400`、`data_validation` | `tests/data_quality` | 进行中 |
| 产品体验 | 现有流程可演示 | 登录门面像管理台，首页密度高，急症 salience 不足 | 新 shell、渐进式问诊、Trust Center、响应式 QA | `templates`、`static` → `frontend` | UI audit/E2E | 待开始 |
| 城市迁移性 | 代码中已有区域点位 | 常州逻辑散落，暂无 RegionContext | registry/repository 契约和 future pack 文档 | `backend/app/infrastructure/regions` | region contract | 进行中 |
| 工程交付 | 有协作规则和路线图 | 无正式测试/CI，依赖仅 2 行 | characterization、schema、CI、release freeze | `tests`、`.github/workflows` | CI | 进行中 |
