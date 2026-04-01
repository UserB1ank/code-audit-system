# Code Audit System - 命令行工具

## 🚀 快速开始

### 前置要求

1. **安装 Qwen Code CLI**
```bash
npm install -g @qwen-code/qwen-code@latest
```

2. **认证 Qwen**
```bash
qwen auth login
# 或设置 API Key
export DASHSCOPE_API_KEY="sk-xxx"
```

3. **验证安装**
```bash
qwen --version
qwen auth status
```

---

## 📖 使用方法

### 基础审计

在项目目录中运行：

```bash
# 方式 1: 使用 OpenClaw 技能命令
/skill code-audit

# 方式 2: 直接运行脚本
bash ~/.openclaw/workspace-cybersecurity_expert/skills/code-audit-system/scripts/code-audit.sh
```

### 指定项目路径

```bash
# 审计本地目录
/skill code-audit /path/to/project

# 审计 Git 仓库
/skill code-audit https://github.com/OWASP/juice-shop.git
```

### 高级选项

```bash
# 深度审计（包含完整调用链分析）
/skill code-audit -d

# 使用更强的 Qwen 模型
/skill code-audit -m qwen3-coder-plus

# YOLO 模式（自动确认所有提示）
/skill code-audit -y

# 组合使用
/skill code-audit -d -m qwen3-coder-plus -y /path/to/project
```

---

## 📋 命令选项

| 选项 | 全称 | 说明 | 默认值 |
|------|------|------|--------|
| `-h` | `--help` | 显示帮助信息 | - |
| `-v` | `--version` | 显示版本号 | - |
| `-q` | `--quick` | 快速审计（静态分析） | 是 |
| `-d` | `--deep` | 深度审计（调用链分析） | 否 |
| `-m` | `--model` | 指定 Qwen 模型 | qwen3.5-plus |
| `-y` | `--yolo` | 自动确认所有提示 | 否 |
| `-o` | `--output` | 指定报告输出目录 | 默认工作区 |

### 支持的 Qwen 模型

| 模型 | 适用场景 |
|------|---------|
| `qwen3.5-plus` | 通用审计（推荐） |
| `qwen3-coder-plus` | 复杂代码分析 |
| `qwen3-coder-next` | 轻量级快速审计 |
| `qwen3-max` | 最强模型（耗时较长） |

---

## 📁 输出结构

审计完成后，会在工作区生成以下目录结构：

```
~/.openclaw/workspace-cybersecurity_expert/code-audit-system/<project_name>/
├── source/          # 项目源码（克隆或复制）
├── reports/         # 审计报告
│   └── audit_report.md
├── pocs/            # POC 脚本
│   ├── 001_sql_injection.py
│   ├── 002_rce.py
│   └── ...
└── state/           # 任务状态（全局）
    ├── task-state.json
    └── task-history.jsonl
```

---

## 📊 审计报告格式

审计报告 (`reports/audit_report.md`) 包含：

```markdown
# 漏洞审计报告

## 项目信息
- 项目名称：xxx
- 审计时间：2026-03-31
- 审计模型：qwen3.5-plus

## 漏洞列表

### 漏洞 1: SQL 注入
- **类型**: SQL Injection
- **认证**: 不需要
- **位置**: `src/user.php` line 30-35
- **触发过程**: 由 `login()` 函数接收用户输入，未经过滤直接拼接到 SQL 语句
- **CVSS**: 9.8 (Critical)
- **修复建议**: 使用参数化查询

### 漏洞 2: RCE
...
```

---

## 🐍 POC 脚本

每个可利用的漏洞会生成独立的 Python POC 脚本：

```python
#!/usr/bin/env python3
"""
POC for SQL Injection in src/user.php
CVE: CVE-2026-XXXXX
"""

import requests

TARGET = "http://target.com"

def exploit():
    # POC implementation
    pass

if __name__ == "__main__":
    exploit()
```

---

## 🔍 任务追踪

### 查看当前状态

```bash
python ~/.openclaw/workspace-cybersecurity_expert/skills/code-audit-system/scripts/task-tracker.py status
```

### 查看历史

```bash
python ~/.openclaw/workspace-cybersecurity_expert/skills/code-audit-system/scripts/task-tracker.py history 10
```

### 生成统计

```bash
python ~/.openclaw/workspace-cybersecurity_expert/skills/code-audit-system/scripts/task-tracker.py stats
```

---

## ⚠️ 注意事项

### 安全提示

1. **沙箱执行**: 所有 POC 脚本应在 Docker 沙箱中执行
2. **授权测试**: 仅对授权的项目进行审计和验证
3. **敏感信息**: 不要将审计报告和 POC 泄露给未授权方

### 性能优化

1. **大型项目**: 使用 `-q` 快速审计模式
2. **深度分析**: 使用 `-d` 模式时预留足够时间
3. **并行审计**: 可对多个项目并行运行审计

### 故障排除

**问题**: `qwen: command not found`
```bash
npm install -g @qwen-code/qwen-code@latest
```

**问题**: `Authentication required`
```bash
qwen auth login
# 或
export DASHSCOPE_API_KEY="sk-xxx"
```

**问题**: 审计时间过长
- 检查项目大小，考虑使用快速模式
- 使用更强的模型可能更快（如 qwen3-max）
- 检查网络连接

---

## 📚 相关文档

- [SKILL.md](../SKILL.md) - 技能完整文档
- [USAGE.md](../reference/USAGE.md) - 飞书 Bot 使用指南
- [report-template.md](../reference/report-template.md) - 报告模板
- [poc-template.py](../reference/poc-template.py) - POC 模板
- [docker-deploy.md](../reference/docker-deploy.md) - Docker 部署指南

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-03-31 | 初始版本，命令行审计入口 |

---

**最后更新**: 2026-03-31
