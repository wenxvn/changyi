# 竞赛发布清单

状态：重构收口已通过；以下未勾选项是完整竞赛发布前的独立门禁，不等同于本轮重构未完成。

## 产品与安全

- [ ] 首屏定位为可信智能就医决策辅助，不是 AI 医生或诊断系统。
- [ ] 三个 Demo case 稳定；急症先显示 Safety Gate。
- [ ] `EMERGENCY`、`URGENT`、`ROUTINE`、`INSUFFICIENT_INFORMATION` 有契约测试。
- [ ] 模型不可用、输入不足、空态、错误态和低置信度均可安全降级。

## 数据与模型

- [ ] 仅 `320400` Region Pack active；未来城市明确标注未接入。
- [ ] 所有正式数据有来源、许可、时间、hash、schema、脱敏和限制。
- [ ] 数据质量报告无未解释的阻断项。
- [ ] 模型卡不宣传未经验证的准确率；实验结果可复现。

## 工程与 UI

- [ ] app factory、API v1、schemas、repositories 和 `app.py` 薄启动兼容层完成审查。
- [ ] Python/JS 检查、pytest、契约、数据质量和构建通过。
- [ ] 1440/1280/768/390 四种尺寸完成视觉检查。
- [ ] 键盘焦点、对比度、reduced motion、网络错误和控制台错误已检查。

## 发布冻结

- [ ] 版本绑定 app/ranking/triage/model/dataset/region pack。
- [ ] `CHANGELOG.md`、`LICENSE`/数据许可和技术证据齐全。
- [ ] Freeze 后只允许 bug、文案、性能和提交修复。
