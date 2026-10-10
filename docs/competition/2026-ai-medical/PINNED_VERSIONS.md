# 冻结复现版本（2026-10-10 本机实测）

仅登记，不改变 `requirements*.txt` 与 `package-lock.json`。评审按 README 短路径安装时，以本表核对版本漂移。

| 组件 | 版本 |
| --- | --- |
| Python | 3.11.9 |
| Flask | 3.1.3 |
| flask-cors | 6.0.5 |
| pytest | 8.4.2 |
| Node | 24.12.0 |
| npm | 11.6.2 |
| React / ReactDOM | 19.2.8（见 `frontend/package.json`） |
| TypeScript | 6.0.3（见 `frontend/package.json`） |
| Vite | 8.2.2（见 `frontend/package.json`） |
| Playwright | 1.63.0（dev，见 `frontend/package.json`） |

本机验证：pytest 1043/1043、前端 21/21 + typecheck + build、浏览器 E2E 96/96 + hooks 4/4、Safety142（recall1.0/under0/over0/FN0）、数据扫描 31/186。`requirements.txt` 仅设下界，评审若装出其他版本且回归数字变化，以本表为准报漂移，不静默接受。
