# MedJourney 数据使用依据确认草稿（未发送）

用途：解决独立中文主诉→科室标签评测的数据缺口。当前作者仓库没有明确数据许可证；本文件不是已获得授权的证明，也不包含原始数据。

继续轮8修正：原论文checklist5 P22明确开放数据用于复现实验，故本地只读资料审核/不拟合对照不以发送本草稿为前置条件。当前仍记许可证unspecified，不推导训练/再分发权利。只读结构预检500 NDJSON已完成，未保存原病例、未训练/发布数据；训练或再分发的使用依据仍另核。本草稿未发送。

2026-10-04用户已要求agent自行审核：本草稿保留为候选资料，不再作为继续核心算法的必经步骤；没有发送。技术、翻译及文献审核自行完成，许可按公开条款或实际授权确定。当前可使用的CC0医师虚构情境继续用于技术评估。

建议收件方：通讯作者 Yefeng Zheng，`yefengzheng@westlake.com.cn`。

公开联系方式依据：[论文首页](https://papers.nips.cc/paper_files/paper/2024/file/9f80af32390984cb709cdeb014d0df41-Paper-Datasets_and_Benchmarks_Track.pdf)，2026-10-04重新核对。此为论文公开地址，未验证投递成功；没有向任何作者发送消息。发送方式与发送授权待用户明确。

主题：Request for permission to use MedJourney Department Recommendation data in an academic competition prototype

Dear MedJourney authors,

We are developing an explainable, safety-aware medical resource routing prototype for the 2026 AIC AI+Medicine competition. We would like to evaluate department routing using the 500 clinician-authored fictional complaints in your Department Recommendation dataset (`data/basic/dr.json`).

Could you confirm the dataset's license or provide written permission for academic research and competition use? Please also clarify whether local evaluation, training on a separately declared training partition, reporting aggregate results, and distributing a reproduction package containing the permitted data or derived inputs are allowed. If redistribution is restricted, we can keep the original data out of the package and provide only retrieval instructions and aggregate results.

We will cite the original publication, document any transformations and department mappings, preserve case-level split boundaries, and distinguish prototype benchmark results from clinical validation. We will not use patient records or deploy the prototype as a clinical decision system.

Thank you for your help.

Best regards,
The competition project team

## 获得回复后核对

- 明确适用文件和版本、许可或授权主体、允许的训练/评测/参赛/再分发范围。
- 保留真实书面使用依据及引用；未获回复不补写许可。
- 先冻结任务/科室映射/病例与近重复分组、train/cal/test职责，再使用数据；未见测试保留完整分母。
- 该数据没有风险等级标签，不能用于声明急症召回或验证代谢/哮喘医疗策略；这部分仍需另有审核证据。
