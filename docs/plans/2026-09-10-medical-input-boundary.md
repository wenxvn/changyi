# 计划：抽取医学输入层边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成

## 目标

完成 P2-S1 的第一小步：将现有口语症状归一化和否定识别纯函数从 `app.py` 移入 `backend/app/domain/medical_input.py`，由旧入口导入并继续提供兼容名称，为后续 Safety Gate、实体和追问服务拆分建立单一输入边界。

## 非目标

- 不新增、删除或调整红旗关键词、医学阈值、分诊等级、推荐权重或模型权重。
- 不改变疾病候选、科室匹配、追问文案或 API 响应字段。
- 不在本切片实现新的否定语义；只保留并测试当前规则行为。
- 不把当前模型输出解释为诊断，也不宣称医学安全问题已经解决。

## 当前基线

- 归一化别名表、归一化函数和 `_contains_positive` 分散在 `app.py`。
- characterization 已记录 `喘不上来` 的 alias under-triage 和 `不舒服` 的信息不足缺口。
- 现有稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 新 domain 模块只包含无 Web/Flask 依赖的常量和纯函数：口语归一化、否定窗口判断。
- `app.py` 通过显式导入保留 `normalize_patient_expression`、`COLLOQUIAL_SYMPTOM_ALIASES`、`KNOWN_DISEASE_PATTERNS` 和 `_contains_positive` 的旧可用名称。
- 不把依赖 `DISEASE_DEPT_MAP`、`DISEASE_DIRECT_RULES` 的 `detect_known_disease` 一并搬运，避免一次切片跨越多个业务边界。
- 正例、否定例、红旗口语 alias、模糊输入和原有快照都必须回归；发现输出变化立即回滚本切片。

## 原子步骤

- [x] 建立医学输入层模块并让 legacy 入口导入它。
- [x] 新增输入层单元测试和否定/红旗反例说明。
- [x] 更新安全卡、架构、风险、进度、历史和 review。
- [x] 运行 L3 验证：模型/输入不足/红旗/已知疾病/否定、API smoke、快照和静态检查。

## 验收标准

- 现有 characterization snapshot 内容和哈希不变。
- `normalize_patient_expression` 对 `喘不上来` 等 alias 输出与迁移前一致。
- `contains_positive` 对“没有胸痛，但出现呼吸困难”等否定/转折文本保持当前结果。
- 模型不可用和输入不足仍有显式安全降级；本切片不新增医学承诺。
- 旧 `/api/*`、`/api/v1/*` 可继续通过测试客户端访问。

## 验证命令与结果

实施结果：16 个 pytest 全部通过；API smoke 通过；`py_compile`、Node check、数据质量校验和 `git diff --check` 通过；characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d` 不变。模型不可用和模糊输入降级由既有 smoke 覆盖；完整 Safety Set 和端到端低置信度矩阵留待 P2-S2。

## 风险、回滚和记录动作

- 风险：函数搬运时改变字符串边界或否定窗口，导致 under-triage/over-triage；用旧快照和反例测试阻断。
- 风险：旧模块外部依赖导入名称；保留兼容导入，不删除旧公开名称。
- 回滚：回退本切片提交即可恢复所有函数到 `app.py`；不涉及数据或模型文件。
- 完成后更新 `docs/status/current.md`、`docs/progress/`、`docs/history/`、`docs/reviews/` 和 `docs/risks/register.md`。
