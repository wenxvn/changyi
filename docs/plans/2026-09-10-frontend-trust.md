# 常医智导前端迁移计划：可信 AI 首版

状态：进行中（首版）  
日期：2026-09-10  
变更等级：L2（只读证据 API、前端状态和展示；不改变医学规则、模型文件或推荐排序）

## 目标

在并行 `frontend/` 中把 Trust Center 从占位页推进为 API 驱动的证据摘要页，集中展示安全评估、模型离线指标、数据质量、数据指纹、运行版本和已知限制。页面必须让用户知道这些事实是原型阶段证据，不代表临床验证。

## 非目标

- 不在页面或证据服务中修改、重算或优化红旗规则、分诊等级、疾病模型或推荐权重。
- 不把离线 Top-1/Top-3、Safety Evaluation 或数据质量报告包装成临床验证、官方推荐、诊断或发布放行。
- 不引入真实患者信息、登录、远程 telemetry、生产监控或外部数据上传。
- 不切换 legacy `/` 默认入口，不顺便完成地图、资源详情或正式 provenance 迁移。

## 关键决策

- 证据由只读 `/api/v1/evidence` 统一组装；前端只负责运行时校验和展示，不复制报告数字。
- 评测失败时服务返回不可用状态和空的待复核列表，不暴露异常类型或内部堆栈；页面保留降级提示。
- 数据质量问题、来源状态和版本号与指标并列展示；SHA-256 只作为可复核指纹，不暗示数据正确或临床适配。
- 证据页默认只展示部分 dataset manifest，完整清单仍可通过 API 获取，避免首屏被长清单占满。

## 实施步骤

1. 从现有安全评估、模型报告、数据质量报告和 Region Pack manifest 组装后端证据 payload。
2. 注册 `/api/v1/evidence`，复用 v1 envelope、版本 meta 和 legacy triage evaluator；不改变业务输出。
3. 扩展前端 Evidence 类型、运行时 parser 和共享 API client 调用。
4. 实现 Trust Center 的 loading/error/empty、Safety、Model/Data、Provenance、Reproducibility 和 Limitations 区块。
5. 接入 App Shell `/trust` 路由，更新 tokenized styles、UI registry、架构、状态、进度、历史和 review。
6. 运行 Python/pytest、TypeScript boundary tests/build、API smoke 以及 desktop/390×844 浏览器检查。

## 验收标准

- `/api/v1/evidence` 返回统一 envelope，真实读取当前安全评估、模型报告、质量报告、版本和数据指纹。
- 页面不硬编码评测数字，能够显示 `provisional`、不代表临床验证、review_required 和数据来源限制。
- 缺失报告、接口错误或空数据有明确降级态，页面不把空值渲染为成功指标。
- 桌面和移动端无横向溢出；legacy 默认入口、旧 API、医学规则和推荐快照不变。
- 文档和 review 明确剩余地图、正式 provenance、E2E/视觉/无障碍/CI 门禁，不标记 competition-ready。

## 回滚

回退本计划新增的 evidence service、v1 route、前端 Evidence 类型/API/Trust 页面和对应文档即可；不影响 Flask 默认 `/`、旧 API、已有 triage/recommendation 行为或现有资源页。
