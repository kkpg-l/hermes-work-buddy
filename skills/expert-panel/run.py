#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expert Panel v4.1
- v4.0: 修正 parse_args, delegate_task 签名, 错误降级
- v4.1: 扩展角色(12个), 智能路由, 报告模板, fact_store 历史对比
"""
import json
import os
import sys
import traceback
from typing import Dict, List, Any

try:
    from hermes_tools import delegate_task  # type: ignore
except Exception:
    def delegate_task(goal: str = "", tasks: list = None, toolsets: list = None, **kw):
        return [{"summary": f"[mock] {goal or tasks}", "ok": True}]

DEBUG = os.environ.get("HERMES_EXPERT_PANEL_DEBUG") == "1"

# ─── 专家角色定义 ────────────────────────────────────

EXPERT_SYSTEM = {
    # 核心 4 专家
    "tech":     "你是资深技术专家（架构 / 代码 / 选型），输出结构化、引用证据。",
    "product":  "你是资深产品专家（需求 / 设计 / 竞品），输出结构化、引用证据。",
    "business": "你是资深商业分析专家（模式 / 市场 / 财务），输出结构化、引用证据。",
    "research": "你是资深研究专家（综述 / 系统分析），输出结构化、引用来源。",
    # 扩展角色
    "ux":        "你是资深 UX 设计专家（交互设计 / 信息架构 / 可用性测试），输出结构化，引用设计原则和用户研究数据。",
    "data":      "你是资深数据专家（数据分析 / 指标体系 / A/B 测试），输出结构化，引用数据驱动方法论。",
    "marketing": "你是资深营销专家（增长策略 / 内容营销 / 品牌定位），输出结构化，引用市场数据和案例。",
    "seo":       "你是资深 SEO 专家（关键词策略 / 技术 SEO / 内容优化），输出结构化，引用搜索引擎最佳实践。",
    "security":  "你是资深安全专家（应用安全 / 基础设施安全 / 合规），输出结构化，引用 OWASP/CVE 等权威来源。",
    "legal":     "你是资深法律合规专家（数据隐私 / 知识产权 / 合同），输出结构化，引用相关法规条文。",
    "ops":       "你是资深运维专家（CI/CD / 监控 / 容灾），输出结构化，引用 SRE 最佳实践。",
    "content":   "你是资深内容专家（文案 / 叙事 / 传播策略），输出结构化，引用传播学和内容营销方法论。",
}

ALL_EXPERTS = tuple(EXPERT_SYSTEM.keys())

# ─── 报告模板 ────────────────────────────────────────

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

# ─── 智能路由 ────────────────────────────────────────

KEYWORD_MAP = {
    "tech":      ["代码", "架构", "技术", "框架", "api", "部署", "性能", "bug", "debug",
                  "code", "arch", "tech", "framework", "deploy", "performance"],
    "product":   ["产品", "需求", "用户", "体验", "竞品", "功能", "设计",
                  "product", "requirement", "user", "competitor", "feature"],
    "business":  ["商业", "市场", "盈利", "成本", "定价", "模式", "融资",
                  "business", "market", "revenue", "cost", "pricing", "model"],
    "research":  ["研究", "趋势", "报告", "综述", "文献", "调研",
                  "research", "trend", "report", "survey", "literature"],
    "ux":        ["交互", "界面", "可用性", "体验设计", "ux", "ui", "usability"],
    "data":      ["数据", "指标", "分析", "ab测试", "埋点", "data", "metric", "analytics"],
    "marketing": ["营销", "推广", "增长", "品牌", "marketing", "growth", "brand"],
    "security":  ["安全", "漏洞", "加密", "合规", "security", "vulnerability", "compliance"],
}


def auto_route(query: str) -> List[str]:
    """根据问题内容自动选择专家组合"""
    q = query.lower()
    scores: Dict[str, int] = {}
    for expert, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[expert] = score

    if not scores:
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


# ─── fact_store 历史对比 ──────────────────────────────

FACT_STORE_DIR = os.path.expanduser("~/.hermes/fact_store/expert-panel")


def save_to_fact_store(query: str, report: str) -> str:
    import hashlib, time
    os.makedirs(FACT_STORE_DIR, exist_ok=True)
    h = hashlib.md5(query.encode()).hexdigest()[:8]
    ts = int(time.time())
    path = os.path.join(FACT_STORE_DIR, f"{ts}_{h}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"query": query, "report": report, "timestamp": ts}, f, ensure_ascii=False, indent=2)
    return path


def load_history(query: str, limit: int = 3) -> list:
    if not os.path.isdir(FACT_STORE_DIR):
        return []
    files = sorted(
        [f for f in os.listdir(FACT_STORE_DIR) if f.endswith(".json")],
        reverse=True
    )[:limit]
    results = []
    for fn in files:
        with open(os.path.join(FACT_STORE_DIR, fn), "r", encoding="utf-8") as f:
            results.append(json.load(f))
    return results


# ─── 工具函数 ─────────────────────────────────────────

def log(msg: str) -> None:
    if DEBUG:
        print(f"[expert-panel] {msg}", file=sys.stderr)


def parse_args(argv: List[str]) -> Dict[str, str]:
    """支持 --key=value 与 --key value 两种形式"""
    args: Dict[str, str] = {}
    i = 1
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--"):
            i += 1
            continue
        body = tok[2:]
        if "=" in body:
            k, v = body.split("=", 1)
            args[k.strip()] = v.strip()
            i += 1
        else:
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args[body] = argv[i + 1]
                i += 2
            else:
                args[body] = "true"
                i += 1
    return args


def build_expert_prompt(expert: str, query: str) -> str:
    sys_prompt = EXPERT_SYSTEM.get(expert, EXPERT_SYSTEM["research"])
    return (
        f"{sys_prompt}\n\n"
        f"## 问题\n{query}\n\n"
        f"## 输出要求\n"
        f"- 不少于 5 个要点\n"
        f"- 关键结论加粗\n"
        f"- 如引用事实请附来源\n"
    )


def load_custom_template(template_name: str) -> str:
    """加载用户自定义报告模板"""
    custom_dir = os.path.expanduser("~/.hermes/skills/expert-panel/templates")
    custom_path = os.path.join(custom_dir, f"{template_name}.md")
    if os.path.isfile(custom_path):
        with open(custom_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


# ─── 主流程 ───────────────────────────────────────────

def main() -> int:
    args = parse_args(sys.argv)
    query = args.get("query", "").strip()

    if not query:
        print('用法：hermes run "expert-panel --query=你的问题"', file=sys.stderr)
        return 2

    # 智能路由 or 手动指定
    route = args.get("route", "")
    if route == "auto":
        experts = auto_route(query)
        log(f"auto_route => {experts}")
    else:
        wanted = args.get("experts", "tech,product,business,research")
        experts = [e for e in wanted.split(",") if e in ALL_EXPERTS] or list(ALL_EXPERTS[:4])
    log(f"experts={experts}")

    mode = args.get("mode", "parallel")
    template_name = args.get("template", "default")
    compare_history = args.get("compare-history", "false") == "true"
    log(f"mode={mode}, template={template_name}, compare_history={compare_history}")

    # ── 1) plan：拆解任务 ──
    plan_prompt = f"""你是 Work Buddy 主协调员。把问题拆为 1~{len(experts)} 个子任务，分配给以下专家：
{', '.join(experts)}

## 问题
{query}

严格输出 JSON，不要任何额外文字：
{{"tasks":[{{"expert":"tech","prompt":"..."}}, ...]}}

约束：
- 每个 expert 最多 1 个任务
- tasks 至少 1 个、至多 {len(experts)} 个
- prompt 要可独立执行（包含原问题语境）"""

    try:
        plan_resp = delegate_task(goal=plan_prompt, toolsets=["terminal"])
        plan_text = plan_resp.get("summary", "") if isinstance(plan_resp, dict) else str(plan_resp)
        plan = json.loads(plan_text)
        tasks = plan.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("plan 为空或非列表")
    except Exception as e:
        log(f"plan 失败，降级为单 expert: {e}")
        tasks = [{"expert": experts[0] if experts else "research", "prompt": query}]

    # ── 2) fan-out：并行/串行 ──
    fanout = []
    for t in tasks:
        expert = t.get("expert", experts[0] if experts else "research")
        if expert not in experts:
            expert = experts[0] if experts else "research"
        fanout.append({
            "goal": build_expert_prompt(expert, t.get("prompt", query)),
            "context": f"role={expert}",
            "toolsets": ["terminal", "file", "search"],
        })

    log(f"开始 fan-out，共 {len(fanout)} 个任务")
    try:
        if mode == "serial":
            results: List[Any] = []
            for f in fanout:
                results.append(delegate_task(**f))
        else:
            results = delegate_task(tasks=fanout)
        if not isinstance(results, list):
            results = [results]
    except Exception as e:
        log(f"fan-out 失败，使用降级路径: {e}\n{traceback.format_exc()}")
        results = [{"summary": f"[降级单跑] {f['goal']}"} for f in fanout]

    summaries = []
    for r in results:
        if isinstance(r, dict):
            summaries.append(r.get("summary", ""))
        else:
            summaries.append(str(r))

    # ── 3) aggregate：汇总 ──
    # 选择报告模板
    template = REPORT_TEMPLATES.get(template_name)
    if template is None:
        template = load_custom_template(template_name)
    if template is None:
        template = REPORT_TEMPLATES["default"]
        log(f"模板 '{template_name}' 未找到，使用 default")

    # 历史对比段落
    history_section = ""
    if compare_history:
        history = load_history(query)
        if history:
            history_summaries = [h.get("report", "")[:500] for h in history]
            history_section = f"""

## 历史对比
请对比以下历史分析结果，指出与本次分析的差异：
{json.dumps(history_summaries, ensure_ascii=False, indent=2)}

输出格式：
- 新增：...
- 变化：...
- 不变：..."""

    agg_prompt = f"""你是主协调员。整合以下专家分析，输出最终报告。

## 原始问题
{query}

## 专家分析（JSON）
{json.dumps(summaries, ensure_ascii=False, indent=2)}

## 严格按以下格式输出（中文，Markdown）：
{template}{history_section}"""

    try:
        final = delegate_task(goal=agg_prompt, toolsets=["terminal"])
        final_report = final.get("summary", "")
    except Exception as e:
        log(f"aggregate 失败，直接拼接: {e}")
        final_report = "# 报告（降级模式）\n"
        for s in summaries:
            final_report += "- " + s.replace("\n", " ")[:300] + "\n"

    # 保存到 fact_store
    try:
        saved_path = save_to_fact_store(query, final_report)
        log(f"报告已保存到 {saved_path}")
    except Exception as e:
        log(f"fact_store 保存失败: {e}")

    print(final_report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
