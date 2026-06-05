#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expert Panel v4.0
- 修正 v3.1: --key=value 解析、delegate_task 签名、错误降级
- 新增: --experts 过滤、--mode 串行/并行、debug 环境变量
"""
import json
import os
import sys
import traceback
from typing import Dict, List, Any

# Hermes 内置工具，按实际包名导入
try:
    from hermes_tools import delegate_task  # type: ignore
except Exception:  # 沙箱外可手动 mock
    def delegate_task(goal: str = "", tasks: list = None, toolsets: list = None, **kw):
        return [{"summary": f"[mock] {goal or tasks}", "ok": True}]

DEBUG = os.environ.get("HERMES_EXPERT_PANEL_DEBUG") == "1"

ALL_EXPERTS = ("tech", "product", "business", "research")


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


EXPERT_SYSTEM = {
    "tech": "你是资深技术专家（架构 / 代码 / 选型），输出结构化、引用证据。",
    "product": "你是资深产品专家（需求 / 设计 / 竞品），输出结构化、引用证据。",
    "business": "你是资深商业分析专家（模式 / 市场 / 财务），输出结构化、引用证据。",
    "research": "你是资深研究专家（综述 / 系统分析），输出结构化、引用来源。",
}


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


def main() -> int:
    args = parse_args(sys.argv)
    query = args.get("query", "").strip()

    if not query:
        print('用法：hermes run "expert-panel --query=你的问题"', file=sys.stderr)
        return 2

    # 过滤专家
    wanted = args.get("experts", "tech,product,business,research")
    experts = [e for e in wanted.split(",") if e in ALL_EXPERTS] or list(ALL_EXPERTS)
    log(f"experts={experts}")

    mode = args.get("mode", "parallel")  # parallel | serial
    log(f"mode={mode}")

    # ---------- 1) plan：拆解任务 ----------
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
        tasks = [{"expert": "research", "prompt": query}]

    # ---------- 2) fan-out：并行/串行 ----------
    fanout = []
    for t in tasks:
        expert = t.get("expert", "research")
        if expert not in experts:
            expert = "research"
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

    # ---------- 3) aggregate：汇总 ----------
    agg_prompt = f"""你是主协调员。整合以下专家分析，输出最终报告。

## 原始问题
{query}

## 专家分析（JSON）
{json.dumps(summaries, ensure_ascii=False, indent=2)}

## 严格按以下四段输出（中文，Markdown）：
## 摘要
（3-5 句话总结核心结论）

## 详细分析
（按主题组织各专家观点，引用其原话要点）

## 各专家观点对比
（一致点 / 分歧点 / 互补点）

## 结论与建议
（3-7 条可执行建议，标优先级 P0/P1/P2）"""

    try:
        final = delegate_task(goal=agg_prompt, toolsets=["terminal"])
        print(final.get("summary", ""))
    except Exception as e:
        # 终极降级：直接拼接
        log(f"aggregate 失败，直接拼接: {e}")
        print("# 报告（降级模式）\n")
        for s in summaries:
            print("- " + s.replace("\n", " ")[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
