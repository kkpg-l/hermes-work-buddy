# Hermes Work Buddy 专家团部署方案 v4.1（完整实战版）

**版本**：v4.1（2026.06） · 取代 v4.0  
**适用环境**：WSL2 (Ubuntu 24.04) + Windows 11，单用户  
**核心组件**：Hermes Agent + DeepSeek API（云端）+ Llama.cpp + Qwen GGUF（可选本地）  
**设计原则**：极简 · 可灰度 · 可回滚 · 5 分钟首跑

---

## 0. 相对 v4.0 的变更摘要

| 模块 | v4.0 | v4.1 新增 |
|------|------|----------|
| 使用场景 | 无 | 4 个典型场景 + 推荐专家组合 |
| 生态联动 | 无 | HeartFlow / planning-workflow / cronjob |
| 专家角色 | 4 个固定 | 4 核心 + 8 扩展模板（UX/数据/营销/SEO 等） |
| 输出格式 | 纯文本 | 文件/PPT/飞书/Notion 4 种扩展 |
| 多轮对话 | 无 | session_search + fact_store 历史对比 |
| 路由策略 | 手动选专家 | 智能路由（自动选专家数量和组合） |
| 报告模板 | 固定四段 | 用户可自定义汇总格式 |
| Skill 组合 | 无 | grill-me → Work Buddy 等组合工作流 |

---

## 一、方案定位与适用边界

### 1.1 目标
为**单用户**在 WSL2 上部署一个「多专家并行分析」的本地 Work Buddy：
- 默认走云端 DeepSeek（成本低、能力强）
- 可选本地 Qwen3-4B 走 Llama.cpp（隐私 / 离线 / 省钱）
- 一个 Hermes 实例 + 一个专家团技能 + 一份主配置

### 1.2 不适用
- 多用户并发（无隔离、无计费）
- 金融/医疗等强合规场景（无审计链）
- 严格离线 + 国家级保密（无 HSM / 离线模型量化评估）

### 1.3 设计原则
1. **5 分钟首跑**：复制粘贴可上线
2. **失败默认安全**：本地服务挂了自动回云端
3. **可灰度**：先专家 1 个 → 全开 4 个 → 引入本地
4. **可回滚**：每个新组件有对应关闭命令

---

## 二、架构与组件

### 2.1 分层

```
┌────────────────────────────────────────────────────┐
│  Hermes Agent（调度中枢，Python 3.11+ venv）       │
│  ├─ 主对话 (CLI / Telegram Gateway / IDE Bridge)   │
│  └─ 专家团技能 expert-panel（delegate_task）       │
├────────────────────────────────────────────────────┤
│  L2 云端增强层（默认）                              │
│  └─ DeepSeek-V3.2-Flash / Pro（OpenAI 兼容 API）   │
├────────────────────────────────────────────────────┤
│  L1 本地推理层（可选，灰度启用）                    │
│  └─ Llama.cpp server ──► Qwen3-4B-Instruct Q4_K_M  │
├────────────────────────────────────────────────────┤
│  工具集（Hermes 内置）                              │
│  ├─ terminal · file · search (DuckDuckGo/Zhihu)    │
│  ├─ fact_store · session_search（替代 OpenViking）  │
│  └─ delegate_task（并行子 Agent）                  │
└────────────────────────────────────────────────────┘
```

### 2.2 数据流（一次「专家团」调用）

```
用户问题
  │
  ▼
[主协调员]  ──► 拆解 JSON 任务列表
  │
  ├─► [tech-expert]      ──┐
  ├─► [product-expert]   ──┤ 并行
  ├─► [business-expert]  ──┤ delegate_task
  └─► [research-expert]  ──┘
                            │
                汇总各专家 summary
                            │
                            ▼
                  [主协调员整合]
                            │
                            ▼
                  结构化最终报告
```

### 2.3 关键决策表

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 记忆 | Hermes `session_search` + `fact_store` | 免维护 OpenViking |
| 搜索 | DuckDuckGo + zhihu-global-search | 免付费 Tavily |
| 专家隔离 | 单 Profile + system prompt | 免 5 套配置 |
| 本地推理 | 可选 | 缺它不影响核心 |
| 调度 | `delegate_task` 并行 | Hermes 原生能力 |

### 2.4 依赖清单

| 组件 | 最低版本 | 用途 |
|------|---------|------|
| WSL2 | Ubuntu 24.04 | 运行环境 |
| Python | 3.11+ | Hermes / 技能脚本 |
| Hermes Agent | 当前主版本 | 调度中枢 |
| DeepSeek API Key | — | 云端推理 |
| Llama.cpp | latest | 仅本地推理 |
| Qwen3-4B-Instruct GGUF | Q4_K_M 量化 | 仅本地推理 |
| 磁盘 | 8 GB（仅云端）/ 12 GB（含本地模型） | — |
| 内存 | 8 GB（云端）/ 12 GB（含本地） | — |

---

## 三、5 分钟极速部署

### 3.1 前提条件检查

```bash
hermes --version || { echo "请先安装 Hermes"; exit 1; }
ls ~/.hermes/hermes-agent/venv/bin/python 2>/dev/null || echo "需要 venv"
curl -sSf https://api.deepseek.com >/dev/null && echo "DeepSeek OK" || echo "需配置代理"
[ -n "$DEEPSEEK_API_KEY" ] && echo "API Key OK" || echo "请 export DEEPSEEK_API_KEY=sk-xxx"
```

### 3.2 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/scripts/install.sh | bash
```

### 3.3 启动与首跑

```bash
hermes run "expert-panel --query=分析 WSL2 上 Hermes + DeepSeek 的最佳实践"
```

---

## 四、专家团技能

见 `skills/expert-panel/SKILL.md` 和 `skills/expert-panel/run.py`。

### 4.1 调试技巧

```bash
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
hermes run "expert-panel --query=xx --experts=tech"
hermes run "expert-panel --query=xx --mode=serial"
hermes run "expert-panel --query=xx --route=auto"
hermes run "expert-panel --query=xx --template=executive"
```

---

## 五、使用场景举例

### 场景 1：技术选型决策

**推荐专家组合**：`--experts=tech,product,business`

| 专家 | 分析角度 |
|------|----------|
| tech | 生态成熟度、TypeScript 支持、性能基准、社区活跃度 |
| product | 学习曲线、组件库丰富度、开发效率 |
| business | 招聘市场、长期维护风险、迁移成本 |

```bash
hermes run "expert-panel --query='团队选前端框架：React vs Vue vs Svelte' --experts=tech,product,business"
```

### 场景 2：产品方案评估

**推荐专家组合**：`--experts=product,business,ux,research`

```bash
hermes run "expert-panel --query='AI 写作助手产品方案评估' --experts=product,business,ux,research"
```

### 场景 3：技术架构审查

**推荐专家组合**：`--experts=tech,security`

```bash
hermes run "expert-panel --query='微服务架构审查' --experts=tech,security"
```

### 场景 4：市场进入策略

**推荐专家组合**：`--experts=business,research,marketing`

```bash
hermes run "expert-panel --query='东南亚 SaaS 市场进入策略' --experts=business,research,marketing"
```

---

## 六、与 Hermes 生态联动

### 6.1 HeartFlow 验证

```yaml
expert_panel:
  heartflow_validation: true
  heartflow_config:
    check_factual_claims: true
    check_logic_consistency: true
    min_confidence: 0.7
```

### 6.2 planning-workflow 联动

```bash
hermes run "planning-workflow --task='重构用户认证模块'"
hermes run "expert-panel --query='评审以上重构计划' --experts=tech,security"
```

### 6.3 定时任务（cronjob）

```bash
0 9 * * 1 hermes run "expert-panel --query='本周 AI 行业动态周报' --experts=research,business --template=weekly-report" >> ~/reports/weekly-$(date +\%Y\%m\%d).md
```

---

## 七、专家角色扩展模板

### 7.1 核心 4 专家

tech / product / business / research

### 7.2 扩展角色（8 个）

ux / data / marketing / seo / security / legal / ops / content

### 7.3 自定义角色

在 `run.py` 的 `EXPERT_SYSTEM` 添加一行即可，命名规范：小写英文 3-10 字符。

---

## 八、输出格式扩展

### 8.1 内置报告模板

default / executive / weekly-report / comparison

### 8.2 输出到文件

```bash
hermes run "expert-panel --query=xxx" | tee "~/reports/report-$(date +%Y%m%d%H%M).md"
```

### 8.3 输出到飞书 / Notion / PPT

详见完整文档。

---

## 九、多轮上下文与历史对比

```bash
hermes run "expert-panel --query='React vs Vue 最新分析' --compare-history=true"
```

---

## 十、智能路由策略

```bash
hermes run "expert-panel --query='AI 写作助手产品方案' --route=auto"
```

---

## 十一、自定义报告模板

```bash
mkdir -p ~/.hermes/skills/expert-panel/templates
cat > ~/.hermes/skills/expert-panel/templates/my-template.md <<'EOF'
## 结论
...
## 行动项
- [ ] ...
EOF
hermes run "expert-panel --query=xxx --template=my-template"
```

---

## 十二、与其他 Skill 组合

```bash
# 先质疑再分析
hermes run "grill-me --topic='我的想法'"
hermes run "expert-panel --query='基于上面的质疑分析...' --route=auto"

# 先发散再收敛
hermes run "brainstorming --topic='功能设计'"
hermes run "expert-panel --query='评估方案...' --route=auto"
```

---

## 十三~二十二

本地推理 / SOP / 验收 / 风险 / 成本 / 可观测性 / 安全 / 性能调优 / 迁移指南 / 版本演进

详见完整文档。

---

**v4.1 完。**
