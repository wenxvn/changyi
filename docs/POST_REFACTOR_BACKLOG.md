# Post-refactor backlog

本文件只登记任务，不代表已授权或已实现。每项都必须按 `AGENTS.md` 的 L3/L4 规则单独规划、评估和回滚。

## 功能迁移记录（2026-09-11 P1）

### 已恢复

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 高德导航 | **已恢复** | 外部 URI，非实时路线 |
| 真实地图 | **已恢复** | OSM 底图 + 医院 marker |
| 用户定位 | **已恢复** | unknown / district / geolocation 三态 |
| 医院详情 | **已恢复** | `/resources?hospital=` |
| 医生详情 | **已恢复** | `/resources?doctor=` |
| 医生照片 | **已恢复** | `DoctorAvatar` + onError 首字回退 |
| 医院 Logo | **已恢复** | `HospitalLogo` + Building 回退 |
| 资源高级筛选 | **已恢复** | 等级/类型/医院/科室/职称 + 关键词 |
| 专家偏好 | **已恢复** | system / wish_expert / no_expert |
| 语音输入 | **已恢复** | 仅 Speech→Text，不自动提交 |

### 延后（P2）

| 能力 | 说明 |
| --- | --- |
| 交通地图层 | 需 bus 数据先通过正式质量门 |
| 本地收藏 / watchlist | 非主链路；需明确非病历 |
| 交通可达性进排序 | 当前 PROVISIONAL，`rankable=false` |

### 永久不恢复

| 能力 | 说明 |
| --- | --- |
| Demo Login | 易被误解为生产安全 |
| Dashboard | Trust Center 已承担证据展示 |
| 浮动 Assistant | 不做 ChatGPT wrapper |
| Tester Feedback | 旧测试员后台 |
| 自动轮播 | 非主路径 |

## Safety / Medical

- 扩展专业复核后的 Safety Evaluation 覆盖，检查未纳入固定样例的红旗表达、否定/历史语境和信息不足边界。
- 继续审核压榨样胸痛伴呼吸困难/冷汗、反复头晕等自然语言组合；当前固定样例已回归通过，不代表医学覆盖完整。
- 评审红旗规则、分诊阈值、医学文案和结构化 follow-up answer 契约。

## Data

- 完成医院/医生逐字段来源、许可证、更新时间、脱敏状态和正式发布范围。
- 处理数据质量报告登记的 187 个异常；不直接修改原始数据。
- 公交/出租车数据补齐 license 与覆盖度后，再评估是否将 `TransitQualityGate.rankable` 打开。

## Product / Frontend

- 评估正式附近急诊路径、实时急诊可用性和更完整的视觉/对比度/无障碍矩阵；当前高德 URI 只提供外部导航跳转。
- 任何新的 Profile、账号、云同步或医疗档案能力必须先做隐私与认证 L4 评审。

## Infrastructure

- 如确有需求，另立生产认证、授权、审计、数据库、部署和监控方案；演示登录/CORS 不能直接升级为生产安全措施。
- 继续观察远端 CI 首次运行结果；只修当前基线相关问题。
