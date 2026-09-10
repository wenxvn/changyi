# 计划：抽取推荐排序纯函数边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成

## 目标

完成 P2-S3 的第一小步：把推荐排序中与 Flask、文件读取、模型调用无关的数值、文本、科室关系和医生资源分层纯函数移入 `backend/app/domain/recommendation/scoring.py`，由 `app.py` 兼容导入，建立 candidate/feature/score 拆分的可回滚起点。

## 非目标

- 不改变医院/医生数据、交通可达性、推荐权重、排序顺序、风险惩罚或推荐解释文案。
- 不把当前内部 `fairness` 字段重新命名为对外“公平性”承诺；语义审查留在后续切片。
- 不在本切片迁移完整 `recommend` 或 `enhanced_recommend_doctors`，避免跨越数据访问和医学分诊边界。
- 不改变 legacy 或 v1 API 响应字段。

## 当前基线

- `app.py` 中 `_clamp`、`_as_text`、医生职称/资源分层和科室关系函数被医院/医生排序共同使用。
- 推荐稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 当前安全发布切片仅保护 `/api/v1`；本切片不触碰 Safety Gate 行为。

## 方案与边界

- 新 domain 模块只接受标量或显式资源字典，不读取全局医院/医生列表，不导入 Flask、模型或 Region repository。
- `app.py` 继续导出旧私有函数名称，所有既有调用先改为兼容别名；测试验证代表性正例、负例和资源层级。
- 先抽取共享纯函数，再以推荐快照和 API smoke 作为行为门；完整 candidate/feature/score pipeline 留到后续小步。

## 原子步骤

- [x] 建立 recommendation scoring domain 模块并接入 legacy 兼容导入。
- [x] 新增纯函数单测，覆盖数值边界、科室关系和医生资源分层。
- [x] 运行推荐快照、API smoke、全量测试和静态检查，确认输出不变。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 既有推荐快照哈希不变，legacy/v1 路由字段和排序不变。
- domain 模块不依赖 Web、数据加载或模型；旧函数名称继续可用。
- 不新增未经定义的公平性或临床能力承诺。

## 验证命令与结果

实施结果：27 个 pytest 全部通过；API smoke 11 项通过；推荐 characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；`py_compile`、Node check、数据质量和 `git diff --check` 通过。未修改推荐权重、数据文件、医学规则或 API 字段。

## 回滚

回退本切片即可恢复纯函数在 `app.py` 中的位置，不涉及数据、模型、规则或 API。
