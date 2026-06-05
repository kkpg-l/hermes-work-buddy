<div align="center">

# 🤝 Hermes Work Buddy

**多专家并行分析 · 本地+云端混合推理 · 5 分钟部署**

[![版本](https://img.shields.io/badge/version-v4.0-blue.svg)](https://github.com/kkpg-l/hermes-work-buddy)
[![环境](https://img.shields.io/badge/env-WSL2%20%2B%20Win11-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[English](#english) · [中文](#中文)

</div>

---

<a id="中文"></a>

## ✨ 这是什么？

Hermes Work Buddy 是一个基于 [Hermes Agent](https://github.com/nicepkg/hermes) 的**多专家并行分析系统**。

你提一个问题，4 个 AI 专家（技术 / 产品 / 商业 / 研究）**同时分析**，最后汇总成结构化报告。

```
你的问题
  │
  ▼
主协调员拆解
  │
  ├─► 🔧 技术专家  ──┐
  ├─► 📦 产品专家  ──┤ 并行
  ├─► 💰 商业专家  ──┤ delegate_task
  └─► 📚 研究专家  ──┘
                        │
            汇总各专家分析结果
                        │
                        ▼
              📋 结构化最终报告
```

## 🎯 核心特性

| 特性 | 说明 |
|------|------|
| 🧠 多专家并行 | 技术、产品、商业、研究 4 视角同时分析 |
| ☁️ 本地+云端 | 日常走 DeepSeek API，可选本地 Qwen3-4B 省钱/离线 |
| ⚡ 5 分钟部署 | 一个技能脚本 + 一份配置，复制粘贴即用 |
| 🔄 可灰度可回滚 | 先开 1 个专家 → 全开 → 引入本地，每步可退 |
| 🛡️ 自动降级 | API 挂了回本地，本地 OOM 回云端，拆解失败退化为单专家 |
| 🔍 调试友好 | DEBUG 模式、串行模式、单专家模式 |

## 📸 效果演示

```bash
$ hermes run "expert-panel --query=对比 React 和 Vue 的技术选型"

## 摘要
React 和 Vue 各有优势：React 生态更大、灵活性更高，Vue 上手更快、
约定更强。对于中小项目推荐 Vue，大型企业级应用推荐 React。

## 详细分析

### 技术维度
- React: 虚拟DOM + JSX，社区生态庞大，TypeScript 支持成熟
- Vue: 模板语法 + 响应式，Composition API 对标 React Hooks
...

### 产品维度
- React: 更适合复杂交互、定制化需求高的场景
- Vue: 更适合快速迭代、团队技术栈统一的场景
...

## 各专家观点对比
- 一致点：两者都是优秀的现代前端框架
- 分歧点：学习曲线 vs 灵活度取舍
- 互补点：技术选型需结合团队和业务

## 结论与建议
1. [P0] 中小项目选 Vue，降低团队学习成本
2. [P0] 大型/复杂项目选 React，生态和灵活性更强
3. [P1] 考虑团队现有技术栈，迁移成本是关键因素
```

## 🚀 快速开始

### 前提

- WSL2 (Ubuntu 24.04) + [Hermes Agent](https://github.com/nicepkg/hermes) 已安装
- DeepSeek API Key（可选，没有也能跑）

### 安装

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/scripts/install.sh | bash

# 或手动安装
git clone https://github.com/kkpg-l/hermes-work-buddy.git
cd hermes-work-buddy && bash scripts/install.sh
```

### 使用

```bash
# 基本用法：4 专家并行分析
hermes run "expert-panel --query=分析 React 和 Vue 的优劣"

# 只要技术和产品专家
hermes run "expert-panel --query=评估 AI 写作助手方案 --experts=tech,product"

# 串行调试模式
hermes run "expert-panel --query=测试 --mode=serial"

# 开启调试输出
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
```

### 验证

```bash
bash ~/.hermes/skills/expert-panel/tests/smoke.sh
```

## 📁 项目结构

```
hermes-work-buddy/
├── README.md                          # 本文件
├── LICENSE                             # MIT
├── CHANGELOG.md                        # 变更日志
├── .gitignore
├── docs/
│   └── Hermes-Work-Buddy-专家团部署方案-v4.0.md   # 完整方案（14章+4附录）
├── skills/expert-panel/
│   ├── SKILL.md                        # Hermes 技能描述
│   ├── run.py                          # 核心脚本
│   └── tests/smoke.sh                  # 冒烟测试
├── config/
│   └── config.example.yaml             # 配置示例（含智能路由）
├── scripts/
│   ├── install.sh                      # 一键安装
│   ├── health-check.sh                 # 健康检查
│   └── uninstall.sh                    # 卸载
└── local-llm/
    ├── start.sh                        # Llama.cpp 启动脚本
    └── llama-server.service            # systemd 服务
```

## 💰 成本参考

| 场景 | 月估算 |
|------|--------|
| 纯 DeepSeek-V3.2-Flash | 5–15 元 |
| 混合（日常本地 + 偶发云端） | 0–5 元 |
| DeepSeek-V3.2-Pro 高质量 | 50–200 元 |

## 🔧 可选：本地推理

有 GPU（≥6 GB 显存）？跑本地模型省钱/离线：

```bash
# 安装 Llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp
cd ~/llama.cpp && make -j$(nproc)

# 下载 Qwen3-4B-Instruct Q4_K_M 到 ~/llama.cpp/models/

# 启动（含开机自启）
bash local-llm/start.sh
mkdir -p ~/.config/systemd/user && cp local-llm/llama-server.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now llama-server.service
```

## 📖 文档

- [完整部署方案 v4.0](docs/Hermes-Work-Buddy-专家团部署方案-v4.0.md) — 14 章 + 4 附录
  - 架构设计 · 5分钟部署 · 完整代码 · 本地推理
  - SOP · 验收 · 风险与回滚 · 成本策略
  - 可观测性 · 安全隐私 · 性能调优 · 迁移指南

## ❓ FAQ

**Q: delegate_task 报错？**
请以 Hermes 官方文档为准，v4.0 脚本已做容错降级。

**Q: 代理导致 API 调不通？**
```bash
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

**Q: 本地模型 OOM？**
换 Q3_K 量化版，或直接关本地走云端：`systemctl --user stop llama-server.service`

**Q: 如何添加新专家？**
在 `run.py` 的 `ALL_EXPERTS` 和 `EXPERT_SYSTEM` 各加一行即可，详见 [SOP](docs/Hermes-Work-Buddy-专家团部署方案-v4.0.md)。

## 🤝 参与贡献

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/my-feature`
3. 提交：`git commit -m 'feat: add my feature'`
4. 推送：`git push origin feat/my-feature`
5. 提交 Pull Request

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐

## 📄 License

[MIT](LICENSE) © 2026 kkpg-l

---

<a id="english"></a>

## ✨ What is this?

Hermes Work Buddy is a **multi-expert parallel analysis system** built on [Hermes Agent](https://github.com/nicepkg/hermes).

Ask one question, get 4 AI experts (Tech / Product / Business / Research) analyzing **in parallel**, then a synthesized structured report.

## 🚀 Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/scripts/install.sh | bash

# Use
hermes run "expert-panel --query=Analyze the pros and cons of React vs Vue"

# Verify
bash ~/.hermes/skills/expert-panel/tests/smoke.sh
```

## 💰 Cost

| Scenario | Monthly Est. |
|----------|-------------|
| DeepSeek-V3.2-Flash only | ¥5–15 |
| Hybrid (local + cloud) | ¥0–5 |

## 📄 License

[MIT](LICENSE) © 2026 kkpg-l
