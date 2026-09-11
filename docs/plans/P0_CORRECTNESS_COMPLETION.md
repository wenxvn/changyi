# P0 Correctness + Product Completion

更新时间：2026-09-11

## 目标

修复重构后仍会影响用户判断的正确性缺口，并补回“分诊 → 推荐 → 详情 → 地图 → 导航”的演示闭环：

- 未提供位置时保持 `unknown`，不伪造区域、距离或交通排序；区域选择明确标记为参考点估算，浏览器定位只在用户主动操作后使用本次会话坐标。
- Follow-up 以结构化答案传递，`original_condition` 永远只保留用户输入；危险信号优先于普通推荐。
- 医院目录从组合根外置到 active Region Pack，区分公开事实、派生能力线索和未支持字段；缺失的床位、门诊量、评级和描述不进入公开事实或排序。
- 同时保留随机切分基线和 exact symptom fingerprint 分组评估，将模型切分、数据哈希、近重复审计和限制带入 Trust Center。
- 恢复真实地理底图、位置参考点、医院详情关联医生和 AMap 导航入口。

## 非目标

本轮不引入真实患者信息、账号/云同步、生产认证、实时急诊可用性、实时导航、临床诊断/处方/急救指令、医学规则重写、外部数据核验或新的推荐权重。已有旧字段兼容投影只为保持 v1 响应形状，不代表其事实已核验。

## 验收标准

- v1 triage/recommendations/map 的未知、区域参考点、精确定位、非法位置和结构化 follow-up 均有回归覆盖。
- 急症路径不发布普通推荐；结构化 `present` 进入急症，`unknown` 保持信息不足与专业复核提示。
- 医院参与推荐的字段能归类为公开事实、派生字段或明确缺失；不支持字段为 `null`/不出现在公开投影，并且不可用特征权重为 0。
- Trust Center 同时展示 random baseline、grouped fingerprint split、近重复限制、医院目录 provenance 和数据质量报告。
- 资源详情可回到医院/医生关联内容，医院和地图可打开 AMap URI；地图有 OpenStreetMap/CARTO 底图署名、拖动/缩放和移动布局，并覆盖底图失败降级。
- Python、Safety、数据质量、前端 typecheck/test/build、Playwright smoke 和 diff/review 门禁通过。

## 回滚点

每个切片按文件/提交独立回滚：位置契约、Follow-up、医院目录、模型评估、资源详情/地图和 Trust 展示互不共享持久状态。若某一切片验证失败，保留原目录和响应形状，撤回该切片，不使用 reset、force push 或覆盖用户已有改动。
