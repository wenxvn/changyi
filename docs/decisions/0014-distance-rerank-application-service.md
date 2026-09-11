# ADR-0014：以 Application Service 编排医生距离重排

状态：已接受  
日期：2026-09-11  
范围：`/api/recommend/rerank` 与 `backend/app/application/recommendation.py`

## 背景

旧 rerank handler 同时完成医生集合选择、医院关系查找、距离计算、摘要投影和排序，导致推荐 HTTP 层继续承载资源编排。

## 决定

- 新增 `DistanceRerankApplicationService`，通过 supplier 注入真实医生、兼容医生、医院和距离函数。
- service 返回旧 data payload，不依赖 Flask、不改变距离或排序语义；route 继续负责输入校验和区域坐标回退。
- 保留真实医生优先、兼容回退以及距离升序的历史行为。

## 影响

正向影响：距离重排可无 Flask 单测，后续推荐 route parity 有明确接缝。

代价：距离仍是直线距离/既有展示值，不代表导航或实时到院保障；推荐整体排序、交通新鲜度和医学审核仍开放。

## 回滚

恢复旧 handler 的局部查找/排序实现即可，不涉及数据、模型或用户状态。
