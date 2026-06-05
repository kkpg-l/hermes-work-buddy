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
| 性能调优 | 缺 | 新增并发控制、Token 优化、本地模型调优、智能路由 |
| 迁移指南 | 缺 | 新增 v3.1 → v4.0 分步迁移 |

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
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/install.sh | bash

# 方式二：git clone
git clone https://github.com/kkpg-l/hermes-work-buddy.git
cd hermes-work-buddy && bash install.sh
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

### 4.2 run.py（v4.0 修正版）

见 `skills/expert-panel/run.py`。

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
# 从 https://huggingface.co/Qwen/Qwen3-4B-Instruct-GGUF 或国内镜像下载
```

### 5.3 启动并注册为 systemd 用户服务

见 `local-llm/start.sh` 和 `local-llm/llama-server.service`。

### 5.4 健康检查

```bash
curl -s http://127.0.0.1:8080/health
# 期望：{"status":"ok"}
```

### 5.5 在 Hermes 中注册

见 `config/config.example.yaml`。

### 5.6 关停本地（回退到纯云端）

```bash
systemctl --user stop --now llama-server.service
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

**示例：添加 UI/UX 专家**

```python
# run.py 中添加
ALL_EXPERTS = ("tech", "product", "business", "research", "ux")

EXPERT_SYSTEM = {
    # ... 原有 ...
    "ux": "你是资深 UX 设计专家（交互 / 视觉 / 可用性），输出结构化、引用设计原则。",
}
```

### 6.3 升级 Hermes

```bash
systemctl --user stop llama-server.service   # 如果用了本地
pip install -U hermes-agent
bash ~/.hermes/skills/expert-panel/tests/smoke.sh
systemctl --user start llama-server.service
```

### 6.4 升级 Llama.cpp / 模型

```bash
cp -r ~/llama.cpp ~/llama.cpp.bak.$(date +%Y%m%d)
cd ~/llama.cpp && git pull && make -j$(nproc)
mv models/Qwen3-4B-Instruct-Q4_K_M.gguf models/Qwen3-4B-Instruct-Q4_K_M.bak.gguf
# 下载新版
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

见 `skills/expert-panel/tests/smoke.sh`。

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
| Hermes 版本升级不兼容 | 低 | 高 | 备份 venv；保留旧版 wheel |

### 8.2 回滚剧本

| 场景 | 步骤 |
|------|------|
| 云端炸 | `HERMES_FORCE_LOCAL=1` + 启 llama |
| 本地炸 | `systemctl --user stop llama-server` + 用云端 |
| 技能升级后异常 | `cp run.py.bak run.py` |
| 整个专家团不稳 | `mv ~/.hermes/skills/expert-panel ~/.hermes/skills/expert-panel.off` |
| 配置文件破坏 | `git -C ~/.hermes checkout -- profiles/`（如有版本控制） |
| Hermes 升级失败 | `pip install hermes-agent==旧版本号` |

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
6. **温度调低**：`temperature: 0.1` 减少 token 浪费
7. **最大 token 限制**：在 config 中设 `max_tokens: 2048`

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

## 十二、性能调优

### 12.1 并发控制

| 参数 | 默认 | 调优建议 |
|------|------|----------|
| 并行专家数 | 4 | 日常 2，复杂 4 |
| delegate_task 超时 | 120 s | 网络差时增至 180 s |
| 串行模式 | off | API 限流时开启 |

### 12.2 Token 优化

```python
# run.py 中可调整的 Token 控制点

# 1. 拆解 prompt 约束
plan_prompt = f"""...
约束：
- prompt 不超过 200 字
- 每个 expert 只输出 5 个要点"""

# 2. 专家输出约束
"输出要求：\n- 不少于 5 个要点\n- 每个要点不超过 50 字\n- 关键结论加粗"

# 3. 汇总约束
"严格按四段输出，总字数不超过 2000 字"
```

### 12.3 本地模型调优

```bash
# Llama.cpp 关键参数
./llama-server \
  --model models/Qwen3-4B-Instruct-Q4_K_M.gguf \
  --n-gpu-layers 25 \          # GPU 层数，显存不够可降到 15
  --n-ctx 4096 \               # 上下文窗口，4B 模型建议 2048-4096
  --threads 8 \                # CPU 线程，建议 = 物理核心数
  --batch-size 512 \           # 批大小，越大吞吐越高但延迟也高
  --mlock                      # 锁定内存，避免 swap
```

| 参数 | 显存 6GB | 显存 8GB+ |
|------|---------|----------|
| n-gpu-layers | 15 | 25 |
| n-ctx | 2048 | 4096 |
| batch-size | 256 | 512 |

### 12.4 智能路由

```yaml
# config.yaml 路由规则
models:
  routes:
    # 简单代码问题 → 本地
    - when_prompt_matches: ["代码", "函数", "报错", "debug", "语法"]
      use: local-qwen
    # 长文本/研究 → 云端
    - when_prompt_length_gt: 500
      use: deepseek-chat
    # 默认 → 云端
    - default: deepseek-chat
```

---

## 十三、迁移指南（v3.1 → v4.0）

### 13.1 迁移步骤

```bash
# 1. 备份 v3.1
cp -r ~/.hermes/skills/expert-panel ~/.hermes/skills/expert-panel.v3.1.bak

# 2. 拉取 v4.0
git clone https://github.com/kkpg-l/hermes-work-buddy.git /tmp/hermes-work-buddy

# 3. 替换技能文件
cp /tmp/hermes-work-buddy/skills/expert-panel/SKILL.md ~/.hermes/skills/expert-panel/
cp /tmp/hermes-work-buddy/skills/expert-panel/run.py ~/.hermes/skills/expert-panel/

# 4. 更新配置（如需本地模型）
cp /tmp/hermes-work-buddy/config/config.example.yaml ~/.hermes/profiles/default/config.yaml
# 按需修改 API Key 等

# 5. 验证
bash /tmp/hermes-work-buddy/skills/expert-panel/tests/smoke.sh

# 6. 清理
rm -rf /tmp/hermes-work-buddy
```

### 13.2 配置差异

| 项 | v3.1 | v4.0 |
|----|------|------|
| 记忆 | OpenViking | fact_store + session_search |
| 搜索 | Tavily API | DuckDuckGo + zhihu |
| Profile | 5 个独立 | 1 个主配置 |
| 本地模型 | 必须 | 可选 |
| 调试 | 无 | DEBUG 环境变量 |

### 13.3 回退到 v3.1

```bash
# 如果 v4.0 有问题
cp -r ~/.hermes/skills/expert-panel.v3.1.bak/* ~/.hermes/skills/expert-panel/
```

---

## 十四、版本演进

### 14.1 升级路径

```
v3.1 (v3.x)          v4.0 (current)        v5.0 (next)
─────────────────     ─────────────────     ─────────────────
单 Profile             + 风险/回滚            + 多 Profile 隔离
4 专家                 + 安全/SOP             + 团队协作
无 SOP                 + 验收 checklist       + Web UI
无监控                 + 3 关键指标           + Prometheus 接入
无调优                 + 性能调优             + 自适应路由
无迁移                 + 迁移指南             + 自动迁移脚本
```

### 14.2 弃用清单（v4.0 起）
- OpenViking 记忆（→ `fact_store`）
- Tavily API（→ DuckDuckGo + zhihu）
- 多 Profile 模式（→ 单 Profile + system prompt）
- `Qwen3.5` 等拼写错误（→ 官方命名）

### 14.3 路线图候选（v5.0 备选）
- [ ] Web 控制台（FastAPI + 静态页）
- [ ] Telegram Bot 网关
- [ ] MCP 工具：浏览器、代码沙箱
- [ ] 记忆图谱（替代简单 fact_store）
- [ ] 量化策略自选（Q3/Q4/Q5）
- [ ] 自动迁移脚本（v3.x → v5.0）
- [ ] 多用户隔离 + 计费

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

# 健康检查
bash /path/to/hermes-work-buddy/scripts/health-check.sh

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
| fan-out | 并行分发子任务 |
| aggregate | 汇总子任务结果 |

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

**Q6. 如何限制 Token 消耗？**  
见第十二章「性能调优」→ Token 优化。

**Q7. 本地模型加载后首 token 很慢？**  
增加 `--n-gpu-layers`、开启 `--mlock`、确保 GPU 驱动正常。

**Q8. WSL2 里 GPU 不可用？**  
确认已安装 NVIDIA CUDA on WSL：`nvidia-smi` 应显示 GPU 信息。

---

**v4.0 完。**
