# ADR-0017：以 Infrastructure Adapter 封装症状疾病模型

状态：已接受  
日期：2026-09-11  
范围：`backend/app/infrastructure/models/symptom_disease.py` 与 `app.py` legacy model wrapper

## 背景

`app.py` 顶层同时负责模型文件路径、sys.path、标签模块导入、lazy runtime 错误缓存和推理参数。prediction endpoint 虽已有 application service，但底层模型 adapter 仍与 Flask composition root 混杂。

## 决定

- 将文件加载、runtime 缓存和 inference 参数封装为无 Flask 的 `SymptomDiseaseModelAdapter`。
- `predict_disease_name` 继续保留为兼容函数，代理 adapter；既有详情/非详情输出、top-k 和降级完全保持。
- 通过 injected runtime 让 adapter 可在无真实模型文件的 unit test 中验证，但不替换默认本地模型。

## 影响

正向影响：模型加载失败与推理参数有独立测试边界，未来模型版本化/替换可不触碰 HTTP 层。

代价：当前 adapter 仍依赖仓库内既有 Python inference/labels 模块，模型质量、低置信度和医学审核问题不因重构改变。

## 回滚

恢复 `app.py` 内原模型 loader/predictor 逻辑即可，不涉及数据或模型回滚。
