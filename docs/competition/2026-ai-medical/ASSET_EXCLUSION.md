# 参赛包素材排除清单（2026-10-10 实测，非法律结论）

依据官方“引用注明 + 合法使用依据”要求，以下素材**不得**进入技术报告截图、演示视频、答辩 PPT、网盘代码包：

| 素材 | 实测状态 | 处理 |
| --- | --- | --- |
| 275 张医生照片（`data/resource_provenance/doctor_photos.json`） | 275/275 `license_status=not_recorded`、`original_source_url` 0 条；274 `LEGACY_EXACT_MATCH`、1 `MANUAL_CONFIRMED`；`reuse_status` 全为 `display_only_legacy` | 参赛包与录屏全部排除或替换为有依据素材；本地演示展示保留来源状态提示，不包装为已授权 |
| 医院目录（`data/regions/320400/`） | `manifest`/`catalog` 仍 `provisional`，`source_url=null`、`license_status=not_recorded` | 报告中如实披露为待核验目录，不写成官方事实 |
| 公交数据 186 异常 | `PLACEHOLDER_TIMESTAMP` 180 + `TIME_ORDER` 6，已隔离 `PROVISIONAL rankable=False` 不进排序 | 报告披露限制，不修复造数 |
| `frontend/dist/`、`.venv/`、`node_modules/`、`.git/objects/pack/tmp_pack_*` | 构建产物/环境/中断下载残留 | 不得进网盘包 |

本清单只登记现状；使用依据须由真实证据补齐后才能把条目移出清单，任何移出需留来源+许可+时间记录。
