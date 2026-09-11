# AGENTS.md — 常医协作规则

## 项目边界

常医是常州市医疗资源检索、分诊辅助、可解释推荐和数据展示的演示系统。它不能声称完成医学诊断、处方、急救指令或临床决策。

- 所有模型、分诊和推荐输出都必须标注为辅助信息，并保留不确定性、人工/专业复核和红旗提示。
- 红旗症状优先于距离、价格或排序偏好；不得在普通 UI 中弱化急症动作。
- 不引入真实患者身份、病历、联系方式、凭证、Cookie、令牌或未脱敏日志。
- 医院、医生、交通和图片事实必须保留来源、更新时间、许可证/权限和脱敏状态；缺失来源不得包装成官方事实。
- 账号、云同步、数据库、生产认证、实时急诊、导航、模型训练和医学规则改动必须另立 L3/L4 评审，不能以重构名义顺带实现。

## 当前正式架构

```text
Browser
  ↓
Flask-served React build (frontend/dist)
  ↓
/api/v1 blueprint
  ↓
HTTP adapters → application services → domain → repositories/model adapters → data
```

`app.py` 是保持 `python app.py` 和旧导入方式的薄启动兼容层；Flask 组合根位于 `backend/app/composition.py`。正式前端只使用 `/api/v1/*`。旧 `/api/*` 路由、旧模板、旧单体 JS/CSS、测试反馈写入端点和迁移 adapter 已移除。

## 开始工作

1. 运行 `git status --short --branch`、`git log --oneline -10`，保留用户已有改动。
2. 阅读本文件、`README.md`、`memory.md`、`docs/status/current.md`、`docs/architecture/current-state.md`、`docs/risks/register.md` 和必要 ADR。
3. 先写清目标、非目标、验收标准和回滚点。功能、架构、数据契约或医疗行为变化要先更新计划/ADR/风险。
4. 只修改当前任务范围，不使用 `git reset --hard`、`git checkout --`、递归删除或 force push。

## 实施规则

- 保持 `/api/v1` URL、响应 envelope、状态码、字段和关键 UI 流程，除非迁移计划明确写出兼容策略。
- 路由只做请求校验、service 调用和错误映射；数据访问、模型调用、排序、解释和公开字段投影必须有唯一 owner。
- 纯重构先用 characterization/golden/smoke 固化行为，再移动边界；禁止为改善测试指标修改红旗、分诊、模型、权重或数据口径。
- 数据文件不能手工改写而缺少来源、时间、许可证和校验说明；生成物与正式数据分开。
- UI 修改遵循 `ui-registry.md` 和 `frontend/src/styles/tokens.css`，保持键盘、focus-visible、reduced-motion、loading/error/empty/safety 状态。
- 删除前用 `git grep` 检查运行时、测试、脚本、CI 和文档引用；删除后运行构建和回归。

## 验证门禁

- Python：`python -m py_compile` 覆盖修改模块；`python -m pytest`；Flask test client 覆盖成功、空/非法输入、缺数据、模型不可用和 404。
- 医学：运行 `python -m evaluation.safety.evaluate_safety`，Safety baseline 必须无意外变化；急症、信息不足和普通路径都要检查。
- 数据：运行 `python -m data_validation.validate_datasets --data-root data --output-dir data_validation`；异常只登记，不静默修复。
- 前端：在 `frontend/` 运行 `npm run typecheck`、`npm run test`、`npm run build`；浏览器检查核心路由刷新、移动/桌面布局、控制台和网络错误。
- 完成前按 `skills/review/SKILL.md` 做计划对齐、系统完整性和交付准备度复核；失败或连续补丁先按 `skills/recover/SKILL.md` 诊断。

## 记录与收尾

日常小改动只更新 `docs/status/current.md`（必要时更新风险）；只有重大架构决策写 ADR，医疗/安全行为变化同时写风险和评估，重大事故写 incident。不要为每个小步骤重复创建 plan/progress/history/review。

收尾时检查 `git diff --check`、`git diff`、`git status`、未跟踪生成物和秘密；更新 `memory.md`，只记录下一次工作真正需要的非敏感上下文。未获明确授权不要推送远端。
