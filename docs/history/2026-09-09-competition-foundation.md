# 2026-09-09 竞赛迁移基础切片记录

## 事实

- 工作树从 `838d4db` 开始时干净；本次仅新增竞赛文档、backend foundation、Region Pack、数据质量工具、测试和脚本 CLI 变更。
- 盘点纠正为 11 份医生 JSON、2,100 条记录；`doctors_h6.json` 声明 82、实际 74 的差异已记录，未改源数据。
- Region manifest 初始相对路径越出预期目录，已改为相对于 `data/regions/320400` 的 `../../` 路径，并由 repository 测试覆盖。
- 旧推荐两个入口现共享 `_build_recommendation_data`；旧 URL 和响应外形保留。

## 验证事实

- Python compile、Node syntax、7 个 unittest 均通过。
- 临时 Flask 环境 smoke 通过；系统 Python 仍没有安装 Flask，因此未修改全局环境。
- 数据质量报告 27 个文件、187 个异常；没有自动清理或覆盖数据。

## 回滚

本切片的文档、backend、tests、data_validation 和脚本变更可按文件/提交独立回退；保留的旧 `/api/*` 路由仍是行为回滚入口。未执行 destructive git 操作。

