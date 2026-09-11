# ADR-0018：摘要、证据与地图使用显式 Application Service

状态：已接受  
日期：2026-09-11  
范围：v1 summary/evidence/map 只读接口

## 背景

资源、分诊、推荐、交通和模型边界已经逐步从根级 Flask 模块中抽出，但摘要、Trust Center 证据和地图接口仍在路由函数内直接拼装区域、数据集、评估报告和坐标投影。这使只读展示边界难以独立测试，也让 `app.py` 继续承担组合职责。

## 决定

- 新增 `SummaryApplicationService`、`EvidenceApplicationService` 和 `MapViewApplicationService`。
- service 通过 suppliers 读取既有区域、医院、医生、交通和项目报告；不复制数据，不改变医学或推荐策略。
- Flask 路由保留 HTTP 参数解析、v1 成功/失败 envelope 和 `MapLocationError` 到 400 的适配。
- Trust Center 继续展示 provisional 状态与既有局限；地图继续是位置示意，不被包装为导航或实时急诊可用性。

## 影响

正向影响：只读投影的依赖和边界可单元测试，后续独立 factory composition 有明确接缝。

限制：service 仍由根级 `app.py` 组合，完整 factory 解耦、实时急诊路径和正式 provenance 仍未完成。

## 回滚

删除三个 service 的实例化和路由委托，恢复原内联/函数调用即可；不影响现有 API 契约。
