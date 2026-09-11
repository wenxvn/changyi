# 历史记录：旧资源路由收敛

日期：2026-09-11

将旧医院/医生索引、详情和关系接口接入 `ResourceCatalogApplicationService`，保持旧 URL、response shape、source marker、兼容回退和 404 行为。新增 service/route 测试后，全量 pytest 为 99/99，表征快照 SHA-256 未变化。本次未修改医学逻辑、推荐排序、模型或原始数据；provenance、正式急诊路径和其他 legacy route parity 继续留在开放风险中。
