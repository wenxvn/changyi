# 2026-09-11 旧资源路由收敛进度

## 本次完成

- 旧 `/api/hospitals`、`/api/hospitals/<id>`、`/api/doctors`、`/api/doctors/<id>`、`/api/hospitals/<id>/doctors` 和 `/api/doctors/detail/<id>` 已接入 `ResourceCatalogApplicationService`。
- 保留旧 response shape、字段、source marker、真实/兼容选择规则和 404 行为。
- 增加 service 回退分支和 3 个 legacy route tests。

## 验证

- Python compile：通过。
- 全量 pytest：`99/99` 通过。
- characterization snapshot：连续结果 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 本切片未修改医学规则、推荐权重、模型和数据文件。

## 未完成与下一步

完整 legacy route parity 仍包括分诊/追问、推荐、交通和助手等其他路由；医院/医生逐字段 provenance 和正式附近急诊路径仍开放。

## 回滚

恢复旧资源 handler 的局部查找并移除本切片测试、ADR、计划和进度记录即可。
