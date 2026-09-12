# Post-refactor backlog

本文件只登记任务，不代表已授权或已实现。每项都必须按 `AGENTS.md` 的 L3/L4 规则单独规划、评估和回滚。

## Legacy Migration Status

# Legacy Migration Complete

后续开发不再以旧版功能迁移为主线，新需求进入 P2 Product Intelligence / Resource Routing。

### 已恢复

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 高德导航 | **已恢复** | 外部 URI，非实时路线 |
| 真实地图 | **已恢复** | OSM 底图 + 医院 marker |
| 用户定位 | **已恢复** | unknown / district / geolocation 三态 |
| 医院详情 | **已恢复** | `/resources?hospital=` |
| 医生详情 | **已恢复** | `/resources?doctor=` |
| 医生照片 | **已恢复** | `DoctorAvatar` + 旧资产可靠映射 + provenance |
| 医院 Logo | **已恢复** | `HospitalLogo` + Building 回退 |
| 资源高级筛选 | **已恢复** | 医院：等级/类型/区域/急诊字段；医生：医院/科室/职称 |
| 专家偏好 | **已恢复** | system / wish_expert / no_expert |
| 语音输入 | **已恢复** | 仅 Speech→Text，不自动提交 |

### 明确放弃 / 永不恢复

| 能力 | 说明 |
| --- | --- |
| Demo Login | 易被误解为生产安全 |
| Dashboard | Trust Center 已承担证据展示 |
| 浮动 Assistant | 不做 ChatGPT wrapper |
| Tester Feedback | 旧测试员后台 |
| 自动轮播 | 非主路径 |
| 旧医院能力 96/98/91 分 | 不恢复伪精确分 |
| 高科研指标主导医生排序 | 学术仅 tie-break |
| 复杂语音自动填表 | 保持 Speech→Text |

## P2 Product / Resource Routing

| 能力 | 说明 |
| --- | --- |
| 服务端医生搜索/分页 | P2-1；当前 2100+ 医生不宜全部前端过滤 |
| Visit Intent | P2-2；仅影响 Resource Routing，不影响 Safety Gate |
| Resource Routing Preferences | P2-3；跨区/距离/连续复诊，默认关闭 |
| 本地收藏 / watchlist | P2-4；localStorage 仅 doctor_id + created_at；非病历 |
| Provenance-aware import pipeline | P2-5；raw snapshot 只读，应用层不直接读 |
| 推荐解释强化 | P2-8；明确展示未参与排序字段 |
| 交通地图层 | 需 bus/taxi/bike 数据先通过正式质量门 |
| 交通可达性进排序 | 当前 PROVISIONAL，`rankable=false` |
| 正式附近急诊路径 | 需实时急诊可用性数据与 L3/L4 |
| 账号 / 云同步 / 正式患者档案 | 必须先做隐私与认证 L4 评审 |
| 全国城市 / 实时公交导航 API | 不在常州演示范围 |

## Safety / Medical

- Safety Set 已扩到 135 cases；继续专业复核 `question-stroke-signs` 过触发与未覆盖表达。
- Over-triage 当前 0.0312，可接受但需持续报告；不得为降 over-triage 削弱红旗召回。
- 继续审核压榨样胸痛伴呼吸困难/冷汗、反复头晕等自然语言组合；固定样例通过不代表医学覆盖完整。
- 评审红旗规则、分诊阈值、医学文案和结构化 follow-up answer 契约。

## Data

- 完成医院/医生逐字段来源、许可证、更新时间、脱敏状态和正式发布范围；结构已就位，仍待外部核验。
- 处理数据质量报告登记的 186 个异常；不直接修改原始数据。
- 公交/出租车/骑行数据补齐 license 与覆盖度后，再评估是否将 `TransitQualityGate.rankable` 打开。
- 医生照片从 `LEGACY_EXACT_MATCH` 升级到 `SOURCE_VERIFIED` 需补齐原始来源 URL 与许可。

## Infrastructure

- 如确有需求，另立生产认证、授权、审计、数据库、部署和监控方案；演示登录/CORS 不能直接升级为生产安全措施。
- 继续观察远端 CI 首次运行结果；只修当前基线相关问题。
