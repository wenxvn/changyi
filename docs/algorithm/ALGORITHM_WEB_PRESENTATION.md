# 核心算法如何体现在网页上

2026-10-06：仅为后续呈现方案，当前不扩展网页实现。

页面应按用户的决策顺序展示：原始主诉 → 已识别证据 → 安全状态 → 补充问题 → 就医方向与资源。急诊与信息不足必须在资源推荐之前决定出口。

| 层次 | 服务端依据 | 建议显示 | 约束 |
|---|---|---|---|
| 输入理解 | original_condition、normalized_condition、symptom_tags[].matched_terms | 原文与识别到的症状词，可展开查看归一化 | 人口词不显示为症状；不将模型补出的疾病当患者自述 |
| 安全分流 | triage_status、reasons、red_flag_tags | 第一张结果卡解释为何需要急诊、及时评估、补充信息或普通方向 | ER不进普通排行榜；INFO保留未知，不显示“安全” |
| 追问 | followup.questions、missing_slots、结构化答案 | 一次一问，说明这项信息影响什么；回答后重新计算并显示变化 | unknown可以再答，原始主诉与答案分开存储 |
| 科室依据 | matched_department、department_candidates[].source | 规则依据/用户自述/人口入口分别说明，候选方向可展开 | population_context的score=0不是低概率疾病，人口入口不作细科诊断 |
| 可靠性 | candidate_score_semantics、disease_prediction.abstained/abstain_reason | 展示“相对支持度”或“不足以判断”，给出缺失信息 | 余弦、相对分数、规则followup confidence均不得标为临床准确率 |
| 资源衔接 | resource_strategy、目录来源和更新时间 | 安全出口允许后再展示科室路径、医院目录、公开医生条目 | 不用检索模型最高分覆盖Safety，也不表示实时可接诊 |

目前前端已有安全状态、追问与分阶段说明。实际代码缺口：frontend/src/api/schemas.ts的triage.symptom_tags按string[]过滤，而后端实际为对象数组（tag/matched_terms/body_system等），因此这条解析路径丢掉对象标签；htriage_analysis虽原样保留，尚无完整类型化的证据链消费。后续应先补对象契约和对应解析验证，再实现症状证据卡，不能只加动画并宣称算法已展示。

演示验收建议选三条固定工程情境：普通咳嗽显示真实症状与方向；“宝宝2个月大”只显示缺主诉与追问；当前胸痛伴呼吸困难直接显示急诊出口。另展示一个unknown→补充回答→重新计算的过程，说明算法实际改变了什么。工程演示不标为临床验证。
