# Symptom Disease Model

这是一个“症状标签 -> 疾病类别”训练项目。当前版本使用标准库实现多项式朴素贝叶斯，不需要额外安装 Python 包。

重要提醒：这个项目只能用于数据建模、分诊辅助或学习演示，不能替代医生诊断。真实使用前需要高质量医学标注数据、严格验证和合规审查。

## 目录

- `data/disease_symptom_structured_41diseases_long.csv`: 推荐训练数据，41 个疾病标签，304 条样本，131 个症状标签
- `data/disease_symptom_training_long.csv`: 更宽覆盖训练数据，标签更多但噪声更大
- `data/disease_symptom_dataset_report.md`: 数据集说明
- `data/disease_symptom_sources.json`: 数据来源和许可证说明
- `train.py`: 训练并保存模型
- `predict.py`: 加载模型并预测
- `app.py`: 疾病名称预测 API 服务
- `models/symptom_disease_41_nb.json`: 推荐主模型
- `models/symptom_disease_full_nb.json`: 宽覆盖实验模型

## 数据格式

CSV 必须包含 `disease` 列，并包含以下任意一列症状字段：

- `symptom_tags`
- `symptoms`
- `symptom_text`

示例：

```csv
disease,symptoms
common_cold,runny_nose;sneezing;sore_throat
influenza,high_fever;muscle_ache;dry_cough
```

`symptoms` 可以用英文分号、竖线、逗号、中文逗号、中文分号或顿号分隔。建议所有症状标签使用稳定的标准词表，例如 `high_fever`、`dry_cough`，不要同一个症状一会儿写“发热”、一会儿写“发烧”。

## 训练

```powershell
python train.py --data data\disease_symptom_structured_41diseases_long.csv --model models\symptom_disease_41_nb.json --test-size 0.25 --min-symptom-df 2
```

如果你的系统里没有 `python` 命令，可以使用 Codex 内置 Python：

```powershell
& 'C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' train.py --data data\disease_symptom_structured_41diseases_long.csv --model models\symptom_disease_41_nb.json --test-size 0.25 --min-symptom-df 2
```

本次主模型训练结果：

- 训练样本：230
- 测试样本：74
- 疾病类别：41
- 症状词表：131
- Top-1 准确率：0.973
- Top-3 准确率：1.000

## 预测

```powershell
python predict.py --model models\symptom_disease_41_nb.json --symptoms "headache|nausea|spinning_movements|loss_of_balance|unsteadiness" --top-k 5
```

输出每行是：疾病标签和模型估计概率。

如果系统只需要疾病名称：

```powershell
python predict.py --symptoms "headache|nausea|spinning_movements|loss_of_balance|unsteadiness" --name-only
```

输出：

```text
(vertigo) Paroymsal Positional Vertigo
```

## 接入常医智达

启动 API 服务：

```powershell
cd D:\symptom-disease-model
python app.py --host 127.0.0.1 --port 5002
```

如果系统里没有 `python` 命令：

```powershell
cd D:\symptom-disease-model
& 'C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B app.py --host 127.0.0.1 --port 5002
```

常医智达调用：

```http
POST http://127.0.0.1:5002/predict
Content-Type: application/json; charset=utf-8

{
  "symptoms": ["打喷嚏", "头晕", "发热"]
}
```

返回：

```json
{
  "disease": "普通感冒"
}
```

当前接口支持中文口语症状映射，例如：

```text
打喷嚏 -> continuous_sneezing
发热/发烧/高烧 -> high_fever
低烧 -> mild_fever
头晕 -> dizziness
咳嗽 -> cough
流鼻涕 -> runny_nose
鼻塞 -> congestion
喉咙痛/嗓子疼 -> throat_irritation
乏力/没力气 -> fatigue
```

如果系统想知道“患者症状是否太少、还应该追问什么”，请求里加 `details: true`：

```json
{
  "symptoms": ["打喷嚏", "头晕", "发热"],
  "details": true
}
```

返回会包含：

```json
{
  "disease": "普通感冒",
  "need_more_info": true,
  "known_symptoms": ["连续打喷嚏", "头晕", "高烧"],
  "follow_up_symptoms": ["乏力", "头痛", "全身不适", "淋巴结肿大", "胸痛"]
}
```

普通模式仍然只返回 `disease`，不会影响只需要疾病名称的接入。

## 换成你的真实数据

1. 用你的数据替换或新增一个 CSV。
2. 确保每行是一条病例或样本，`disease` 是标注疾病，`symptoms` 是症状标签列表。
3. 每个疾病类别最好至少有几十到几百条样本；类别越多，通常需要更多数据。
4. 重新运行 `train.py`。

## 后续可升级方向

- 增加年龄、性别、病程、体征、检查结果等特征。
- 换成 scikit-learn 的 Logistic Regression、Linear SVM、Random Forest 或 XGBoost。
- 输出 Top-K 疾病并增加置信度阈值，低置信度时提示人工复核。
- 用独立测试集评估准确率、召回率、混淆矩阵和各疾病类别表现。
