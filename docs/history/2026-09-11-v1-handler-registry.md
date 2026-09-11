# 历史记录：v1 Handler Registry

日期：2026-09-11

v1 blueprint 的兼容 handler 现由根级 Flask composition 显式注册，adapter 在请求上下文中优先从 extension 解析，旧 lazy import 作为 fallback 保留。新增 registry contract 后全量测试为 109/109，v1 API、稳定快照和 Safety Evaluation 基线未变化。
