# 竞赛迁移基础切片复核

日期：2026-09-09  
范围：P0-S1、P0-S3、P1-S1～P1-S4 的最小骨架

## 计划对齐

- 竞赛 workspace、审计、目标架构、数据溯源、模型/安全/评估/发布文档已建立。
- Region Pack、数据加载边界和 v1 API 外壳已建立；没有修改红旗规则、模型权重或排序权重。
- P0-S2 已生成稳定字段快照；P0-S4 已完成一次 desktop 运行态检查，负责人确认 UI 基线后已建立 registry，并完成首个 token/手动轮播切片；完整 viewport/console 仍未完成。

## 系统完整性

- 通过：Python compile、Node syntax、9 个基础/数据边界测试、临时 Flask API smoke。
- 通过：最终 API smoke 9 项，覆盖成功、空输入 400、404、v1 envelope 和急症 `triage_status=EMERGENCY`；稳定快照连续两次 SHA-256 一致。
- 通过：Region manifest 路径、active region 唯一性、loader 路径逃逸和 malformed JSON 测试。
- 已知问题：数据质量报告有 187 个异常；v1 endpoint 虽已在 factory/legacy 两个入口可访问，业务仍依赖 legacy adapter，完整 legacy route parity 未完成。
- UI 已验证急症流程最终显示急症提醒、120 入口和免责声明；手动轮播可切换到资源覆盖页；仍有定位超时降级、favicon/Leaflet 图片 404，且移动端矩阵未验证。

## 生产准备度

当前不具备生产发布条件：医院目录来源/许可未逐字段闭环，反馈日志仍需隐私最小化，系统没有 CI/正式依赖层和运行态 UI/无障碍验证。所有未来城市仍未激活，竞赛演示应明确说明当前仅覆盖常州。

## 复核结论

允许进入下一小切片；质量异常仍须按数据治理流程处理。不允许以本切片的 smoke 结果宣传医学准确率或生产可用性。
