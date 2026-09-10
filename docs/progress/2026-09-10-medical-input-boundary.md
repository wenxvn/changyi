# 2026-09-10 医学输入边界切片

## 目标

完成 P2-S1 的第一小步：把既有口语症状归一化和否定窗口判断从 `app.py` 抽取到无 Web 依赖的 domain 模块，同时保持旧入口名称和 API 行为不变。

## 已完成

- 新增 `backend/app/domain/medical_input.py`，承载归一化别名、已知疾病模式常量和否定窗口纯函数。
- `app.py` 通过兼容导入继续暴露 `normalize_patient_expression`、`COLLOQUIAL_SYMPTOM_ALIASES`、`KNOWN_DISEASE_PATTERNS` 和 `_contains_positive`。
- 新增 4 个输入边界测试，覆盖 alias、否定、转折和硬边界后的阳性。
- 更新计划、安全卡、架构、风险、迁移、评分卡、历史和 review 记录。

## 验证

- `pytest`：16/16 通过。
- `py_compile`：`app.py`、domain 模块及相关测试通过。
- API smoke：既有 9 项通过，包含急症、空输入、非法输入、模型降级和 404 边界。
- characterization snapshot：哈希仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- `node --check static/js/app.js`、数据质量扫描和 `git diff --check` 通过。

## 未完成与下一步

`喘不上来` 的 alias under-triage、`不舒服` 的信息不足降级和统一 `INSUFFICIENT_INFORMATION` 仍是已记录问题，本切片没有静默修复。下一步进入 P2-S2，先建立 Safety Gate、状态枚举和独立 Safety Set，再由医学审核决定规则变化。

## 回滚

本切片只涉及模块抽取、兼容导入、测试和文档；回退本切片改动即可恢复函数在 `app.py` 内的旧位置，不涉及数据或模型文件。
