# photo-tools

本项目是一个基于 Python + PyQt 的本地照片处理 GUI 工具。

当前阶段目标：

- 建立项目基础设施
- 统一 Python 运行环境
- 搭建 GUI 骨架并跑通基础交互
- 实现两个核心功能的真实扫描、预览与执行
- 准备跨平台构建与持续集成能力

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

本地构建应用：

```bash
python scripts/build_app.py
```

构建指定平台/架构的包：

```bash
python scripts/build_app.py --platform macos --arch arm64
python scripts/build_app.py --platform macos --arch x86_64
python scripts/build_app.py --platform windows --arch x86
```

约定：

- 每次修改 Python 代码后，都需要在项目 `.venv` 中执行一次 `ruff check .`
- 测试默认使用 `pytest`
- 应用构建默认使用 `PyInstaller`
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

持续集成与构建：

- GitHub Actions 将执行 `ruff check .`
- GitHub Actions 将执行 `pytest`
- GitHub Actions 将验证 `macOS arm64`、`macOS x86_64` 和 `Windows x64` 构建
- 本地默认按当前机器架构构建；你这台 macOS ARM 机器默认产出 `macOS arm64`
- 构建产物默认输出到 `dist/<platform>-<arch>/`，中间产物输出到 `build/<platform>-<arch>/`
- 应用包名固定为 `photo-tools.app` 或 `photo-tools.exe`，平台架构信息只保留在目录名和 CI artifact 名中

后续待办：

- 评估并逐步扩展更多照片格式的元数据读写支持；重点关注 `png/heic/arw/cr2/nef/dng` 等当前仅支持扫描、暂不支持 EXIF 拍摄时间写入的格式
