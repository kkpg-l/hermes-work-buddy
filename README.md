# Hermes Work Buddy 专家团

> 多专家并行分析 · 本地 + 云端混合推理 · 5 分钟部署

[![版本](https://img.shields.io/badge/version-v4.0-blue.svg)](https://github.com/kkpg-l/hermes-work-buddy)
[![环境](https://img.shields.io/badge/env-WSL2%20%2B%20Win11-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## 这是什么？

Hermes Work Buddy 是一个基于 [Hermes Agent](https://github.com/nicepkg/hermes) 的多专家并行分析系统。你提一个问题，4 个 AI 专家（技术 / 产品 / 商业 / 研究）同时分析，最后汇总成结构化报告。

```
你的问题 → 主协调员拆解 → 4 个专家并行分析 → 汇总报告
```

## 核心特性

- **多专家并行**：技术、产品、商业、研究 4 视角同时分析
- **本地 + 云端**：日常走 DeepSeek API，可选本地 Qwen3-4B 省钱/离线
- **5 分钟部署**：一个技能脚本 + 一份配置，复制粘贴即用
- **可灰度可回滚**：先开 1 个专家 → 全开 → 引入本地，每步可退
- **自动降级**：API 挂了回本地，本地 OOM 回云端，拆解失败退化为单专家

## 快速开始

### 前提

- WSL2 (Ubuntu 24.04) + Hermes Agent 已安装
- DeepSeek API Key（可选，没有也能跑）

### 安装

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/kkpg-l/hermes-work-buddy/main/install.sh | bash

# 或手动安装
git clone https://github.com/kkpg-l/hermes-work-buddy.git
cd hermes-work-buddy
bash install.sh
```

### 使用

```bash
# 基本用法
hermes run "expert-panel --query=分析 React 和 Vue 的优劣"

# 只要技术和产品专家
hermes run "expert-panel --query=评估 AI 写作助手产品方案 --experts=tech,product"

# 串行调试
hermes run "expert-panel --query=测试 --mode=serial"

# 开启调试
HERMES_EXPERT_PANEL_DEBUG=1 hermes run "expert-panel --query=自检"
```

### 验证

```bash
bash ~/.hermes/skills/expert-panel/tests/smoke.sh
```

## 项目结构

```
hermes-work-buddy/
├── README.md                          # 本文件
├── CHANGELOG.md                       # 变更日志
├── .gitignore
├── docs/
│   └── Hermes-Work-Buddy-专家团部署方案-v4.0.md   # 完整方案文档
├── skills/
│   └── expert-panel/
│       ├── SKILL.md                   # Hermes 技能描述
│       ├── run.py                     # 核心脚本
│       └── tests/
│           └── smoke.sh               # 冒烟测试
├── config/
│   └── config.example.yaml            # 配置示例
├── scripts/
│   ├── install.sh                     # 一键安装
│   ├── health-check.sh                # 健康检查
│   └── uninstall.sh                   # 卸载
└── local-llm/
    ├── start.sh                       # Llama.cpp 启动脚本
    └── llama-server.service           # systemd 服务文件
```

## 可选：本地推理

如果你有 GPU（≥6 GB 显存），可以跑本地模型省钱/离线：

```bash
# 安装 Llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp
cd ~/llama.cpp && make -j$(nproc)

# 下载 Qwen3-4B-Instruct Q4_K_M 量化版到 ~/llama.cpp/models/

# 启动
bash local-llm/start.sh

# 注册为开机自启
mkdir -p ~/.config/systemd/user
cp local-llm/llama-server.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now llama-server.service
```

## 成本参考

| 场景 | 月估算 |
|------|--------|
| 纯 DeepSeek-V3.2-Flash | 5–15 元 |
| 混合（日常本地 + 偶发云端） | 0–5 元 |
| DeepSeek-V3.2-Pro 高质量 | 50–200 元 |

## 文档

- [完整部署方案 v4.0](docs/Hermes-Work-Buddy-专家团部署方案-v4.0.md) — 12 章 + 4 附录，含 SOP、风险、验收、安全

## 常见问题

**Q: delegate_task 报错？**
请以 Hermes 官方文档为准，v4.0 脚本已做容错降级。

**Q: 代理导致 API 调不通？**
```bash
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

**Q: 本地模型 OOM？**
换 Q3_K 量化版，或直接关本地走云端：`systemctl --user stop llama-server.service`

## License

MIT
