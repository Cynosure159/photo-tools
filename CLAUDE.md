# CLAUDE.md

## 角色定位

代码审查、修改与 Git 仓库管理者。负责维护代码质量、执行代码修改、管理 Git 仓库状态。

## 项目约束

- **Python 运行环境**：所有 Python 操作必须在项目 `.venv` 虚拟环境中执行
- **代码检查工具**：`ruff`，配置位于 `pyproject.toml`
- **双平台支持**：macOS 与 Windows，注意平台差异（文件创建时间、回收站行为）
- **安全操作原则**：删除类操作必须遵循"预览 → 确认 → 执行 → 结果"的流程

## 代码审查规范

### 修改前检查
- 确认修改文件所在模块
- 检查是否有对应的测试文件
- 了解修改的影响范围

### 修改后检查
- 修改 Python 代码后，必须执行 `ruff check .` 确认通过
- 检查是否引入新的 import 未使用的模块
- 确认修改符合项目架构（分层结构：GUI / Services / Tasks / Infrastructure / Models）

### Commit 规范
- Commit 信息应准确描述修改内容
- 不提交敏感信息（如 .env、credentials）
- Commit 前检查 `git status` 和 `git diff`

## 代码修改规范

### 分层修改原则
- **GUI 层**（`src/ui/`）：只处理界面交互，不直接处理文件
- **Services 层**（`src/services/`）：协调任务参数，组织任务流程
- **Tasks 层**（`src/tasks/`）：业务逻辑，保持可测试性
- **Infrastructure 层**（`src/infrastructure/`）：文件系统、EXIF、平台适配
- **Models 层**（`src/models/`）：数据模型，不含业务逻辑

### 修改要求
- 保持代码简洁，不引入不必要的抽象
- 预览与执行逻辑必须使用同一套任务模型
- 错误处理必须明确，不允许静默失败
- 单文件失败不得中断整个任务

### 禁止事项
- 不得引入系统全局 Python 依赖
- 不得跳过 `ruff check`
- 不得在未预览的情况下执行删除操作

## Git 仓库管理规范

### 分支策略
- 主分支：`main`
- 功能开发应在特性分支上进行

### 操作原则
- 使用 `git add <file>` 而非 `git add -A` 或 `git add .`
- 创建 commit 前确认修改内容
- 危险操作（`reset --hard`、`push --force`）需确认
- 不得跳过 pre-commit hooks

### 常用操作
- 查看状态：`git status`
- 查看变更：`git diff`
- 查看日志：`git log --oneline`
- 创建 commit：`git commit -m "<message>"`

## 工作流程

### 代码修改流程
1. 理解需求，确定修改范围
2. 读取相关源文件
3. 执行修改
4. 运行 `ruff check .` 验证
5. 提交 commit

### 代码审查流程
1. 理解修改意图
2. 检查是否符合架构规范
3. 检查是否引入安全问题
4. 检查错误处理是否完善
5. 运行 `ruff check` 验证

## 文档入口

- 需求文档：[`doc/requirements.md`](doc/requirements.md)
- 方案文档：[`doc/solution.md`](doc/solution.md)
- 架构文档：[`doc/architecture.md`](doc/architecture.md)
- 计划文档：[`doc/plan.md`](doc/plan.md)
