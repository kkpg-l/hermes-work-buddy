# Changelog

All notable changes to this project will be documented in this file.

## [v4.1] - 2026-06-05

### Added
- **使用场景举例**：4 个典型场景 + 推荐专家组合（技术选型/产品评估/架构审查/市场策略）
- **Hermes 生态联动**：HeartFlow 验证、planning-workflow 联动、cronjob 定时任务
- **专家角色扩展**：从 4 个扩展到 12 个（+ux/data/marketing/seo/security/legal/ops/content）
- **输出格式扩展**：4 种内置模板（default/executive/weekly-report/comparison）+ 自定义模板
- **输出目标扩展**：文件/飞书 Webhook/Notion API/PPT（python-pptx）
- **智能路由**：`--route=auto` 根据问题内容自动选择专家数量和组合
- **自定义报告模板**：用户可在 templates/ 目录下创建 .md 模板
- **多轮上下文**：session_search 跨轮引用 + fact_store 历史对比（`--compare-history=true`）
- **Skill 组合**：grill-me → Work Buddy、brainstorming → Work Buddy 等工作流
- **fact_store 集成**：自动保存报告到 `~/.hermes/fact_store/expert-panel/`

### Changed
- 文档版本从 v4.0 升级到 v4.1（22 章 + 4 附录）
- run.py 新增 auto_route、REPORT_TEMPLATES、fact_store 读写
- SKILL.md 新增扩展角色、参数说明、Skill 组合示例

---

## [v4.0] - 2026-06-05

### Added
- 完整 v4.0 部署方案文档（14 章 + 4 附录）
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
- 6 类 SOP
- 安全与隐私章节
- 可观测性章节
- 性能调优章节
- 迁移指南

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
- `delegate_task` 签名混用
- 本地模型绑定 `0.0.0.0` 的安全隐患

---

## [v3.1] - 2026-06-04

### Added
- 初始公开版本
- 4 专家并行分析
- `delegate_task` 并行调度
- 可选本地 Llama.cpp + Qwen GGUF
- 基础排障指南
