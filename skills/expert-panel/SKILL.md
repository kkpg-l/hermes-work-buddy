---
name: expert-panel
description: Work Buddy 专家团 - 多专家并行分析与报告生成
trigger: 专家团|expert panel|分析|研究|报告|评估|方案
---

# Expert Panel Skill v4.0

调用多个专家子 Agent 并行分析问题，最终汇总为结构化报告。

## 使用方式

```bash
# 基本用法
hermes run "expert-panel --query=你的问题"

# 指定专家
hermes run "expert-panel --query=xxx --experts=tech,product"

# 串行调试
hermes run "expert-panel --query=xxx --mode=serial"
```

## 专家角色

| 专家 | 代号 | 职责 |
|------|------|------|
| 技术专家 | tech | 技术架构、代码、技术选型 |
| 产品专家 | product | 产品设计、需求、竞品分析 |
| 商业专家 | business | 商业模式、市场分析、财务预测 |
| 研究专家 | research | 文献综述、系统分析、深度研究 |

## 工作流程

1. **plan**：主协调员拆解为 JSON 任务列表
2. **fan-out**：`delegate_task` 并行/串行执行
3. **aggregate**：汇总为 摘要/详细/对比/结论 四段

## 降级策略

- `delegate_task` 失败 → 退化为单 `research-expert`
- 拆解 JSON 失败 → 退化为整段 prompt
- 本地模型 OOM → 回退云端

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --query | （必填） | 要分析的问题 |
| --experts | tech,product,business,research | 逗号分隔的专家列表 |
| --mode | parallel | parallel 或 serial |

## 调试

```bash
# 开启 debug 输出中间 JSON
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"

# 单独跑某专家
hermes run "expert-panel --query=xxx --experts=tech"
```
