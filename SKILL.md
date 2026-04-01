---
name: code-audit-system
description: 基于 OpenClaw 的多 Agent 代码审计系统。支持两种调用方式：(1) 命令行 `/skill code-audit` 直接审计项目，(2) 飞书 Bot 交互完成自动化安全审计。使用场景：(1) 人工/AI 搜集 GitHub/Gitee 项目，(2) Qwen 代码审计生成漏洞报告，(3) Docker 隔离环境部署，(4) POC 脚本编写，(5) 漏洞验证，(6) 报告汇总推送。支持任务追踪和断点续传。
aliases: ["code-audit", "audit", "security-audit", "vuln-scan"]
keywords: ["code audit", "security", "vulnerability", "Qwen", "POC", "CVE"]
---

# Code Audit System Skill

## 🚀 快速开始

### 方式一：命令行直接审计（推荐）

在项目目录中运行：

```bash
# 基础审计
/skill code-audit

# 或指定项目路径
/skill code-audit /path/to/project

# 深度审计（包含完整调用链分析）
/skill code-audit -d

# 指定 Qwen 模型
/skill code-audit -m qwen3-coder-plus

# 自动确认所有提示（YOLO 模式）
/skill code-audit -y

# 完整选项
/skill code-audit -d -m qwen3-coder-plus -y /path/to/project
```

### 方式二：飞书 Bot 交互

```bash
# 添加审计项目
/audit add https://github.com/example/target.git

# 查看状态
/audit status <project_id>
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户 (飞书 Bot)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   OpenClaw Main Agent                           │
│  • 接收飞书命令                                                  │
│  • 协调子 Agent                                                  │
│  • 环境部署 (需确认)                                             │
│  • 汇总报告                                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│project-       │   │code-auditor     │   │poc-           │
│collector      │   │(Qwen)           │   │developer      │
│• GitHub 搜索   │   │• 代码审计        │   │• POC 编写     │
│• 项目克隆      │   │• 漏洞报告        │   │• Python 脚本  │
└───────────────┘   └─────────────────┘   └───────────────┘
                              ↓
                    ┌─────────────────┐
                    │vulnerability-   │
                    │verifier         │
                    │• POC 执行        │
                    │• 漏洞验证        │
                    └─────────────────┘
```

### 命令行脚本说明

**脚本位置**: `scripts/code-audit.sh`

**选项**:
| 选项 | 说明 | 示例 |
|------|------|------|
| `-h, --help` | 显示帮助 | `/skill code-audit -h` |
| `-q, --quick` | 快速审计（默认） | `/skill code-audit -q` |
| `-d, --deep` | 深度审计（调用链分析） | `/skill code-audit -d` |
| `-m, --model` | 指定 Qwen 模型 | `/skill code-audit -m qwen3-coder-plus` |
| `-y, --yolo` | 自动确认所有提示 | `/skill code-audit -y` |
| `-o, --output` | 指定报告输出目录 | `/skill code-audit -o /tmp/reports` |

**审计流程**:
```
1. 检查 Qwen CLI 安装和认证
2. 初始化审计环境
3. 克隆/复制项目源码
4. 调用 Qwen 进行代码审计
5. 生成审计报告 (reports/audit_report.md)
6. (可选) 创建 POC 脚本 (pocs/*.py)
```

---

### 飞书 Bot 方式

## 核心功能

### 命令行模式

| 功能 | 实现方式 | 确认要求 | 说明 |
|------|---------|---------|------|
| 项目准备 | `code-audit.sh` | 自动 | 克隆 Git 仓库或复制本地项目 |
| 漏洞审计 | Qwen CLI (`-m qwen3.5-plus`) | 可选 (-y) | 静态代码分析，生成审计报告 |
| POC 编写 | Qwen CLI | 可选 (-y) | 根据报告自动编写 Python POC |
| 任务追踪 | `task-tracker.py` | 自动 | 状态记录到 `state/task-state.json` |

### 飞书 Bot 模式

| 功能 | 负责 Agent | 确认要求 | 说明 |
|------|-----------|---------|------|
| 项目搜集 | project-collector | 自动 | 人工提交或 AI 搜索 GitHub |
| 漏洞审计 | code-auditor (Qwen) | 自动 | 使用 code-audit skill，-y 模式 |
| 环境部署 | main-agent | **需确认** | Docker 隔离部署 |
| POC 编写 | poc-developer (Qwen) | 自动 | 读取报告，编写 Python 脚本 |
| 漏洞验证 | vulnerability-verifier | **需确认** | Docker 沙箱执行 POC |
| 报告汇总 | main-agent | 自动 | 汇总所有报告，飞书推送 |

## 工作流程

### 命令行模式流程

```
1. 用户在项目目录运行 /skill code-audit
   ↓
2. code-audit.sh 检查 Qwen CLI 和认证
   ↓
3. 初始化审计环境 (code-audit-system/<project>/)
   ↓
4. 克隆/复制项目源码到 source/
   ↓
5. 调用 Qwen 进行代码审计 → 生成 reports/audit_report.md
   ↓
6. (可选) 创建 POC 脚本 → pocs/*.py
   ↓
7. 输出报告路径和 POC 目录
```

### 飞书 Bot 模式流程

```
1. 用户添加项目 / AI 搜集
   ↓
2. project-collector 克隆项目到 source/
   ↓
3. code-auditor (Qwen) 审计代码 → 生成 reports/audit_report.md
   ↓
4. 询问：是否部署 Docker 环境？
   ┌─ 是 → main-agent 部署 docker/
   └─ 否 → 跳过
   ↓
5. poc-developer (Qwen) 读取报告 → 编写 pocs/*.py
   ↓
6. 询问：是否验证漏洞？
   ┌─ 是 → vulnerability-verifier 执行 → 生成 reports/verify_report.md
   └─ 否 → 跳过
   ↓
7. main-agent 汇总报告 → 飞书推送
```

## 漏洞报告格式

审计报告必须包含：

```markdown
# 漏洞审计报告

## 项目信息
- 项目名称：xxx
- 审计时间：2026-03-09
- 审计工具：Qwen + code-audit skill

## 漏洞列表

### 漏洞 1: SQL 注入
- **类型**: SQL Injection
- **认证**: 需要/不需要
- **位置**: `src/user.php` line 30-35
- **触发过程**: 由 `login()` 函数接收用户输入，未经过滤直接拼接到 SQL 语句，导致 SQL 注入
- **修复建议**: 使用参数化查询

### 漏洞 2: RCE
- **类型**: Remote Code Execution
- **认证**: 需要
- **位置**: `admin/upload.php` line 45-60
- **触发过程**: ...
- **修复建议**: ...
```

## 验证报告格式

在审计报告基础上增加：

```markdown
### 漏洞 1: SQL 注入
- **验证状态**: ✅ 成功 / ❌ 失败
- **POC 路径**: `pocs/001_sql_injection.py`
- **执行结果**: 成功获取数据库版本 MySQL 5.7.32
```

## 目录结构

```
~/.openclaw/<workspace>/code-audit-system/
├── <项目名称 1>/
│   ├── source/          # 源码 (git clone)
│   ├── reports/         # 审计报告 + 验证报告
│   │   ├── audit_report.md
│   │   └── verify_report.md
│   ├── pocs/            # POC 脚本
│   │   ├── 001_sql_injection.py
│   │   └── 002_rce.py
│   └── docker/          # Docker 配置
│       ├── Dockerfile
│       └── docker-compose.yml
├── <项目名称 2>/
├── state/               # 任务状态追踪
│   ├── task-state.json
│   └── task-history.jsonl
└── scripts/
    └── task-tracker.py
```

## 飞书命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `/audit add` | 添加审计项目 | `/audit add https://github.com/xxx/xxx.git` |
| `/audit search` | AI 搜索项目 | `/audit search "SQL injection" --cve` |
| `/audit list` | 查看项目列表 | `/audit list` |
| `/audit status` | 查看项目状态 | `/audit status 1` |
| `/audit report` | 获取审计报告 | `/audit report 1` |
| `/audit deploy` | 部署环境 | `/audit deploy 1` |
| `/audit poc` | 编写 POC | `/audit poc 1` |
| `/audit verify` | 验证漏洞 | `/audit verify 1` |
| `/audit cancel` | 取消任务 | `/audit cancel <task_id>` |

## Agent 配置

### 命令行模式

| 组件 | 工具 | 模型 | 说明 |
|------|------|------|------|
| `code-audit.sh` | Qwen CLI | qwen3.5-plus (默认) | 主审计脚本 |
| `task-tracker.py` | Python | - | 任务状态追踪 |

### 飞书 Bot 模式

| Agent | 模式 | 工具 | 超时 | 确认 |
|-------|------|------|------|------|
| `project-collector` | run | agent-browser | 600s | 自动 |
| `code-auditor` | session | qwen-code | 3600s | 自动 (-y) |
| `main-agent` | session | docker-essentials | - | 环境部署需确认 |
| `poc-developer` | session | qwen-code | 1800s | 自动 (-y) |
| `vulnerability-verifier` | run | docker-sandbox | 1800s | **需确认** |

## 支持的漏洞类型

- SQL Injection (SQL 注入)
- XSS (跨站脚本)
- RCE (远程代码执行)
- File Upload Vulnerability (文件上传)
- SSRF (服务端请求伪造)
- XXE (XML 实体注入)
- Authentication/Authorization Bypass (认证/授权绕过)
- Path Traversal (路径遍历)
- Command Injection (命令注入)
- Deserialization Vulnerability (反序列化)
- Information Disclosure (信息泄露)

## 任务追踪

### 状态文件

```
code-audit-system/state/
├── task-state.json      # 当前状态快照
└── task-history.jsonl   # 事件历史 (JSONL)
```

### 追踪器命令

```bash
# 查看当前状态
python code-audit-system/scripts/task-tracker.py status

# 查看历史
python code-audit-system/scripts/task-tracker.py history [limit]

# 生成统计
python code-audit-system/scripts/task-tracker.py stats

# 恢复任务
python code-audit-system/scripts/task-tracker.py resume
```

## 环境部署注意事项

### ⚠️ Web 目录权限设置

PHP 项目需要 Web 用户 (www-data, UID 33) 对以下目录有**读写权限**：

| 目录 | 用途 | 必须可写 |
|------|------|---------|
| `.env` | 环境配置 | ✅ |
| `runtime/` | 日志、缓存 | ✅ |
| `app/install/` | 安装程序 | ✅ |
| `public/uploads/` | 上传文件 | ✅ |

**解决方案**: 在 `docker-compose.yml` 中添加：

```yaml
services:
  web:
    user: "33:33"
    command: >
      sh -c "chown -R 33:33 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads;
             chmod -R 775 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads;
             apache2-foreground"
```

详见 `references/docker-deploy.md` 完整指南。

---

## 安全说明

1. **沙箱执行**: 所有 POC 在 Docker 隔离环境中执行
2. **用户确认**: 环境部署和漏洞验证需用户确认
3. **权限控制**: 飞书用户权限验证
4. **操作日志**: 完整记录所有操作
5. **敏感信息**: 状态文件不包含密码、Token

## 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 使用指南 | `references/USAGE.md` | 完整使用流程 |
| 报告模板 | `references/report-template.md` | 审计 + 验证报告模板 |
| POC 模板 | `references/poc-template.py` | Python POC 脚本模板 |
| Docker 部署 | `references/docker-deploy.md` | Docker 环境部署指南 (**含权限设置**) |
| 故障排除 | `references/troubleshooting.md` | 常见问题解决方案 |
| 任务追踪 | `scripts/task-tracker.py` | 状态查询工具 |
| 命令行脚本 | `scripts/code-audit.sh` | 命令行审计入口 |

---

## 💡 使用示例

### 命令行模式

```bash
# 示例 1: 审计当前目录
cd /path/to/project
/skill code-audit

# 示例 2: 审计指定项目
/skill code-audit /path/to/vulnerable-app

# 示例 3: 深度审计（完整调用链分析）
/skill code-audit -d /path/to/project

# 示例 4: 使用更强的 Qwen 模型
/skill code-audit -m qwen3-coder-plus /path/to/project

# 示例 5: YOLO 模式（自动确认所有提示）
/skill code-audit -y -d /path/to/project

# 示例 6: 审计 Git 仓库
/skill code-audit https://github.com/OWASP/juice-shop.git
```

### 飞书 Bot 模式

```bash
# 添加审计项目
/audit add https://github.com/OWASP/juice-shop.git

# 查看项目列表
/audit list

# 查看项目状态
/audit status 1

# 获取审计报告
/audit report 1

# 手动触发 POC 编写
/audit poc 1

# 手动触发漏洞验证
/audit verify 1
```

---

## 版本

- **Skill 版本**: 3.1.0
- **最后更新**: 2026-03-31
- **新增功能**: 命令行 `/skill code-audit` 直接审计
