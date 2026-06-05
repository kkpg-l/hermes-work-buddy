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
# 1. Hermes 可用
hermes --version || { echo "请先安装 Hermes"; exit 1; }

# 2. 虚拟环境正常
ls ~/.hermes/hermes-agent/venv/bin/python 2>/dev/null || echo "需要 venv"

# 3. 网络
curl -sSf https://api.deepseek.com >/dev/null && echo "DeepSeek OK" || echo "需配置代理"

# 4. API Key 已写入环境
[ -n "$DEEPSEEK_API_KEY" ] && echo "API Key OK" || echo "请 export DEEPSEEK_API_KEY=sk-xxx"
```

### 3.2 一键安装

```bash
# 方式一：curl
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/scripts/install.sh | bash

# 方式二：git clone
git clone https://github.com/kkpg-l/hermes-work-buddy.git
cd hermes-work-buddy && bash scripts/install.sh
```

### 3.3 启动与首跑

```bash
# 拉起专家团
hermes run "expert-panel --query=分析 WSL2 上 Hermes + DeepSeek 的最佳实践"

# 验证
# 期望：返回包含"摘要/详细分析/各专家观点/结论"四段的报告
```

---

## 四、专家团技能（完整代码）

### 4.1 SKILL.md

见 `skills/expert-panel/SKILL.md`。

### 4.2 run.py（v4.1 修正版）

见 `skills/expert-panel/run.py`。

### 4.3 调试技巧

```bash
# 看中间 JSON
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"

# 只跑技术专家
hermes run "expert-panel --query=对比 LangChain 和 Hermes --experts=tech"

# 串行（排查并行问题）
hermes run "expert-panel --query=xx --mode=serial"

# 使用智能路由（自动选专家）
hermes run "expert-panel --query=简单代码问题 --route=auto"

# 使用自定义报告模板
hermes run "expert-panel --query=xxx --template=executive"
```

---

## 五、使用场景举例

### 场景 1：技术选型决策

**问题**：「我们团队要选一个前端框架，对比 React / Vue / Svelte」

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

**问题**：「评估做一个 AI 写作助手的产品方案」

**推荐专家组合**：`--experts=product,business,ux,research`

| 专家 | 分析角度 |
|------|----------|
| product | 目标用户、核心功能、差异化 |
| business | 商业模式、定价策略、市场规模 |
| ux | 交互流程、关键体验节点 |
| research | 竞品分析、行业趋势 |

```bash
hermes run "expert-panel --query='AI 写作助手产品方案评估' --experts=product,business,ux,research"
```

### 场景 3：技术架构审查

**问题**：「审查我们的微服务架构方案，找出潜在问题」

**推荐专家组合**：`--experts=tech,security`

```bash
hermes run "expert-panel --query='微服务架构审查：服务拆分、通信、部署方案' --experts=tech,security"
```

### 场景 4：市场进入策略

**问题**：「分析进入东南亚 SaaS 市场的可行性」

**推荐专家组合**：`--experts=business,research,marketing`

```bash
hermes run "expert-panel --query='东南亚 SaaS 市场进入策略' --experts=business,research,marketing"
```

---

## 六、与 Hermes 生态联动

### 6.1 HeartFlow 验证

HeartFlow 是 Hermes 的执行验证机制，可在专家团产出后自动校验结论的合理性。

```yaml
# config.yaml 中启用
expert_panel:
  heartflow_validation: true
  heartflow_config:
    check_factual_claims: true    # 事实性声明校验
    check_logic_consistency: true  # 逻辑一致性检查
    min_confidence: 0.7           # 最低置信度
```

```python
# run.py 中集成（aggregate 步骤后追加）
if os.environ.get("HERMES_HEARTFLOW_ENABLED") == "1":
    validation_prompt = f"""请校验以下报告中的事实性声明和逻辑一致性：
{final_report}

输出 JSON：
{{"issues": [{{"claim": "...", "type": "factual|logic", "severity": "high|medium|low", "suggestion": "..."}}]}}"""
    validation = delegate_task(goal=validation_prompt, toolsets=["terminal"])
    # 如有 high severity 问题，追加修正说明
```

### 6.2 planning-workflow 联动

将专家团嵌入 Hermes 的 planning-workflow，实现「先规划再执行」：

```
用户需求
  │
  ▼
[planning-workflow]  ──► 生成执行计划
  │
  ▼
[expert-panel]  ──► 对计划做多专家评审
  │
  ▼
[planning-workflow]  ──► 根据评审修正计划
  │
  ▼
[执行]
```

```bash
# 先让 planning-workflow 生成计划
hermes run "planning-workflow --task='重构用户认证模块'"

# 再用专家团评审
hermes run "expert-panel --query='评审以下重构计划：[计划内容]' --experts=tech,security"
```

### 6.3 定时任务（cronjob）

利用 Hermes cronjob 或系统 crontab 实现定期分析：

```bash
# 每周一早 9 点生成行业周报
crontab -e
# 添加：
0 9 * * 1 HERMES_FORCE_CLOUD=1 hermes run "expert-panel --query='本周 AI 行业动态周报' --experts=research,business --template=weekly-report" >> ~/reports/weekly-$(date +\%Y\%m\%d).md 2>&1

# 每天早 8 点检查技术栈更新
0 8 * * * hermes run "expert-panel --query='今日技术栈更新检查' --experts=tech --route=auto" >> ~/reports/daily-$(date +\%Y\%m\%d).md 2>&1
```

---

## 七、专家角色扩展模板

### 7.1 核心 4 专家（内置）

| 代号 | 角色 | system prompt 要点 |
|------|------|-------------------|
| tech | 技术专家 | 架构/代码/选型，引用证据 |
| product | 产品专家 | 需求/设计/竞品，引用证据 |
| business | 商业专家 | 模式/市场/财务，引用证据 |
| research | 研究专家 | 综述/系统分析，引用来源 |

### 7.2 扩展角色模板

在 `run.py` 的 `EXPERT_SYSTEM` 字典中添加即可启用：

```python
EXPERT_SYSTEM = {
    # --- 核心 4 专家 ---
    "tech":     "你是资深技术专家（架构 / 代码 / 选型），输出结构化、引用证据。",
    "product":  "你是资深产品专家（需求 / 设计 / 竞品），输出结构化、引用证据。",
    "business": "你是资深商业分析专家（模式 / 市场 / 财务），输出结构化、引用证据。",
    "research": "你是资深研究专家（综述 / 系统分析），输出结构化、引用来源。",

    # --- 扩展角色 ---
    "ux":         "你是资深 UX 设计专家（交互设计 / 信息架构 / 可用性测试），输出结构化，引用设计原则和用户研究数据。",
    "data":       "你是资深数据专家（数据分析 / 指标体系 / A/B 测试），输出结构化，引用数据驱动方法论。",
    "marketing":  "你是资深营销专家（增长策略 / 内容营销 / 品牌定位），输出结构化，引用市场数据和案例。",
    "seo":        "你是资深 SEO 专家（关键词策略 / 技术SEO / 内容优化），输出结构化，引用搜索引擎最佳实践。",
    "security":   "你是资深安全专家（应用安全 / 基础设施安全 / 合规），输出结构化，引用 OWASP/CVE 等权威来源。",
    "legal":      "你是资深法律合规专家（数据隐私 / 知识产权 / 合同），输出结构化，引用相关法规条文。",
    "ops":        "你是资深运维专家（CI/CD / 监控 / 容灾），输出结构化，引用 SRE 最佳实践。",
    "content":    "你是资深内容专家（文案 / 叙事 / 传播策略），输出结构化，引用传播学和内容营销方法论。",
}

ALL_EXPERTS = tuple(EXPERT_SYSTEM.keys())
```

### 7.3 自定义角色指南

创建新专家只需 2 步：

1. 在 `EXPERT_SYSTEM` 添加一行：`"代号": "角色描述 + 输出要求"`
2. 在 `ALL_EXPERTS` 元组中添加代号

**命名规范**：
- 代号：小写英文，3-10 字符，语义明确
- 描述模板：`你是资深{领域}专家（{子领域1} / {子领域2} / {子领域3}），输出结构化，引用{权威来源}。`

---

## 八、输出格式扩展

### 8.1 内置报告模板

| 模板名 | 用途 | 格式 |
|--------|------|------|
| default | 通用分析 | 摘要/详细/对比/结论 四段 |
| executive | 高管摘要 | 1 页纸，只保留摘要 + 3 条建议 |
| weekly-report | 周报 | 本周要点/趋势/风险/下周建议 |
| comparison | 对比分析 | 维度表格 + 评分 + 推荐 |

```bash
# 使用模板
hermes run "expert-panel --query=xxx --template=executive"
hermes run "expert-panel --query=xxx --template=weekly-report"
hermes run "expert-panel --query=xxx --template=comparison"
```

### 8.2 输出到文件

```bash
# Markdown 文件
hermes run "expert-panel --query=xxx" > report.md

# 带时间戳自动保存
hermes run "expert-panel --query=xxx" | tee "~/reports/report-$(date +%Y%m%d%H%M).md"
```

### 8.3 输出到飞书

```python
# 在 run.py 的 aggregate 步骤后追加
# 需先配置飞书 Webhook URL
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK_URL", "")

if FEISHU_WEBHOOK:
    import json as _json
    import urllib.request
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": f"专家团报告：{query[:50]}"}},
            "elements": [
                {"tag": "markdown", "content": final_report[:4000]}
            ]
        }
    }
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=_json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req)
```

### 8.4 输出到 Notion

```python
# 使用 Notion API 追加到页面
# 需配置 NOTION_TOKEN 和 NOTION_PAGE_ID
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")

if NOTION_TOKEN and NOTION_PAGE_ID:
    import urllib.request
    blocks = [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": query[:100]}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": final_report[:2000]}}]}}
    ]
    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children",
        data=json.dumps({"children": blocks}).encode(),
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    urllib.request.urlopen(req)
```

### 8.5 输出为 PPT（通过 python-pptx）

```python
# 需安装：pip install python-pptx
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[1])  # 标题+内容
slide.shapes.title.text = query[:50]
slide.shapes.placeholders[1].text = final_report[:2000]
prs.save(f"/tmp/expert-panel-{int(time.time())}.pptx")
```

---

## 九、多轮上下文与历史对比

### 9.1 session_search 跨轮引用

在同一会话中，后续问题可引用前序分析结果：

```bash
# 第一轮：技术选型
hermes run "expert-panel --query='React vs Vue 技术选型' --experts=tech,product"

# 第二轮：深入追问（Hermes 自动带上下文）
hermes run "expert-panel --query='基于上面的分析，如果团队只有 3 个前端，选哪个更合适？'"
```

### 9.2 fact_store 历史对比

利用 Hermes 内置 `fact_store` 实现跨会话对比：

```python
# run.py 中集成 fact_store 读写
import os
FACT_STORE_DIR = os.path.expanduser("~/.hermes/fact_store/expert-panel")
os.makedirs(FACT_STORE_DIR, exist_ok=True)

def save_to_fact_store(query: str, report: str) -> str:
    """保存报告到 fact_store，返回文件路径"""
    import hashlib, time
    h = hashlib.md5(query.encode()).hexdigest()[:8]
    ts = int(time.time())
    path = os.path.join(FACT_STORE_DIR, f"{ts}_{h}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"query": query, "report": report, "timestamp": ts}, f, ensure_ascii=False, indent=2)
    return path

def load_history(query: str, limit: int = 3) -> list:
    """加载相似历史报告"""
    files = sorted(
        [f for f in os.listdir(FACT_STORE_DIR) if f.endswith(".json")],
        reverse=True
    )[:limit]
    results = []
    for fn in files:
        with open(os.path.join(FACT_STORE_DIR, fn), "r", encoding="utf-8") as f:
            results.append(json.load(f))
    return results
```

### 9.3 历史对比报告

```bash
# 自动对比历史分析
hermes run "expert-panel --query='React vs Vue 最新分析' --compare-history=true"
```

输出中会包含「与上次分析的差异」段落：

```markdown
## 历史对比
- 与 2026-05-20 的分析相比：
  - 新增：Svelte 5 Runes 机制改变了竞争格局
  - 变化：React Server Components 生态更成熟，推荐度从 P1 升至 P0
  - 不变：Vue 仍为中小项目首选
```

---

## 十、智能路由策略

### 10.1 路由规则

| 问题复杂度 | 判断条件 | 路由 |
|-----------|----------|------|
| 简单 | 单一领域、< 50 字 | 1 个专家 |
| 中等 | 跨 2-3 个领域 | 2-3 个专家 |
| 复杂 | 跨 4+ 领域 / 含「分析/评估/方案」 | 4 个专家 |

### 10.2 自动路由实现

```python
# run.py 中的智能路由逻辑
import re

def auto_route(query: str) -> list:
    """根据问题内容自动选择专家组合"""
    q = query.lower()
    
    # 关键词 → 专家映射
    KEYWORD_MAP = {
        "tech": ["代码", "架构", "技术", "框架", "api", "部署", "性能", "bug", "debug",
                 "code", "arch", "tech", "framework", "deploy", "performance"],
        "product": ["产品", "需求", "用户", "体验", "竞品", "功能", "设计",
                    "product", "requirement", "user", "competitor", "feature"],
        "business": ["商业", "市场", "盈利", "成本", "定价", "模式", "融资",
                     "business", "market", "revenue", "cost", "pricing", "model"],
        "research": ["研究", "趋势", "报告", "综述", "文献", "调研",
                     "research", "trend", "report", "survey", "literature"],
        "ux": ["交互", "界面", "可用性", "体验设计", "ux", "ui", "usability"],
        "data": ["数据", "指标", "分析", "ab测试", "埋点", "data", "metric", "analytics"],
        "marketing": ["营销", "推广", "增长", "品牌", "marketing", "growth", "brand"],
        "security": ["安全", "漏洞", "加密", "合规", "security", "vulnerability", "compliance"],
    }
    
    # 计算每个领域的匹配分数
    scores = {}
    for expert, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[expert] = score
    
    # 按分数排序取 top N
    if not scores:
        # 无关键词匹配，默认 research
        return ["research"]
    
    sorted_experts = sorted(scores.items(), key=lambda x: -x[1])
    
    # 简单问题：1 个专家
    if len(query) < 50 and len(sorted_experts) <= 1:
        return [sorted_experts[0][0]]
    
    # 中等问题：top 2-3
    if len(sorted_experts) <= 3:
        return [e[0] for e in sorted_experts]
    
    # 复杂问题：top 4
    return [e[0] for e in sorted_experts[:4]]
```

### 10.3 使用方式

```bash
# 自动路由（推荐）
hermes run "expert-panel --query='AI 写作助手产品方案评估' --route=auto"

# 手动指定（覆盖自动）
hermes run "expert-panel --query='xxx' --experts=tech,product"
```

---

## 十一、自定义报告模板

### 11.1 内置模板定义

```python
# run.py 中的报告模板
REPORT_TEMPLATES = {
    "default": """## 摘要
（3-5 句话总结核心结论）

## 详细分析
（按主题组织各专家观点，引用其原话要点）

## 各专家观点对比
（一致点 / 分歧点 / 互补点）

## 结论与建议
（3-7 条可执行建议，标优先级 P0/P1/P2）""",

    "executive": """## 核心结论
（3 句话）

## 关键建议
1. [P0] ...
2. [P1] ...
3. [P1] ...

## 风险提示
（1-2 句）""",

    "weekly-report": """## 本周要点
（3-5 条）

## 趋势分析
（上升/下降/新兴趋势）

## 风险与机会
（各 2-3 条）

## 下周建议
（3-5 条可执行项）""",

    "comparison": """## 对比维度
| 维度 | 选项A | 选项B | 选项C |
|------|-------|-------|-------|
| ... | ... | ... | ... |

## 评分
（1-10 分制，各维度打分）

## 推荐结论
（综合评分 + 适用场景推荐）""",
}
```

### 11.2 自定义模板

用户可在 `~/.hermes/skills/expert-panel/templates/` 下创建自定义模板：

```bash
# 创建自定义模板
mkdir -p ~/.hermes/skills/expert-panel/templates
cat > ~/.hermes/skills/expert-panel/templates/my-template.md <<'EOF'
## 🎯 一句话结论
（1 句话）

## 📊 数据支撑
（关键数据点）

## 🔥 行动项
- [ ] 行动1
- [ ] 行动2
- [ ] 行动3
EOF

# 使用
hermes run "expert-panel --query=xxx --template=my-template"
```

---

## 十二、与其他 Skill 组合

### 12.1 grill-me → Work Buddy（先质疑再分析）

先用 `grill-me` 对想法进行压力测试，再用专家团深入分析：

```bash
# Step 1: 用 grill-me 质疑你的想法
hermes run "grill-me --topic='我想做一个 AI 写作助手'"
# 输出：5-10 个尖锐问题

# Step 2: 用专家团分析这些问题的答案
hermes run "expert-panel --query='AI 写作助手的以下风险如何应对：[grill-me 输出的问题]' --experts=product,business,tech"
```

### 12.2 brainstorming → Work Buddy（先发散再收敛）

```bash
# Step 1: 用 brainstorming 发散想法
hermes run "brainstorming --topic='AI 写作助手的功能设计'"

# Step 2: 用专家团评估收敛后的方案
hermes run "expert-panel --query='评估以下 AI 写作助手方案：[brainstorming 产出]' --route=auto"
```

### 12.3 Work Buddy → requesting-code-review（分析后审代码）

```bash
# Step 1: 专家团分析技术方案
hermes run "expert-panel --query='微服务拆分方案评审' --experts=tech,security,ops"

# Step 2: 方案确定后，对实现代码做 review
hermes run "requesting-code-review --path=./src/auth/"
```

### 12.4 定时组合（cronjob）

```bash
# 每周一：先研究趋势，再生成周报
crontab -e
0 9 * * 1 hermes run "expert-panel --query='本周 AI 行业动态' --experts=research,business --template=weekly-report" >> ~/reports/weekly.md
```

---

## 十三、本地推理（Llama.cpp + Qwen3-4B）— 可选灰度

### 13.1 适用判断

| 场景 | 建议 |
|------|------|
| 隐私数据 / 离线 | ✅ 开本地 |
| 日常省钱 | ✅ 简单任务走本地 |
| 长上下文 / 复杂推理 | ❌ 仍走云端 |
| GPU 显存 < 6 GB | ❌ 建议关 |

### 13.2 安装

```bash
sudo apt update && sudo apt install -y build-essential cmake git
git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp
cd ~/llama.cpp && make -j$(nproc)
mkdir -p ~/llama.cpp/models
# 从 https://huggingface.co/Qwen/Qwen3-4B-Instruct-GGUF 或国内镜像下载
```

### 13.3 启动并注册为 systemd 用户服务

见 `local-llm/start.sh` 和 `local-llm/llama-server.service`。

### 13.4 健康检查

```bash
curl -s http://127.0.0.1:8080/health
# 期望：{"status":"ok"}
```

### 13.5 在 Hermes 中注册

见 `config/config.example.yaml`。

### 13.6 关停本地（回退到纯云端）

```bash
systemctl --user stop --now llama-server.service
```

---

## 十四、SOP（标准操作流程）

### 14.1 日常使用

```bash
# 1) 起本地推理（如果用）
systemctl --user is-active llama-server.service || systemctl --user start llama-server.service

# 2) 验证网络 & API Key
curl -sSf https://api.deepseek.com >/dev/null
[ -n "$DEEPSEEK_API_KEY" ] && echo OK

# 3) 启动专家团
hermes run "expert-panel --query=今日任务"
```

### 14.2 添加新专家

1. 在 `run.py` 的 `EXPERT_SYSTEM` 添加一行
2. 在 `ALL_EXPERTS` 元组中添加代号
3. 在 `SKILL.md` 的「专家角色」段落同步
4. 跑冒烟测试
5. 记录到 `CHANGELOG.md`

### 14.3 升级 Hermes

```bash
systemctl --user stop llama-server.service
pip install -U hermes-agent
bash ~/.hermes/skills/expert-panel/tests/smoke.sh
systemctl --user start llama-server.service
```

### 14.4 升级 Llama.cpp / 模型

```bash
cp -r ~/llama.cpp ~/llama.cpp.bak.$(date +%Y%m%d)
cd ~/llama.cpp && git pull && make -j$(nproc)
mv models/Qwen3-4B-Instruct-Q4_K_M.gguf models/Qwen3-4B-Instruct-Q4_K_M.bak.gguf
systemctl --user restart llama-server.service
```

### 14.5 升级专家团技能

```bash
cd ~/.hermes/skills/expert-panel
cp run.py run.py.bak
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
```

### 14.6 故障应急（30 秒定位）

```bash
# 1) hermes 还能用吗？
hermes --version
# 2) 本地推理在跑吗？
systemctl --user status llama-server.service
curl -s http://127.0.0.1:8080/health
# 3) 云端能调吗？
curl -sSf https://api.deepseek.com
# 4) 代理干扰？
env | grep -i proxy
# 取消：unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
# 5) 看最近日志
journalctl --user -u llama-server.service -n 50
tail -n 100 ~/.hermes/logs/*.log 2>/dev/null
```

---

## 十五、验证与验收

### 15.1 冒烟测试 5 条

见 `skills/expert-panel/tests/smoke.sh`。

### 15.2 验收 checklist

- [ ] `hermes --version` 正常
- [ ] `expert-panel --query=1+1=几` 返回 2
- [ ] 至少 1 个 expert 能产出 5+ 要点
- [ ] 汇总报告包含「摘要/详细/对比/结论」4 段
- [ ] 关闭本地推理后仍能工作（云端回退）
- [ ] `unset http_proxy` 后云端可调
- [ ] 冒烟脚本 5 条全过
- [ ] `--route=auto` 能自动选择专家
- [ ] `--template=executive` 输出精简格式
- [ ] 扩展角色（ux/data/marketing）可正常调用

### 15.3 性能基线（参考值）

| 操作 | 期望耗时 | 备注 |
|------|----------|------|
| 单 expert 回答 | 5–15 s | 云端 |
| 4 expert 并行 | 20–40 s | 取决于最慢一个 |
| 本地 4B 模型首 token | < 2 s | GPU 加速 |
| 冒烟脚本全跑 | < 3 min | 云端 |

---

## 十六、风险登记与回滚

### 16.1 风险表

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| DeepSeek API 限流/宕机 | 中 | 高 | `fallback_to_local: true` |
| 本地模型 OOM | 中 | 中 | 量化降到 Q3_K；切云端 |
| 代理环境变量污染 | 高 | 中 | 启动脚本里 `unset *_proxy` |
| delegate_task 拆解失败 | 中 | 中 | v4.1 已降级单 expert |
| 提示词注入（外部输入） | 中 | 高 | 限制 toolsets；隔离 system prompt |
| 磁盘满（GGUF 占用大） | 低 | 中 | 监控 `df -h`；定期清理 |
| WSL 时区错乱 | 低 | 低 | `sudo timedatectl set-timezone Asia/Shanghai` |
| Hermes 版本升级不兼容 | 低 | 高 | 备份 venv；保留旧版 wheel |

### 16.2 回滚剧本

| 场景 | 步骤 |
|------|------|
| 云端炸 | `HERMES_FORCE_LOCAL=1` + 启 llama |
| 本地炸 | `systemctl --user stop llama-server` + 用云端 |
| 技能升级后异常 | `cp run.py.bak run.py` |
| 整个专家团不稳 | `mv ~/.hermes/skills/expert-panel ~/.hermes/skills/expert-panel.off` |
| 配置文件破坏 | `git -C ~/.hermes checkout -- profiles/` |
| Hermes 升级失败 | `pip install hermes-agent==旧版本号` |

---

## 十七、成本与省钱策略

### 17.1 价格参考（截至 2026-06，请以官网为准）

| 模型 | 输入 ¥/M | 输出 ¥/M | 备注 |
|------|---------|---------|------|
| DeepSeek-V3.2-Flash | ~1 | ~4 | 默认 |
| DeepSeek-V3.2-Pro | ~4 | ~16 | 高质量 |
| 本地 Qwen3-4B | 0 | 0 | 电费忽略 |

### 17.2 省钱动作清单

1. **缓存命中**（DeepSeek）成本降至 0.02 元/百万 tokens
2. **路由**：含"代码/函数/报错"走本地
3. **智能路由**：`--route=auto` 自动选最少专家
4. **专家数控制**：日常用 1–2 个，复杂任务再开 4 个
5. **短 prompt**：拆解 prompt 时约束字数
6. **关闭不必要 toolsets**：能不用 `search` 就不开
7. **温度调低**：`temperature: 0.1` 减少 token 浪费
8. **最大 token 限制**：在 config 中设 `max_tokens: 2048`

### 17.3 典型月度账单

| 场景 | 估算 |
|------|------|
| 纯云端 V3.2-Flash 中度使用 | 5–15 元 |
| 混合（日常本地 + 偶发云端） | 0–5 元 |
| 纯云端 V3.2-Pro | 50–200 元 |

---

## 十八、可观测性

### 18.1 日志位置

| 来源 | 路径 |
|------|------|
| Hermes 主日志 | `~/.hermes/logs/hermes.log` |
| Llama.cpp 日志 | `journalctl --user -u llama-server.service` |
| 专家团 debug | `HERMES_EXPERT_PANEL_DEBUG=1` 时输出到 stderr |
| 临时 trace | `/tmp/hermes-expert-panel-*.json` |

### 18.2 3 个关键指标

| 指标 | 怎么算 | 阈值 |
|------|--------|------|
| 专家团成功率 | 24h 内成功调用 / 总调用 | > 95% |
| 平均耗时 | 汇总步骤 wall-clock | < 60s |
| 月成本 | 解析 DeepSeek usage | < 30 元 |

### 18.3 调试开关

```bash
export HERMES_EXPERT_PANEL_DEBUG=1
export HERMES_LOG_LEVEL=debug
hermes run "expert-panel --query=xx" 2>&1 | tee /tmp/exp.log
```

---

## 十九、安全与隐私

### 19.1 API Key 保管
- 写入 `~/.bashrc`：`export DEEPSEEK_API_KEY=sk-xxx`
- **不要**写进 git 仓库
- 定期轮换（每 90 天）
- 单独建一个 sub-account，仅授予 chat 权限

### 19.2 提示词注入
- 外部内容不要直接拼到 system prompt
- 隔离：用户输入只放进 `user` 段
- 工具最小化：能不开 `terminal` 就不开

### 19.3 本地数据
- `~/.hermes/fact_store/` 包含历史事实，敏感场景请 `chmod 700`
- WSL 文件 Windows 可见，反之亦然；不放敏感数据到 Desktop

### 19.4 网络出口
- 本地 llama 绑 `127.0.0.1`，不暴露 `0.0.0.0`
- 云端走 HTTPS；不关证书校验

---

## 二十、性能调优

### 20.1 并发控制

| 参数 | 默认 | 调优建议 |
|------|------|----------|
| 并行专家数 | 4 | 日常 2，复杂 4 |
| delegate_task 超时 | 120 s | 网络差时增至 180 s |
| 串行模式 | off | API 限流时开启 |

### 20.2 Token 优化

```python
# 拆解 prompt 约束
plan_prompt = f"""...
约束：
- prompt 不超过 200 字
- 每个 expert 只输出 5 个要点"""

# 专家输出约束
"输出要求：\n- 不少于 5 个要点\n- 每个要点不超过 50 字\n- 关键结论加粗"

# 汇总约束
"严格按四段输出，总字数不超过 2000 字"
```

### 20.3 本地模型调优

```bash
./llama-server \
  --model models/Qwen3-4B-Instruct-Q4_K_M.gguf \
  --n-gpu-layers 25 \
  --n-ctx 4096 \
  --threads 8 \
  --batch-size 512 \
  --mlock
```

| 参数 | 显存 6GB | 显存 8GB+ |
|------|---------|----------|
| n-gpu-layers | 15 | 25 |
| n-ctx | 2048 | 4096 |
| batch-size | 256 | 512 |

---

## 二十一、迁移指南（v3.1 → v4.1）

### 21.1 迁移步骤

```bash
# 1. 备份
cp -r ~/.hermes/skills/expert-panel ~/.hermes/skills/expert-panel.bak

# 2. 拉取 v4.1
git clone https://github.com/kkpg-l/hermes-work-buddy.git /tmp/hermes-work-buddy

# 3. 替换
cp /tmp/hermes-work-buddy/skills/expert-panel/SKILL.md ~/.hermes/skills/expert-panel/
cp /tmp/hermes-work-buddy/skills/expert-panel/run.py ~/.hermes/skills/expert-panel/

# 4. 更新配置
cp /tmp/hermes-work-buddy/config/config.example.yaml ~/.hermes/profiles/default/config.yaml

# 5. 验证
bash /tmp/hermes-work-buddy/skills/expert-panel/tests/smoke.sh

# 6. 清理
rm -rf /tmp/hermes-work-buddy
```

### 21.2 回退

```bash
cp -r ~/.hermes/skills/expert-panel.bak/* ~/.hermes/skills/expert-panel/
```

---

## 二十二、版本演进

### 22.1 升级路径

```
v3.1          v4.0              v4.1 (current)      v5.0 (next)
───────       ──────            ──────               ──────
单 Profile     + 风险/回滚       + 使用场景            + 多 Profile
4 专家         + 安全/SOP        + 生态联动            + 团队协作
无 SOP         + 验收            + 8 扩展角色           + Web UI
无监控         + 调优            + 智能路由             + Prometheus
无调优         + 迁移指南        + 自定义模板           + 自适应路由
                                + Skill 组合           + 自动迁移
                                + 多轮上下文
```

### 22.2 弃用清单（v4.1 起）
- OpenViking 记忆（→ `fact_store`）
- Tavily API（→ DuckDuckGo + zhihu）
- 多 Profile 模式（→ 单 Profile + system prompt）

### 22.3 路线图候选（v5.0 备选）
- [ ] Web 控制台（FastAPI + 静态页）
- [ ] Telegram Bot 网关
- [ ] MCP 工具：浏览器、代码沙箱
- [ ] 记忆图谱
- [ ] 多用户隔离 + 计费
- [ ] 自适应路由（基于历史成功率动态调整）

---

## 附录 A：完整文件清单

```
~/.hermes/
├── profiles/default/config.yaml
├── skills/expert-panel/
│   ├── SKILL.md
│   ├── run.py
│   ├── templates/              # 自定义报告模板
│   │   └── my-template.md
│   └── tests/smoke.sh
├── fact_store/expert-panel/    # 历史报告存储
├── logs/
└── fact_store/

~/llama.cpp/
├── (编译产物)
├── start.sh
└── models/Qwen3-4B-Instruct-Q4_K_M.gguf

~/.config/systemd/user/
└── llama-server.service
```

## 附录 B：关键命令速查

```bash
# 基本使用
hermes run "expert-panel --query=你的问题"
hermes run "expert-panel --query=xxx --experts=tech,product"
hermes run "expert-panel --query=xxx --route=auto"
hermes run "expert-panel --query=xxx --template=executive"
hermes run "expert-panel --query=xxx --mode=serial"

# 调试
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"

# 健康检查
bash scripts/health-check.sh

# 网络
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

## 附录 C：术语表

| 术语 | 含义 |
|------|------|
| L1/L2 | 本地推理层 / 云端增强层 |
| expert-panel | 本方案核心技能名 |
| delegate_task | Hermes 内置并行子任务 API |
| fact_store | Hermes 内置事实记忆 |
| fallback_to_local | 云端异常自动回本地 |
| smoke test | 冒烟测试 |
| fan-out | 并行分发子任务 |
| aggregate | 汇总子任务结果 |
| auto_route | 智能路由，自动选专家 |
| HeartFlow | Hermes 执行验证机制 |

## 附录 D：FAQ

**Q1. delegate_task 实际签名是什么？**  
请以 Hermes 官方文档为准。v4.1 脚本已做容错降级。

**Q2. 模型名不存在？**  
以官方模型目录为准。下载失败时用国内镜像（如 `hf-mirror.com`）。

**Q3. 专家回答风格不统一？**  
调整 `EXPERT_SYSTEM` 字典；增加「输出格式示例」。

**Q4. 汇总报告缺一段？**  
检查报告模板是否完整；开启 DEBUG 看 aggregate 步骤输出。

**Q5. 5 分钟内搞不定？**  
最常见：① 代理未取消；② API Key 未生效；③ venv 中缺依赖。按 §14.6 跑应急诊断。

**Q6. 如何限制 Token 消耗？**  
见第二十章「性能调优」→ Token 优化。使用 `--route=auto` 自动选最少专家。

**Q7. 智能路由不准？**  
在 `run.py` 的 `KEYWORD_MAP` 中补充领域关键词。

**Q8. 自定义模板不生效？**  
确认模板文件在 `~/.hermes/skills/expert-panel/templates/` 目录下，文件名为 `模板名.md`。

**Q9. 飞书/Notion 推送失败？**  
检查 Webhook URL / API Token 是否正确，网络是否可达。

---

**v4.1 完。**
