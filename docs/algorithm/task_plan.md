# 探索计划

依据：CORE_EXPLORATION.md。用户已授权自主技术决策，不等待确认。

| 阶段 | 状态 |
|---|---|
| 1 评测根因修复及失败回归 | complete |
| 2 修正 Round4 五 seed 复评 | complete |
| 3 表示/标准模型/内层选择矩阵 | complete |
| 4 校准/拒答/分科室覆盖 | complete |
| 5 泛化/源迁移/压力实验 | complete |
| 6 追问概率与对照 | complete |
| 7 中文桥接与安全挑战 | complete |
| 8 冻结报告/回归/停止定时任务 | complete |

## 错误记录
| 错误 | 处理 |
|---|---|
| heartbeat 未指定 destination/target | 指定 destination=thread，已创建成功 |
| joblib 的 -m 回调保存为 __main__，跨模块加载失败 | 已定位到函数模块名；增加限定5个已知回调的本地加载器，不重训、不覆盖原模型，后续导出可移植模型 |
| Windows py_compile不展开字面*.py | 使用PowerShell显式文件数组，编译通过 |
