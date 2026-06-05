# Changelog

All notable changes to this project will be documented in this file.

## [v4.0] - 2026-06-05

### Added
- 完整 v4.0 部署方案文档（12 章 + 4 附录）
- `run.py` v4.0：修正 parse_args bug、delegate_task 签名、错误降级
- 新增 `--experts` 参数：按需选择专家
- 新增 `--mode=serial` 串行调试模式
- 新增 `HERMES_EXPERT_PANEL_DEBUG` 调试开关
- 冒烟测试 `smoke.sh`（5 条）
- 一键安装脚本 `install.sh`
- 健康检查脚本 `health-check.sh`
- 卸载脚本 `uninstall.sh`
- Llama.cpp 启动脚本 + systemd 服务文件
- 配置示例 `config.example.yaml`
- 风险登记表 + 回滚剧本
- 6 类 SOP（日常/添加专家/升级/故障应急）
- 安全与隐私章节（API Key / 提示词注入 / 网络出口）
- 可观测性（日志位置 / 3 关键指标 / 调试开关）
- 性能调优章节（并发/Token/本地模型/路由）
- 迁移指南（v3.1 → v4.0 分步操作）

### Changed
- 模型名修正：`Qwen3.5-4B` → `Qwen3-4B-Instruct`，`DeepSeek-V4-Flash` → `DeepSeek-V3.2-Flash`
- 专家隔离方式：多 Profile → 单 Profile + system prompt
- 记忆方案：OpenViking → Hermes 内置 `fact_store` + `session_search`
- 搜索方案：Tavily API → DuckDuckGo + zhihu-global-search

### Removed
- OpenViking 依赖
- Tavily API 依赖
- 多 Profile 配置模式

### Fixed
- `parse_args` 对 `--key --flag2` 形式的解析 bug
- `delegate_task` 签名混用（统一为 `goal=` / `tasks=` 分离调用）
- 本地模型绑定 `0.0.0.0` 的安全隐患（改为 `127.0.0.1`）

---

## [v3.1] - 2026-06-04

### Added
- 初始公开版本
- 4 专家并行分析（技术/产品/商业/研究）
- `delegate_task` 并行调度
- 可选本地 Llama.cpp + Qwen GGUF
- 基础排障指南
