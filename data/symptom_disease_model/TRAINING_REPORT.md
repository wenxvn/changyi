# Symptom Disease Model Training Report

训练日期：2026-06-17

## 使用的数据

主模型使用 `disease_symptom_structured_41diseases_long.csv`：

- 样本数：304
- 疾病类别：41
- 症状标签数：131
- 数据来源：`shanover_disease_symptoms_prec_full`

同时额外训练了一个宽覆盖实验模型，使用 `disease_symptom_training_long.csv`，并过滤少于 5 条样本的疾病标签。该模型覆盖更多标签，但数据噪声更大，效果明显低于主模型。

## 主模型

模型文件：`models\symptom_disease_41_nb.json`

算法：多项式朴素贝叶斯

评估方式：按疾病类别分层切分，测试集比例 0.25。

结果：

- 训练样本：230
- 测试样本：74
- 疾病类别：41
- 症状词表：131
- Top-1 准确率：0.973
- Top-3 准确率：1.000

## 宽覆盖实验模型

模型文件：`models\symptom_disease_full_nb.json`

结果：

- 训练样本：1,264
- 测试样本：425
- 疾病类别：58
- 症状词表：237
- Top-1 准确率：0.398
- Top-3 准确率：0.544

## 示例预测

输入症状：

```text
headache|nausea|spinning_movements|loss_of_balance|unsteadiness
```

输出 Top-5：

```text
(vertigo) Paroymsal Positional Vertigo    0.9609
Malaria                                  0.0064
Typhoid                                  0.0049
Hypertension                             0.0043
Dengue                                   0.0042
```

## 注意

该模型只能作为数据建模或分诊辅助原型，不能作为临床诊断系统使用。若用于真实业务，应补充医学专家审核、独立测试集评估、低置信度人工复核和合规说明。
