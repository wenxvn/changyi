# 首轮竞赛准备度审计

日期：2026-09-09  
基线：`main`，HEAD `838d4db`

## 结论

仓库已经有可演示的 Flask 医疗资源推荐原型，但尚未达到正式竞赛作品的证据标准。最优先的工作是把现有行为冻结成可重复基线，建立 Region/manifest/data quality 边界，并让急症安全与模型局限可验证；本轮不通过改变排序“做出更好看数字”。

## 量化发现

| 领域 | 发现 | 证据 |
| --- | --- | --- |
| 后端 | 3,172 行；88 个函数；最大函数 235 行；24 个路由 | `app.py` AST/行数审计 |
| API | `/api/recommend` 与 `/api/recommend/enhanced` 存在重复核心逻辑 | `app.py` 2811、2910 |
| 前端 | 4,351 行 JS；25 处 fetch；84 处 innerHTML；112 处 window 私有状态引用 | `static/js/app.js` 静态审计 |
| UI | 7,174 行 CSS；572 hex；185 rgb/rgba；104 inline style；17 media queries | `static/css/style.css`/模板/JS |
| 数据 | 11 份医生 JSON 共 2,100 条；公交/出租车/骑行五个集合各 50 条；医院 21 条代码常量 | 数据清单与 AST、`data_validation/data_quality_report.json` |
| 模型 | 41 类 NB 报告 Top-1 0.973、Top-3 1.000 | 模型文件/训练报告 |
| 可复现性 | 基线脚本曾依赖 `D:/...` 与 Windows 字体路径；依赖文件仅 2 行 | 基线 `parse_hospitals.py`、脚本、`requirements.txt` |
| 运行环境 | 当前 Python 3.14 未安装 Flask/Flask-CORS，Flask smoke 暂时无法运行 | 2026-09-09 环境检查 |
| 发布风险 | 跟踪 `tools/cloudflared.exe`；`ppt_build_tmp` 有生成物；反馈文件含历史网络元数据和健康描述 | `git ls-files`、数据审计 |

## 安全与可信度问题

- 旧版疾病候选把启发式分数显示为 `probability`，需要在产品层严格区分“疾病模型估计”与“推荐排序指数”。
- 医院 `beds`、`daily_outpatients`、`rating`、`strength_scores` 混在代码常量中，来源/派生语义没有逐字段 manifest。
- 交通数据已有脱敏说明，但当前样本存在需要自动报告的时间/异常年份风险；不应直接宣传为实时交通。
- 测试反馈接口会保存 remote IP、User-Agent 和 payload，后续应默认最小收集并建立 redaction。

## 本轮不做

不删除用户文件、不更换 Flask、不改模型和红旗规则、不抓取全国数据、不重写前端、不手工修改实验结果。所有这些会在后续有证据和审核时分片处理。

## 首轮实施后的校正

- 医生资产以当前工作树实际文件为准：11 份 `doctors_h*.json`、2,100 条记录；其中 `doctors_h6.json` 的声明总数 82 与实际 74 不一致，已由质量报告保留为异常，未改数据。
- `parse_hospitals.py` 已改为显式 `--input-dir/--output-dir/--region` CLI；医院源文件缺失时不会自动覆盖 `data/`。
- 图标构建脚本已移除 Windows 字体绝对路径，字体改为可选 `--font-path`，缺省使用 Pillow fallback。
- 质量报告当前扫描 27 个数据文件、记录 187 个异常；主要是公交时间字段的疑似占位年份和 6 条时间先后异常。该报告是数据债务证据，不是放行结论。

## 审计证据与下一步

迁移蓝图见 [MIGRATION_PLAN.md](MIGRATION_PLAN.md)，目标边界见 [ARCHITECTURE_TARGET.md](ARCHITECTURE_TARGET.md)。下一步运行 characterization、schema/data quality、Python compile 和 v1 smoke；UI 需依赖完整运行环境后按 imprint audit 建立基线。
