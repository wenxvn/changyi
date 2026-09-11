# 2026-09-11 医生距离重排 Application Service 进度

## 本次完成

- `/api/recommend/rerank` 的医生/医院查找、真实优先、兼容回退、医院摘要、距离计算和排序已移入 `DistanceRerankApplicationService`。
- 保留旧输入校验、区域坐标回退、JSON 字段和距离升序。
- 增加 service unit，覆盖未知医生忽略和距离排序。

## 验证

- Python compile：通过。
- 全量 pytest：`105/105` 通过。
- rerank API smoke、characterization snapshot、交通测试和 Safety Evaluation：基线保持。

## 未完成与下一步

推荐整体急症排序、交通新鲜度/刷新、完整 legacy route parity、逐字段 provenance、正式附近急诊路径和远端 CI 仍开放；距离仍不是导航能力。

## 回滚

恢复旧 rerank handler 的局部实现并移除本切片 service、测试和记录即可。
