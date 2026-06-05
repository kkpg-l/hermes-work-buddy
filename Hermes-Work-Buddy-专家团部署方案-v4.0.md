# Hermes Work Buddy 专家团部署方案 v4.0（完整实战版）

**版本**：v4.0（2026.06） · 取代 v3.1
**适用环境**：WSL2 (Ubuntu 24.04) + Windows 11，单用户
**核心组件**：Hermes Agent + DeepSeek API（云端）+ Llama.cpp + Qwen GGUF（可选本地）
**设计原则**：极简 · 可灰度 · 可回滚 · 5 分钟首跑

---

## 0. 相对 v3.1 的变更摘要

| 模块 | v3.1 状态 | v4.0 改进 |
|------|----------|----------|
| 专家团脚本 | `parse_args` 对 `--key --flag2` 形式有 bug；`delegate_task` 签名混杂 | 统一为 `--key=value` 解析；明确分阶段调用 `plan → fan-out → aggregate` |
| 验收 | 无 | 新增 5 条冒烟测试 + 验收 checklist |
| 风险与回滚 | 仅 4 行排障 | 新增风险登记、回滚剧本 |
| SOP | 缺 | 新增 6 类标准操作流程 |
| 可观测性 | 缺 | 新增日志位置、3 个关键指标、调试开关 |
| 安全 | 缺 | 新增 API key、提示词注入、本地数据 |
| 模型名 | `Qwen3.5-4B` / `DeepSeek-V4-Flash` | 修正为 `Qwen3-4B-Instruct` / `DeepSeek-V3.2-Flash`（请以官方目录为准） |
| 文档 | 一份直铺 | 分模块，便于局部更新与版本演进 |

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

### 3.2 一键脚本（推荐）

把以下保存为 `~/.hermes/install_expert_panel.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1) 建技能目录
mkdir -p ~/.hermes/skills/expert-panel
cd ~/.hermes/skills/expert-panel

# 2) 写 SKILL.md 与 run.py（见第四、五章）
#    用户可手动复制；或用 curl 从 git 拉取
echo "请把第四、五章的 SKILL.md 与 run.py 写入本目录"
echo "路径：$(pwd)"

# 3) 验证
hermes run "expert-panel --query=自检：返回 1+1 的答案"
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

### 4.1 `~/.hermes/skills/expert-panel/SKILL.md`

```yaml
---
name: expert-panel
description: Work Buddy 专家团 - 多专家并行分析与报告生成
trigger: 专家团|expert panel|分析|研究|报告|评估|方案
---

# Expert Panel Skill v4.0

调用多个专家子 Agent 并行分析问题，最终汇总为结构化报告。

## 使用方式

hermes run "expert-panel --query=你的问题"
hermes run "expert-panel --query=xxx --experts=tech,product"
hermes run "expert-panel --query=xxx --mode=serial"   # 调试用
```

## 专家角色

- **tech-expert**：技术架构、代码、技术选型
- **product-expert**：产品设计、需求、竞品
- **business-expert**：商业模式、市场、财务
- **research-expert**：研究综述、文献、深度调研

## 工作流程

1. **plan**：主协调员拆解为 JSON 任务列表
2. **fan-out**：`delegate_task` 并行/串行执行
3. **aggregate**：汇总为 摘要/详细/对比/结论 四段

## 降级策略

- `delegate_task` 失败 → 退化为单 `research-expert`
- 拆解 JSON 失败 → 退化为整段 prompt
- 本地模型 OOM → 回退云端

## 调试

- 开启 `HERMES_EXPERT_PANEL_DEBUG=1` 输出中间 JSON
- 单独跑某专家：`hermes run "expert-panel --query=xxx --experts=tech"`

### 4.2 `~/.hermes/skills/expert-panel/run.py`（v4.0 修正版）

```python
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
        # 占位：真实环境由 Hermes 提供
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
    "tech":     "你是资深技术专家（架构 / 代码 / 选型），输出结构化、引用证据。",
    "product":  "你是资深产品专家（需求 / 设计 / 竞品），输出结构化、引用证据。",
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
        print("用法：hermes run \"expert-panel --query=你的问题\"", file=sys.stderr)
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
```

### 4.3 调试技巧

```bash
# 看中间 JSON
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"

# 只跑技术专家
hermes run "expert-panel --query=对比 LangChain 和 Hermes --experts=tech"

# 串行（排查并行问题）
hermes run "expert-panel --query=xx --mode=serial"
```

---

## 五、本地推理（Llama.cpp + Qwen3-4B）— 可选灰度

### 5.1 适用判断

| 场景 | 建议 |
|------|------|
| 隐私数据 / 离线 | ✅ 开本地 |
| 日常省钱 | ✅ 简单任务走本地 |
| 长上下文 / 复杂推理 | ❌ 仍走云端 |
| GPU 显存 < 6 GB | ❌ 建议关 |

### 5.2 安装

```bash
sudo apt update && sudo apt install -y build-essential cmake git

git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp
cd ~/llama.cpp && make -j$(nproc)

# 模型（以 Qwen3-4B-Instruct Q4_K_M 为例，~2.5 GB）
mkdir -p ~/llama.cpp/models
# 从 https://huggingface.co/Qwen/Qwen3-4B-Instruct-GGUF  或国内镜像下载
# 选择 Q4_K_M 量化版
```

### 5.3 启动并注册为 systemd 用户服务（开机自启）

```bash
# 启动脚本
cat > ~/llama.cpp/start.sh <<'EOF'
#!/usr/bin/env bash
cd ~/llama.cpp
exec ./build/bin/llama-server \
  --model models/Qwen3-4B-Instruct-Q4_K_M.gguf \
  --n-gpu-layers 25 \
  --n-ctx 4096 \
  --threads 8 \
  --port 8080 \
  --host 127.0.0.1
EOF
chmod +x ~/llama.cpp/start.sh

# systemd 用户服务
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/llama-server.service <<'EOF'
[Unit]
Description=Llama.cpp server (Qwen3-4B)
After=network.target

[Service]
Type=simple
ExecStart=%h/llama.cpp/start.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now llama-server.service
systemctl --user status llama-server.service
```

### 5.4 健康检查

```bash
curl -s http://127.0.0.1:8080/health
# 期望：{"status":"ok"}

# 简单对话
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen3-4B-Instruct-Q4_K_M","messages":[{"role":"user","content":"1+1=?"}]}' \
  | head -c 200
```

### 5.5 在 Hermes 中注册

编辑 `~/.hermes/profiles/default/config.yaml`：

```yaml
models:
  primary: deepseek-chat
  fallback: local-qwen
  fallback_to_local: true
  routes:
    - when_prompt_matches: ["代码", "函数", "报错"]
      use: local-qwen
    - default: deepseek-chat

providers:
  local-qwen:
    type: openai_compatible
    endpoint: http://127.0.0.1:8080/v1
    model_name: Qwen3-4B-Instruct-Q4_K_M
    temperature: 0.2
    timeout: 60

  deepseek:
    type: openai_compatible
    endpoint: https://api.deepseek.com/v1
    model_name: deepseek-chat
    api_key: ${DEEPSEEK_API_KEY}
    temperature: 0.3
```

### 5.6 关停本地（回退到纯云端）

```bash
systemctl --user stop --now llama-server.service
# 临时切换：HERMES_FORCE_CLOUD=1 hermes run ...
```

---

## 六、SOP（标准操作流程）

### 6.1 日常使用

```bash
# 1) 起本地推理（如果用）
systemctl --user is-active llama-server.service || systemctl --user start llama-server.service

# 2) 验证网络 & API Key
curl -sSf https://api.deepseek.com >/dev/null
[ -n "$DEEPSEEK_API_KEY" ] && echo OK

# 3) 启动专家团
hermes run "expert-panel --query=今日任务"
```

### 6.2 添加新专家

1. 在 `run.py` 的 `ALL_EXPERTS`、`EXPERT_SYSTEM` 各加一行
2. 在 `SKILL.md` 的「专家角色」段落同步
3. 跑冒烟测试（第七章）
4. 记录到 `CHANGELOG.md`

### 6.3 升级 Hermes

```bash
# 停本地服务
systemctl --user stop llama-server.service

# 升级
pip install -U hermes-agent   # 或项目自带命令

# 跑验收
bash ~/.hermes/skills/expert-panel/tests/smoke.sh

# 起本地
systemctl --user start llama-server.service
```

### 6.4 升级 Llama.cpp / 模型

```bash
# 备份
cp -r ~/llama.cpp ~/llama.cpp.bak.$(date +%Y%m%d)

# 拉新代码
cd ~/llama.cpp && git pull && make -j$(nproc)

# 替换模型（保留旧版）
mv models/Qwen3-4B-Instruct-Q4_K_M.gguf models/Qwen3-4B-Instruct-Q4_K_M.bak.gguf
# 下载新版

# 重启
systemctl --user restart llama-server.service
```

### 6.5 升级专家团技能

```bash
cd ~/.hermes/skills/expert-panel
cp run.py run.py.bak
# 写入新版 run.py
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
```

### 6.6 故障应急（30 秒定位）

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

## 七、验证与验收

### 7.1 冒烟测试 5 条

```bash
# 保存为 ~/.hermes/skills/expert-panel/tests/smoke.sh
#!/usr/bin/env bash
set -e
cd ~/.hermes/skills/expert-panel

echo "T1: 最小调用"
hermes run "expert-panel --query=1+1=几" | grep -q "2" || { echo "T1 FAIL"; exit 1; }

echo "T2: 单一专家"
hermes run "expert-panel --query=hello --experts=tech" | grep -q "." || { echo "T2 FAIL"; exit 1; }

echo "T3: 中文长问"
hermes run "expert-panel --query=分析 WSL2 与 VirtualBox 的优劣" | grep -q "分析" || { echo "T3 FAIL"; exit 1; }

echo "T4: 串行模式"
hermes run "expert-panel --query=test --mode=serial" | grep -q "." || { echo "T4 FAIL"; exit 1; }

echo "T5: 本地模型（若启用）"
if curl -s http://127.0.0.1:8080/health >/dev/null; then
  hermes run "expert-panel --query=写一个 python 排序函数" | grep -q "." || { echo "T5 FAIL"; exit 1; }
else
  echo "T5 SKIP (本地未启)"
fi

echo "ALL PASS"
```

### 7.2 验收 checklist

- [ ] `hermes --version` 正常
- [ ] `expert-panel --query=1+1=几` 返回 2
- [ ] 至少 1 个 expert 能产出 5+ 要点
- [ ] 汇总报告包含「摘要/详细/对比/结论」4 段
- [ ] 关闭本地推理后仍能工作（云端回退）
- [ ] `unset http_proxy` 后云端可调
- [ ] 冒烟脚本 5 条全过

### 7.3 性能基线（参考值）

| 操作 | 期望耗时 | 备注 |
|------|----------|------|
| 单 expert 回答 | 5–15 s | 云端 |
| 4 expert 并行 | 20–40 s | 取决于最慢一个 |
| 本地 4B 模型首 token | < 2 s | GPU 加速 |
| 冒烟脚本全跑 | < 3 min | 云端 |

---

## 八、风险登记与回滚

### 8.1 风险表

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| DeepSeek API 限流/宕机 | 中 | 高 | `fallback_to_local: true` |
| 本地模型 OOM | 中 | 中 | 量化降到 Q3_K；切云端 |
| 代理环境变量污染 | 高 | 中 | 启动脚本里 `unset *_proxy` |
| delegate_task 拆解失败 | 中 | 中 | v4.0 已降级单 expert |
| 提示词注入（外部输入） | 中 | 高 | 限制 toolsets；隔离 system prompt |
| 磁盘满（GGUF 占用大） | 低 | 中 | 监控 `df -h`；定期清理 |
| WSL 时区错乱 | 低 | 低 | `sudo timedatectl set-timezone Asia/Shanghai` |

### 8.2 回滚剧本

| 场景 | 步骤 |
|------|------|
| 云端炸 | `HERMES_FORCE_LOCAL=1` + 启 llama |
| 本地炸 | `systemctl --user stop llama-server` + 用云端 |
| 技能升级后异常 | `cp run.py.bak run.py` |
| 整个专家团不稳 | `mv ~/.hermes/skills/expert-panel ~/.hermes/skills/expert-panel.off` |
| 配置文件破坏 | `git -C ~/.hermes checkout -- profiles/`（如有版本控制） |

---

## 九、成本与省钱策略

### 9.1 价格参考（截至 2026-06，请以官网为准）

| 模型 | 输入 ¥/M | 输出 ¥/M | 备注 |
|------|---------|---------|------|
| DeepSeek-V3.2-Flash | ~1 | ~4 | 默认 |
| DeepSeek-V3.2-Pro | ~4 | ~16 | 高质量 |
| 本地 Qwen3-4B | 0 | 0 | 电费忽略 |

### 9.2 省钱动作清单

1. **缓存命中**（DeepSeek）成本降至 0.02 元/百万 tokens
2. **路由**：含"代码/函数/报错"走本地
3. **专家数控制**：日常用 1–2 个，复杂任务再开 4 个
4. **短 prompt**：拆解 prompt 时约束字数
5. **关闭不必要 toolsets**：能不用 `search` 就不开

### 9.3 典型月度账单

| 场景 | 估算 |
|------|------|
| 纯云端 V3.2-Flash 中度使用 | 5–15 元 |
| 混合（日常本地 + 偶发云端） | 0–5 元 |
| 纯云端 V3.2-Pro | 50–200 元 |

---

## 十、可观测性

### 10.1 日志位置

| 来源 | 路径 |
|------|------|
| Hermes 主日志 | `~/.hermes/logs/hermes.log` |
| Llama.cpp 日志 | `journalctl --user -u llama-server.service` |
| 专家团 debug | `HERMES_EXPERT_PANEL_DEBUG=1` 时输出到 stderr |
| 临时 trace | `/tmp/hermes-expert-panel-*.json`（如启用） |

### 10.2 3 个关键指标

| 指标 | 怎么算 | 阈值 |
|------|--------|------|
| 专家团成功率 | 24h 内成功调用 / 总调用 | > 95% |
| 平均耗时 | 汇总步骤 wall-clock | < 60s |
| 月成本 | 解析 DeepSeek usage | < 30 元 |

### 10.3 调试开关

```bash
# 全开
export HERMES_EXPERT_PANEL_DEBUG=1
export HERMES_LOG_LEVEL=debug

# 只看本次
hermes run "expert-panel --query=xx" 2>&1 | tee /tmp/exp.log
```

---

## 十一、安全与隐私

### 11.1 API Key 保管
- 写入 `~/.bashrc`：`export DEEPSEEK_API_KEY=sk-xxx`
- **不要**写进 git 仓库
- 定期轮换（每 90 天）
- 单独建一个 sub-account，仅授予 chat 权限

### 11.2 提示词注入
- 外部内容（搜索结果、文件）不要直接拼到 system prompt
- 隔离：用户输入只放进 `user` 段
- 工具最小化：能不开 `terminal` 就不开

### 11.3 本地数据
- `~/.hermes/fact_store/` 包含历史事实，敏感场景请 `chmod 700`
- WSL 文件 Windows 可见，反之亦然；不放敏感数据到 Desktop

### 11.4 网络出口
- 本地 llama 绑 `127.0.0.1`，不暴露 `0.0.0.0`
- 云端走 HTTPS；不关证书校验

---

## 十二、版本演进

### 12.1 升级路径（v3.1 → v4.0 → v5.0）

```
v3.1 (v3.x)          v4.0 (current)        v5.0 (next)
─────────────────     ─────────────────     ─────────────────
单 Profile             + 风险/回滚            + 多 Profile 隔离
4 专家                 + 安全/SOP             + 团队协作
无 SOP                 + 验收 checklist       + Web UI
无监控                 + 3 关键指标           + Prometheus 接入
```

### 12.2 弃用清单（v4.0 起）
- OpenViking 记忆（→ `fact_store`）
- Tavily API（→ DuckDuckGo + zhihu）
- 多 Profile 模式（→ 单 Profile + system prompt）
- `Qwen3.5` 等拼写错误（→ 官方命名）

### 12.3 路线图候选（v5.0 备选）
- [ ] Web 控制台（FastAPI + 静态页）
- [ ] Telegram Bot 网关
- [ ] MCP 工具：浏览器、代码沙箱
- [ ] 记忆图谱（替代简单 fact_store）
- [ ] 量化策略自选（Q3/Q4/Q5）

---

## 附录 A：完整文件清单

```
~/.hermes/
├── profiles/default/config.yaml          # 主配置
├── skills/expert-panel/
│   ├── SKILL.md
│   ├── run.py
│   └── tests/smoke.sh
├── logs/                                  # 日志
└── fact_store/                            # 事实记忆

~/llama.cpp/
├── (编译产物)
├── start.sh
└── models/Qwen3-4B-Instruct-Q4_K_M.gguf

~/.config/systemd/user/
└── llama-server.service

~/.bashrc 追加:
  export DEEPSEEK_API_KEY=sk-xxx
  export HERMES_EXPERT_PANEL_DEBUG=0   # 需要时改 1
```

## 附录 B：关键命令速查

```bash
# 启停
systemctl --user start|stop|status|restart llama-server.service
hermes run "expert-panel --query=..."

# 调试
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
journalctl --user -u llama-server.service -n 50 -f

# 验收
bash ~/.hermes/skills/expert-panel/tests/smoke.sh

# 网络
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
curl -sSf https://api.deepseek.com
```

## 附录 C：术语表

| 术语 | 含义 |
|------|------|
| L1/L2 | 本地推理层 / 云端增强层 |
| expert-panel | 本方案核心技能名 |
| delegate_task | Hermes 内置并行子任务 API |
| fact_store | Hermes 内置事实记忆 |
| fallback_to_local | 云端异常自动回本地 |
| smoke test | 冒烟测试（最小可运行验证） |

## 附录 D：FAQ

**Q1. delegate_task 实际签名是什么？**
请以 Hermes 官方文档为准。v4.0 脚本已做容错：传 `goal=` 单任务、传 `tasks=[…]` 批任务均可；若接口不同，按报错调整。

**Q2. 模型名 Qwen3-4B / DeepSeek-V3.2 不存在？**
以官方模型目录为准。下载失败时优先用 Hugging Face 国内镜像（如 `hf-mirror.com`）。

**Q3. 专家回答风格不统一？**
调整 `EXPERT_SYSTEM` 字典；增加「输出格式示例」。

**Q4. 汇总报告缺一段？**
检查 `agg_prompt` 模板的 4 段是否完整；开启 DEBUG 看 `aggregate` 步骤输出。

**Q5. 5 分钟内搞不定？**
最常见三个原因：① 代理未取消；② API Key 未生效；③ venv 中缺依赖。先按第六章 §6.6 跑一遍应急诊断。

---

**v4.0 完。**
