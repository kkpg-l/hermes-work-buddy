<div align="center">

# 🤝 Hermes Work Buddy

**多专家并行分析 · 本地+云端混合推理 · 5 分钟部署**

[![版本](https://img.shields.io/badge/version-v4.1-blue.svg)](https://github.com/kkpg-l/hermes-work-buddy)
[![环境](https://img.shields.io/badge/env-WSL2%20%2B%20Win11-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

[English](#english) · [中文](#中文)

</div>

---

<a id="中文"></a>

## ✨ 这是什么？

Hermes Work Buddy 是一个基于 [Hermes Agent](https://github.com/nicepkg/hermes) 的**多专家并行分析系统**。

你提一个问题，最多 12 个 AI 专家同时分析，最后汇总成结构化报告。

## 🎯 核心特性

| 特性 | 说明 |
|------|------|
| 🧠 多专家并行 | 12 个专家角色（技术/产品/商业/研究/UX/数据/营销/SEO/安全/法律/运维/内容） |
| ☁️ 本地+云端 | 日常走 DeepSeek API，可选本地 Qwen3-4B 省钱/离线 |
| ⚡ 5 分钟部署 | 一个技能脚本 + 一份配置，复制粘贴即用 |
| 🤖 智能路由 | `--route=auto` 自动选择最合适的专家组合 |
| 📝 报告模板 | 4 种内置模板 + 自定义模板 |
| 📊 多轮上下文 | 历史对比、跨会话引用 |
| 🔄 可灰度可回滚 | 先开 1 个专家 → 全开 → 引入本地，每步可退 |
| 🛡️ 自动降级 | API 挂了回本地，本地 OOM 回云端，拆解失败退化为单专家 |
| 🔗 生态联动 | HeartFlow 验证 / planning-workflow / cronjob 定时任务 |
| 🧩 Skill 组合 | grill-me → Work Buddy / brainstorming → Work Buddy |

## 🚀 快速开始

```bash
# 安装
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/scripts/install.sh | bash

# 使用
hermes run "expert-panel --query=分析 React 和 Vue 的优劣"
hermes run "expert-panel --query=AI 写作助手方案 --route=auto"
hermes run "expert-panel --query=xxx --template=executive"
hermes run "expert-panel --query=xxx --compare-history=true"

# 验证
bash ~/.hermes/skills/expert-panel/tests/smoke.sh
```

## 💰 成本参考

| 场景 | 月估算 |
|------|--------|
| 纯 DeepSeek-V3.2-Flash | 5–15 元 |
| 混合（日常本地 + 偶发云端） | 0–5 元 |

## 📖 文档

- [完整部署方案 v4.1](docs/Hermes-Work-Buddy-专家团部署方案-v4.1.md) — 22 章 + 4 附录

## ❓ FAQ

**Q: 智能路由不准？** 在 `run.py` 的 `KEYWORD_MAP` 中补充领域关键词。

**Q: 代理导致 API 调不通？** `unset http_proxy https_proxy all_proxy`

**Q: 如何添加自定义专家？** 在 `run.py` 的 `EXPERT_SYSTEM` 添加一行即可。

**Q: 如何自定义报告格式？** 在 `~/.hermes/skills/expert-panel/templates/` 下创建 `.md` 模板文件。

## 🤝 参与贡献

1. Fork → 2. 分支 → 3. 提交 → 4. PR

## 📄 License

[MIT](LICENSE) © 2026 kkpg-l

---

<a id="english"></a>

## ✨ What is this?

Hermes Work Buddy is a **multi-expert parallel analysis system** built on [Hermes Agent](https://github.com/nicepkg/hermes).

## 🚀 Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/scripts/install.sh | bash
hermes run "expert-panel --query=Analyze React vs Vue --route=auto"
```

## 📄 License

[MIT](LICENSE) © 2026 kkpg-l
