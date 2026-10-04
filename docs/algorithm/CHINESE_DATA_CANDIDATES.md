# 中文语料适用度核查（2026-10-02）

本轮只核查作者发布的元数据、许可及任务定义，未导入外部患者文本或咨询记录。

| 候选 | 已核验信息 | 核心算法适用度 |
|---|---|---|
| [LCMDC 作者仓库](https://github.com/anord-wang/Chinese-Medical-Dialogue-System)、[Zenodo](https://zenodo.org/records/13771008) | 作者提供分级分诊任务，说明 raw 文件包含患者提问、医生回答和基本信息；[Zenodo API](https://zenodo.org/api/records/13771008) 返回 cc-by-4.0、open | 比现有英文症状码更接近中文任务；原始咨询记录不能直接纳入当前项目。后续必须明确去标识处理、是否允许此类记录、初诊主诉与诊后咨询区分，以及粗/细科室到常州目录的映射 |
| [Huatuo26M-Lite 数据卡](https://huggingface.co/datasets/FreedomIntelligence/Huatuo26M-Lite)、[作者仓库](https://github.com/FreedomIntelligence/Huatuo-26M) | Apache-2.0；数据卡显示约178k行、16个label值，字段有question/answer/related_diseases；作者说明Lite经过清理和改写并包含科室字段 | 可作为中文分类研究候选。推断：问答类别/咨询科室不等于经过独立审核的初诊就医科室；诊断已知、治疗咨询、急症初诊需要分层，answer与related_diseases不能当模型输入或混进测试标签生成 |

采用前的技术方案：只评估必要的脱敏主诉与科室字段；处理与识别记录进入独立隔离流程；拒绝身份、联系信息、真实病历与不明使用依据的数据进入此仓库；不训练诊疗回答生成器。冻结按来源/文本近重复组/时间划分的独立测试集；先跑中文char-TFIDF/词级稀疏模型，规模与证据足够后再谈中文编码器。

这是数据候选与接入协议，**没有对应训练结果**。已有模型94%左右的英文混合文本内部结果，不能借中文数据卡来宣称完成中文验证。
