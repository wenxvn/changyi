# 常医后端重构计划：医生距离重排 Application Service

状态：已完成  
日期：2026-09-11  
变更等级：L2（既有推荐结果的只读重排编排；不改变医疗策略）

## 目标

将旧 `/api/recommend/rerank` 的医生/医院查找、距离计算结果组装和排序移入独立 application service，保留 route 的输入校验、区域回退和原响应 envelope。

## 非目标

- 不改变 doctor id 选择顺序、真实医生优先、兼容医生回退、医院字段白名单、距离函数或排序规则。
- 不改变推荐权重、分诊、急症路径、交通样本、数据来源或医学文案。
- 不增加定位权限、导航、实时交通、数据库或结构化 follow-up。

## 数据与安全验收边界

- 距离只继续作为展示/重排值，不包装为就医时效、道路导航或医疗可及性保障。
- 用户坐标仍由现有请求/区域回退逻辑提供；本切片不新增身份、历史或敏感数据存储。
- characterization snapshot 与既有交通/推荐纯函数测试必须保持。

## 实施步骤

1. 在 recommendation application module 增加注入式 `DistanceRerankApplicationService`。
2. 将旧 rerank route 收敛为 JSON/区域解析和 service 调用。
3. 增加 service unit，运行 Python compile、全量 pytest、rerank API smoke、快照、Safety Evaluation 和 diff 检查。

## 验收

- service 不依赖 Flask；真实医生优先、兼容回退、医院摘要和距离升序保持。
- 旧 `/api/recommend/rerank` 的成功/空输入/区域回退行为保持。

## 回滚

恢复旧 route 内查找/排序代码并移除 service、测试和记录即可；不修改数据或模型。

## 实施结果

- rerank 的目录查找、医院摘要、距离计算和升序排序已移入 `DistanceRerankApplicationService`。
- 新增 service unit；全量 pytest 为 `105/105`。
- 快照、交通计算和 Safety Evaluation 基线保持。
