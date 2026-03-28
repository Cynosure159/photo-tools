# AGENTS

## 文档入口

- 需求文档：[`/doc/requirements.md`](/Users/cy/Projects/photo-tools/doc/requirements.md)
- 方案文档：[`/doc/solution.md`](/Users/cy/Projects/photo-tools/doc/solution.md)
- 架构文档：[`/doc/architecture.md`](/Users/cy/Projects/photo-tools/doc/architecture.md)
- 计划文档：[`/doc/plan.md`](/Users/cy/Projects/photo-tools/doc/plan.md)

## 项目约束

- 项目定位为本地照片处理 GUI 工具，技术栈为 Python + PyQt。
- Python 必须在项目 `.venv` 虚拟环境中运行，不允许依赖系统全局 Python 作为默认运行环境。
- 当前首版只覆盖两个场景：批量修改照片时间信息、按成片保留原片并清理其他文件。
- 所有高风险操作必须遵循“先预览，再执行，再展示结果”的流程。
- 删除类操作必须提供二次确认，且永久删除要有更强提示。
- 实现阶段默认兼顾 macOS 与 Windows，并明确处理平台差异带来的文件时间与回收站行为问题。
