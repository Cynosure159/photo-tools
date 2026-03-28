# photo-tools

本项目是一个基于 Python + PyQt 的本地照片处理 GUI 工具。

当前阶段目标：

- 建立项目基础设施
- 统一 Python 运行环境
- 准备 GUI 启动骨架

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

当前仅完成阶段 1 基础设施骨架，业务功能尚未开始实现。
