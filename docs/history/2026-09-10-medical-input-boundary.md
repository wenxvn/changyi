# H-20260910-002：抽取医学输入 domain 边界

- 日期：2026-09-10
- 类型：重构 / L3 安全边界准备
- 结果：完成

## 事件

将 `app.py` 中已有的症状口语归一化、否定窗口判断和相关兼容常量移动到 `backend/app/domain/medical_input.py`。旧入口通过显式导入继续提供原名称，未改变医学关键词、红旗判断、分诊等级、推荐权重或模型输出。

## 证据

- 4 个输入边界测试覆盖 alias、否定、转折和句法硬边界。
- 全量 pytest 16/16 通过。
- characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- API smoke、Python/JavaScript 静态检查、数据质量扫描和 diff 检查通过。

## 后续

Safety Gate 尚未独立；alias under-triage 和模糊输入降级仍登记在安全卡与 R-001，进入 P2-S2 时必须使用反例集和医学审核记录处理。
