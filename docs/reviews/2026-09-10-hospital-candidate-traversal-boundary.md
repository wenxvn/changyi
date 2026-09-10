# Review：医院候选遍历边界

日期：2026-09-10

## 第一层：计划对齐

通过。只迁移医院候选遍历和上下文准备，未改变候选集合、距离、交通 policy、单候选组合、rerank 或公共字段。

## 第二层：系统完整性

通过。domain orchestration 不读取 Flask、全局数据或文件，依赖均由回调和显式参数提供；urgent/emergency 仍禁用公交/出租车 ranking 权重，first_visit 仍保留原 policy。

## 第三层：生产准备度

发现问题但不阻塞本切片：交通数据加载/刷新、医院 provenance、服务层和急症候选整体排序仍开放；Safety Eval 的 review_required case 不能作为发布放行证据。

## 结论

本切片可进入急症候选遍历或应用 service 拆分；继续保持人工/专业复核要求。
