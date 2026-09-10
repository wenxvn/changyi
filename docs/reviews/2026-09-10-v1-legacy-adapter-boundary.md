# Review：v1 legacy adapter 边界

日期：2026-09-10

## 第一层：计划对齐

通过。adapter 只承担延迟解析与调用，路由、状态码、响应 envelope 和既有业务函数保持。

## 第二层：系统完整性

通过。adapter 不复制 triage、推荐、模型或数据逻辑；契约测试覆盖失败 envelope、请求校验、v1/legacy 急症状态和目录 source 标记。

## 第三层：生产准备度

发现问题但不阻塞本切片：完整 route parity、认证、CORS/部署安全、医院 provenance 和 Safety 缺口仍开放；“legacy_catalog_pending_provenance” 标记继续保留。

## 结论

本切片可进入交通 cache 或应用服务边界；在完成 adapter parity 前，不应把 v1 兼容外壳当成独立生产 API。
