# 胸闷旧映射复核（W34）

旧词表把胸闷、气短、呼吸困难均映到breathlessness，症状中文名为呼吸困难。原别名、中文名、模型JSON全部未改，before/after全JSON/CSV哈希相同。

2026-10-03访问[NHLBI症状页](https://www.nhlbi.nih.gov/health/asthma/symptoms)及[NHS哮喘页](https://www.nhs.uk/conditions/asthma/)：分别列出chest tightness与shortness of breath。**不能仅由并列列表判定旧映射医学错误。** 补查[ATS官方dyspnea声明](https://pmc.ncbi.nlm.nih.gov/articles/PMC5448624/)：胸部紧缩感可以属于不同呼吸不适感之一。这支持二者存在关联，同时不提供本项目中文二值特征的无条件等价认证。

本轮的工程问题是同码丢失语义：没有胸闷但呼吸困难，旧adapter把breathlessness同时记录阴性与阳性并拒答。否认较细的感受不能直接当作否认所有呼吸不适。这里没有患者标签或医学诊断，也没有依据将胸闷重新编码为另一疾病。

保守处理仅在辅助模型隔离待核验的胸闷关联，不参与Safety：

- 肯定/未知胸闷整条aux拒答，明确说明含义待核验；不悄悄删该描述后给出部分预测。
- 明确否认胸闷不进入该隔离；剩余真实咳嗽/呼吸困难保留，不被旧同码阴性污染。
- 原规则胸闷标签、Safety原文/阈值、就医方向不改；8对照前后Safety状态与科室完全一致，明确呼吸急症仍在先。

新8项协议6失败→0失败，仅隔离与证据状态契约。这个选择可能拒绝有用的dyspnea描述、降低辅助接受率，不能称临床准确率改善或旧词表已被判错。精确/上下位语义与真实中文标签仍需独立核验；其他旧别名也未被本轮认证。

W32的196输入服务统计是旧v2.7源码历史结果，本轮改变接受策略后不能直接当当前接受率，未重放或覆盖。

证据：schema2 w34-chest-alias-before/after，result SHA分别88c142458f8e3f6f6ec6f18ca8963c1b91043be49640f7b4b4d25090885e6daf与03b95efdf2a0e8b883224e429138c250fb7b1044ee4e6fdf5d937df650abbe85。
