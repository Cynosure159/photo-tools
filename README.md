# photo-tools

本项目是一个基于 Python + PyQt 的本地照片处理 GUI 工具。

当前阶段目标：

- 建立项目基础设施
- 统一 Python 运行环境
- 搭建 GUI 骨架并跑通基础交互

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

当前已完成阶段 2 GUI 骨架：

- 主窗口支持两个功能页签切换
- 时间修改页已具备输入区、参数区、预览表格、状态区和执行确认链路
- 原片筛选页已具备目录选择、删除策略、预览表格、状态区和高风险确认链路

当前预览与执行结果仍为骨架占位数据，真实扫描、匹配、写入和删除逻辑将在后续阶段实现。
