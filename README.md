# photo-tools

本项目是一个基于 Python + PyQt 的本地照片处理 GUI 工具。

当前阶段目标：

- 建立项目基础设施
- 统一 Python 运行环境
- 搭建 GUI 骨架并跑通基础交互
- 实现时间修改功能的真实扫描、预览与执行

## 运行约束

Python 必须在项目根目录下的 `.venv` 虚拟环境中运行，不允许默认使用系统全局 Python。

## 环境准备

创建虚拟环境：

```bash
python3 -m venv .venv
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

代码检查：

```bash
ruff check .
```

运行测试：

```bash
pytest
```

约定：

- 每次修改 Python 代码后，都需要在项目 `.venv` 中执行一次 `ruff check .`
- 测试默认使用 `pytest`
- `ruff` 配置位于项目根目录的 [`pyproject.toml`](/Users/cy/Projects/photo-tools/pyproject.toml)

## 启动项目

```bash
python -m src.app.main
```

如果未激活项目 `.venv`，启动入口会直接报错并退出。

## 目录结构

```text
photo-tools/
  AGENTS.md
  README.md
  requirements.txt
  doc/
  src/
    app/
    infrastructure/
    models/
    services/
    tasks/
    ui/
  tests/
```

## 当前状态

当前已完成阶段 3 的时间修改功能：

- 主窗口支持两个功能页签切换
- 时间修改页已支持真实文件扫描、偏移预览、批量执行和结果统计
- 原片筛选页已支持真实的成片/原片扫描、basename 匹配、预览统计、回收站移动与永久删除

当前限制：

- 创建时间写入目前仅在 Windows 上实现；macOS 会在预览中明确标记为不可写入
- EXIF 拍摄时间写入目前支持 `jpg/jpeg/tif/tiff`
- 原片筛选按照片文件类型扫描，V1 默认不将 `.xmp` 等 sidecar 文件作为强制保留对象

后续待办：

- 评估并逐步扩展更多照片格式的元数据读写支持；重点关注 `png/heic/arw/cr2/nef/dng` 等当前仅支持扫描、暂不支持 EXIF 拍摄时间写入的格式
