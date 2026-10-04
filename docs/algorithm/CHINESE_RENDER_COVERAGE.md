# 中文工程代理输入覆盖（W62，2026-10-04）

当前同源渲染链不是完整中文主诉输入域。结构化304样本包含131种症状码、2325次出现；48种有中文name，83种没有，渲染器会原样保留英文码。

| 完整分母项 | 当前审计结果 |
|---|---:|
| 原始结构化样本 | 304 |
| 仅使用已登记中文name的样本 | 71 |
| 含英文码回退的样本 | 233 |
| 中文name出现次数 | 1629 |
| 英文码回退出现次数 | 696（29.94%） |
| 有name但现有alias解析未找回自身code | 12种、238次出现 |

缺name的高频code包括irritability、excessive_hunger、lethargy；已有name未被现有alias找回的高频code包括loss_of_appetite、dark_urine、swelled_lymph_nodes。这是词表与渲染覆盖观察，不是医学翻译错误结论，未核验临床语义。

证据为`evaluation/core_exploration/results/versioned-challenges/w62-chinese-render-coverage/`：prepared/started/result/completed记录schema3声明身份稳定，全部行与code保留。临床标签核验数0，clinical_accuracy=null；failed=0只表示审计执行契约，不表示输入域完整。

旧45job中文代理结果保留，未重训、未按test选择模型或校准，未将当前parser状态回填成旧实验状态。当前审计的238次未找回不能当作旧模型错误数。那些结果仍是合成工程代理，不能视为真实中文临床分类证据。

后续先保持完整分母，分别披露有中文name与英文回退的输入范围；不删除233个混合输入来制造高覆盖，不未经来源核验补83个医学翻译。已登记name与alias对照可先做独立研究桥接实验，但不得自动改正式字典或将桥接回收率当临床准确率。要判断算法泛化与校准仍需要符合项目边界的独立中文标签证据。

W63仅研究构造对照：48个结构化已有name×4状态192契约，原alias48失败、候选0失败，新增14条已登记name的声明关联。name文件总计50项，另excessive_thirst/high_blood_pressure不在该结构化词表；首whole50/200范围偏差结果保留并标记不接受作192验收，最终v2范围明确。正式字典未改，没有模型拟合或临床性能结果，英文回退缺口仍在。按name自身构造的契约回收属于工程一致性，不是独立语义验证。
