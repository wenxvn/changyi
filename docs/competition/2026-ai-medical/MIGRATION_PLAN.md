# 竞赛迁移计划

- 状态：进行中
- 建立日期：2026-09-09
- 变更等级：本轮基础设施为 L2；涉及红旗、模型、推荐权重或医疗文案的后续 Slice 自动升级为 L3。
- 总原则：先审计与表征，再抽取单一边界；旧入口保持可回滚。

## 已完成的首轮审计

- 记录 Git 分支、工作树、未跟踪文件、大文件/二进制、重复/硬编码风险和依赖现状。
- 读取并核对 README、工作流文档、ADR、风险和质量门禁。
- 盘点 24 个 Flask 路由、21 个医院常量、11 个医生 JSON（2,100 条）、公交/出租车/骑行数据和本地症状模型。
- 量化前端耦合：4,351 行 JS、112 处 `window._*` 状态引用、25 处 fetch、84 处 `innerHTML` 赋值、104 处 inline style。
- 量化视觉债务：7,174 行 CSS、572 个 hex 色值、185 处 rgb/rgba、17 个媒体查询。
- 基线发现 `parse_hospitals.py` 依赖 `D:/...`，图标脚本含 `C:/Windows/Fonts/...`；本轮已将两者改为显式输入/可选字体路径；仓库仍有 `tools/cloudflared.exe` 和历史生成物风险。
- 发现现有模型报告的 0.973/1.000 指标来自小数据单次分层切分，尚未满足竞赛宣传条件。

## Slice 列表

### Phase 0 · Audit & Characterization

1. **P0-S1 竞赛工作区与证据入口**：本目录 13 份文档、审计报告、评分卡。回滚：文档提交可独立回退。
2. **P0-S2 API/纯函数表征**：冻结旧路由、归一化、否定、科室、红旗、追问、推荐和模型不可用样例。验收：输出 snapshot 可重复。
3. **P0-S3 数据质量基线**：新增 schema/质量检查，生成 JSON/Markdown 报告，不改原始数据。验收：异常显式报告。
4. **P0-S4 UI audit baseline**：启动 legacy 页面后审计 desktop/mobile、console、network、overflow 和安全显著性；先确认基线再改 UI。

### Phase 1 · Repository Foundation

5. **P1-S1 配置与应用工厂**：集中根目录、active region、CORS 和环境配置；旧入口保留。
6. **P1-S2 RegionRegistry/RegionContext**：激活 `320400`，Future City Pack 不伪造数据。
7. **P1-S3 DataLoader 与 repositories**：统一 JSON/CSV 错误、schema、来源和只读加载；先接医生/交通，医院保留兼容适配器。
8. **P1-S4 API v1 contracts**：`/api/v1/health`、`/ready`、`/regions` 和推荐兼容外壳，禁止前端复制规则。
9. **P1-S5 CI 与依赖层**：runtime/dev/data-tools 分层、Python/JS/pytest/schema/model smoke。

### Phase 2 · Backend Domain Extraction

10. **P2-S1 医学输入层**：normalization、negation、entities。
11. **P2-S2 Safety Gate/triage/follow-up**：统一枚举，需 Safety Case、样例/反例和医学审核记录。
12. **P2-S3 recommendation pipeline**：candidate、feature、score、rerank、explain。
13. **P2-S4 API route adapters**：旧 API 调新 service，契约比较后收敛推荐入口。

### Phase 3-9 · Evaluation、Frontend、Trust、Hardening、Release

14. 先完成 fingerprint split、baseline、校准、Safety Set 与推荐消融。
15. 建立 `frontend/` 新 shell、Design Tokens、首页、渐进式问诊和结果页；legacy 保留至 parity。
16. 接入医院/医生/地图、来源徽标和 Trust Center。
17. 完成 E2E、无障碍、性能、隐私、视觉 QA、CI 和三分钟演示。
18. 绑定版本、冻结发布，输出 `v1.0-competition`。

## 当前实施顺序

本轮已完成 P0-S1、P0-S2 的快照、P0-S3、P1-S1、P1-S2、P1-S3 的最小可用骨架，并建立 P1-S4 的 v1 兼容外壳；P0-S4 已完成一次 desktop 运行态审计，负责人已确认三项 UI 基线建议并建立 `ui-registry.md`。随后完成首个低风险 UI 切片：语义 token 别名、统一 focus-visible 和首页手动轮播。完整 viewport 矩阵与独立 console 报告仍待继续；本轮未修改红旗规则、权重或模型文件。

## 回滚与风险

- 旧 `/api/*` 路径继续保留；v1 失败时回到旧路径。
- Region manifest 只增加元数据，不删除或改写原数据。
- 质量报告中的异常先登记到 R-002/R-005/R-008/R-009，不静默修数据。
- 任何医学语义变化须暂停该 Slice，新增 ADR 和领域审核记录。
