---
name: expert-panel
description: Work Buddy 专家团 - 多专家并行分析与报告生成
trigger: 专家团|expert panel|分析|研究|报告|评估|方案
---

# Expert Panel Skill v4.1

调用多个专家子 Agent 并行分析问题，最终汇总为结构化报告。

## 使用方式

```bash
# 基本用法
hermes run "expert-panel --query=你的问题"

# 指定专家
hermes run "expert-panel --query=xxx --experts=tech,product"

# 智能路由（自动选专家）
hermes run "expert-panel --query=xxx --route=auto"

# 使用报告模板
hermes run "expert-panel --query=xxx --template=executive"

# 历史对比
hermes run "expert-panel --query=xxx --compare-history=true"

# 串行调试
hermes run "expert-panel --query=xxx --mode=serial"
```

## 专家角色

### 核心 4 专家

| 专家 | 代号 | 职责 |
|------|------|------|
| 技术专家 | tech | 技术架构、代码、技术选型 |
| 产品专家 | product | 产品设计、需求、竞品分析 |
| 商业专家 | business | 商业模式、市场分析、财务预测 |
| 研究专家 | research | 文献综述、系统分析、深度研究 |

### 扩展角色

| 专家 | 代号 | 职责 |
|------|------|------|
| UX 专家 | ux | 交互设计、信息架构、可用性 |
| 数据专家 | data | 数据分析、指标体系、A/B 测试 |
| 营销专家 | marketing | 增长策略、内容营销、品牌定位 |
| SEO 专家 | seo | 关键词策略、技术 SEO、内容优化 |
| 安全专家 | security | 应用安全、基础设施安全、合规 |
| 法律专家 | legal | 数据隐私、知识产权、合同 |
| 运维专家 | ops | CI/CD、监控、容灾 |
| 内容专家 | content | 文案、叙事、传播策略 |

## 工作流程

1. **plan**：主协调员拆解为 JSON 任务列表
2. **fan-out**：`delegate_task` 并行/串行执行
3. **aggregate**：按模板汇总报告

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --query | （必填） | 要分析的问题 |
| --experts | tech,product,business,research | 逗号分隔的专家列表 |
| --route | （空） | 设为 `auto` 启用智能路由 |
| --template | default | 报告模板：default/executive/weekly-report/comparison/自定义 |
| --compare-history | false | 设为 `true` 启用历史对比 |
| --mode | parallel | parallel 或 serial |

## 降级策略

- `delegate_task` 失败 → 退化为单专家
- 拆解 JSON 失败 → 退化为整段 prompt
- 本地模型 OOM → 回退云端

## 调试

```bash
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
hermes run "expert-panel --query=xxx --experts=tech"
```

## 自定义模板

在 `~/.hermes/skills/expert-panel/templates/` 下创建 `.md` 文件即可：

```bash
mkdir -p ~/.hermes/skills/expert-panel/templates
cat > ~/.hermes/skills/expert-panel/templates/my-template.md <<'EOF'
## 结论
...
## 行动项
- [ ] ...
EOF
```

## 与其他 Skill 组合

```bash
# 先质疑再分析
hermes run "grill-me --topic='我的想法'"
hermes run "expert-panel --query='基于上面的质疑分析...' --route=auto"

# 先发散再收敛
hermes run "brainstorming --topic='功能设计'"
hermes run "expert-panel --query='评估方案...' --route=auto"
```
