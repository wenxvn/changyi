# 常医智导前端迁移计划：本地演示资料与分析历史

状态：已完成  
日期：2026-09-11  
变更等级：L2（前端本地偏好、脱敏历史和 Profile route；不改变医学规则、推荐排序或后端数据）

## 目标

完成重构提示词中的 F11 Profile/History 首版：为本地演示提供可理解的资料入口、明确的当前浏览器存储边界和可选的最近分析摘要，使用户可以回看演示路径，但不把原始症状文本或身份资料写入本地历史。

## 非目标

- 不新增登录、账号、姓名、联系方式、患者标识、病历或云端同步。
- 不保存原始症状、追问答案、模型原文、推荐解释或任何可复原用户输入的字段。
- 不改变分诊状态、红旗规则、追问组合、推荐排序和后端 API 契约。
- 不新增收藏、预约、导航、电话外呼或生产隐私承诺。

## 契约与安全边界

- `/profile` 是本地演示资料页，不代表已登录用户中心。
- 历史功能默认关闭；用户主动开启后，最多保留 8 条摘要，仅使用版本化 `localStorage` 键。
- 摘要只包含生成时间、固定演示场景、服务端返回的分诊状态/标签和匹配科室；不会接收或存储输入文本。
- 页面显示“仅保存在当前浏览器”，提供关闭记录和分步清除历史；存储不可用时静默降级为空状态。
- 所有跨页面同步通过前端 state module 的受控事件完成，页面不直接访问 `localStorage`。

## 实施步骤

1. 增加本地演示资料/历史 state module，定义白名单、校验、容量限制和安全降级。
2. 增加 `/profile` route 和 Profile/History 页面；接入 header profile button，提供空态、开关、清除和免责声明。
3. 在 triage 完成且历史已开启时写入脱敏摘要；不在追问中间态写入原始输入。
4. 增加 frontend boundary assertions，更新架构、scorecard、risk、status、progress、history、review、UI registry 和 memory。
5. 运行 typecheck、boundary/test/build、Python 回归、静态检查和 Profile desktop/mobile/keyboard 运行态检查。

## 验收标准

- `/profile` 可通过 header profile button 和浏览器后退访问；移动端无横向溢出。
- 默认关闭时没有历史；开启后只记录脱敏摘要，关闭后不再新增；清除动作需要二次确认。
- 页面和测试明确证明没有原始症状/追问答案/身份字段落入 history schema。
- legacy `/`、现有 `/api/v1`、Emergency 独立路径和推荐快照保持不变。

## 回滚

移除 Profile route/page、`demoProfile` state module、triage 记录调用、样式和对应文档即可；不影响后端、legacy 页面、既有分析请求和推荐结果。
