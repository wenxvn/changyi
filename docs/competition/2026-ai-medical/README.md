# 常医智导 · 2026 AI+医学竞赛工作区

本目录是参加 2026 全球校园人工智能算法精英大赛「AI+医学」赛道的单一竞赛证据入口。它记录产品边界、目标架构、数据来源、模型限制、安全机制、实验计划、演示路径和发布门禁。

## 当前定位

**常医智导（CarePath AI）** 是一个面向常州市的可信智能就医决策辅助系统：先识别需要优先处理的安全信号，再在常州可验证的医院、医生和交通资源中提供科室与就医路径参考。

系统不提供诊断、处方、急救替代或医疗效果承诺。疾病候选只用于研究/分诊辅助，资源综合分只用于排序，不是疾病概率、诊断概率或医疗质量保证。

## 文档索引

- [竞赛简报](COMPETITION_BRIEF.md)
- [产品规格](PRODUCT_SPEC.md)
- [目标架构](ARCHITECTURE_TARGET.md)
- [设计系统](DESIGN_SYSTEM.md)
- [数据溯源](DATA_PROVENANCE.md)
- [模型卡](MODEL_CARD.md)
- [安全卡](SAFETY_CARD.md)
- [评估计划](EVALUATION_PLAN.md)
- [评分卡](SCORECARD.md)
- [演示脚本](DEMO_SCRIPT.md)
- [发布清单](RELEASE_CHECKLIST.md)
- [迁移计划](MIGRATION_PLAN.md)
- [首轮审计报告](AUDIT_REPORT.md)
- [Legacy UI imprint 审计](UI_AUDIT_BASELINE.md)

## 证据规则

任何展示给评委的数字都必须能回到数据清单、模型文件、评估结果或自动生成的质量报告。没有来源、许可、时间戳、schema 和质量检查记录的数据只能标记为 `demo_only`，不得进入正式主推荐结果。

## 当前区域

当前 active Region 只有：`320400 · 常州市`。其他城市是架构层面的 Future City Pack，不代表已经接入数据。
