# 评估计划

## 医学辅助评估

Baseline A 为关键词/规则，Baseline B 为当前 Multinomial Naive Bayes，Baseline C 为简单线性模型（环境和数据允许时），Full 为规则 + 模型 + Safety Gate + Follow-up。数据按 symptom-set fingerprint 分组，避免相同或高度相似症状组合跨 train/test。

报告：Top-1、Top-3、Macro Precision/Recall/F1、Per-class Recall、Coverage、Abstention、Brier、ECE、混淆矩阵和 reliability diagram。

## Safety Evaluation Set

安全评估独立运行 `python -m evaluation.safety.evaluate_safety`，case set 覆盖心血管急症、卒中、呼吸困难、急腹症、严重外伤、意识异常、过敏、孕产急症、儿童危重、眼科急症、心理危机、否定、口语和信息不足。报告 Red Flag Recall、Under-triage Rate、Over-triage Rate 和 Emergency False Negative；当前基线中的 `review_required` case 不视为通过，指标不手工填写。

## 安全评估

固定覆盖心血管急症、卒中、呼吸困难、急腹症、外伤、意识异常、过敏、孕产急症、儿童危重、眼科急症、心理危机、否定/口语/模糊表达和信息不足；每次红旗规则修改都必须跑回归。

## 推荐评估

按 A 仅科室、B 加医院能力、C 加医生、D 加距离、E 加交通、F 加 Resource Fit、G Full 做消融。若没有临床 ground truth，明确标记 `prototype/offline evaluation`，只报告 NDCG@K、Hit@K、平均距离、顶级专家过度使用率、普通病例三甲集中率和急症适配率。

## 可复现性

每个结果绑定 app、triage rules、ranking、model、dataset、region pack 版本、数据 hash、配置 hash、随机种子和 git commit；图表只能从 raw result 生成。
