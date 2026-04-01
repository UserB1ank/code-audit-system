# 代码审计系统使用指南

## 快速开始

### 1. 添加审计项目

通过飞书发送：

```
/audit add https://github.com/OWASP/juice-shop.git
```

批量添加：

```
/audit add
https://github.com/xxx/xxx.git
https://github.com/yyy/yyy.git
```

### 2. AI 搜索项目

让 AI 搜索适合审计的 CVE 相关项目：

```
/audit search "SQL injection" --cve
/audit search "file upload bypass" --cve
```

### 3. 查看项目状态

```
/audit status 1
```

### 4. 系统自动执行

系统会自动创建以下子 Agent：

1. **project-collector** - 克隆项目到 `source/`
2. **code-auditor (Qwen)** - 代码审计，生成 `reports/audit_report.md`
3. **poc-developer (Qwen)** - 编写 POC 到 `pocs/`

### 5. 环境部署（可选）

系统会询问：

> 🐳 是否为项目部署 Docker 环境？

- 回复 **是**：使用 `docker-essentials` 部署 Docker 环境
- 回复 **否**：跳过此步骤

### 6. 漏洞验证（可选）

系统会询问：

> 🔍 是否需要验证发现的漏洞？

- 回复 **是**：在 Docker 沙箱中执行 POC，生成 `reports/verify_report.md`
- 回复 **否**：跳过验证

### 7. 获取报告

```
/audit report 1
```

## 完整工作流

```
┌──────────────────────────────────────────────────────────┐
│  1. 用户添加项目 / AI 搜索                                │
│     /audit add https://github.com/xxx/xxx.git           │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  2. project-collector (subagent)                        │
│     • 克隆项目到 source/                                 │
│     • 准备审计环境                                       │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  3. code-auditor (Qwen, subagent)                       │
│     • 使用 code-audit skill                              │
│     • 工作模式：无需确认 (-y)                            │
│     • 生成 reports/audit_report.md                       │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  4. 询问：是否部署 Docker 环境？                          │
│     用户确认 → main-agent 部署 docker/                   │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┘
│  5. poc-developer (Qwen, subagent)                      │
│     • 读取 audit_report.md                               │
│     • 编写 POC 脚本到 pocs/                               │
│     • 每个漏洞一个 Python 脚本                             │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  6. 询问：是否验证漏洞？                                  │
│     用户确认 → vulnerability-verifier 执行               │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  7. vulnerability-verifier                              │
│     • 在 Docker 沙箱中执行 POC                             │
│     • 生成 reports/verify_report.md                      │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┘
│  8. main-agent 汇总报告 → 飞书推送                        │
└──────────────────────────────────────────────────────────┘
```

## 飞书命令详解

### /audit add

添加审计项目。

**格式:**

```
/audit add <url>
/audit add <url1>
<url2>
<url3>
```

**示例:**

```
/audit add https://github.com/OWASP/juice-shop.git
```

### /audit search

AI 搜索 GitHub 上适合审计的项目。

**格式:**

```
/audit search <关键词> [--cve]
```

**示例:**

```
/audit search "SQL injection" --cve
/audit search "file upload" --cve
```

### /audit list

查看所有审计项目及其状态。

**输出:**

```
[1] https://github.com/xxx/xxx.git
    状态：auditing
    创建：2026-03-09 00:30:00
    
[2] https://github.com/yyy/yyy.git
    状态：completed
    创建：2026-03-08 15:20:00
```

### /audit status

查看项目详细状态。

**格式:**

```
/audit status <project_id>
```

**输出:**

```
📊 项目状态 [1]

URL: https://github.com/xxx/xxx.git
状态：poc_developing
进度：75%

当前步骤：POC 编写
已发现漏洞：5 个
已编写 POC: 3 个
```

### /audit report

获取审计报告。

**格式:**

```
/audit report <project_id>
```

**输出:**

```markdown
# 漏洞审计报告

## 项目信息
- 项目名称：xxx
- 审计时间：2026-03-09
- 审计工具：Qwen + code-audit skill

## 漏洞列表

### 漏洞 1: SQL 注入
- 类型：SQL Injection
- 认证：否
- 位置：src/user.php line 30-35
- 触发过程：login() 函数...
```

### /audit deploy

手动触发环境部署。

**格式:**

```
/audit deploy <project_id>
```

### /audit poc

手动触发 POC 编写。

**格式:**

```
/audit poc <project_id>
```

### /audit verify

手动触发漏洞验证。

**格式:**

```
/audit verify <project_id>
```

## 报告格式

### 审计报告

必须包含以下内容：

- **漏洞类型**: SQL 注入/XSS/RCE 等
- **认证要求**: 是否需要认证
- **漏洞位置**: 文件 + 行号 (如 `src/user.php line 30-35`)
- **触发过程描述**: 由 xxx 函数引起，xxx 处理后，形成了 xxx，最终导致了 xxx 漏洞
- **修复建议**: 具体的修复方案

### 验证报告

在审计报告基础上增加：

- **验证状态**: ✅成功 / ❌失败
- **POC 具体路径**: `pocs/001_sql_injection.py`
- **执行结果**: 实际执行输出

## 安全说明

1. **沙箱执行**: 所有 POC 在 Docker 隔离环境中执行
2. **用户确认**: 环境部署和漏洞验证需用户确认
3. **权限控制**: 飞书用户权限验证
4. **操作日志**: 完整记录所有操作

## 常见问题

### Q: 项目克隆失败？

A: 检查 GitHub 地址是否正确，是否需要认证。

### Q: 审计时间过长？

A: 大型项目可能需要较长时间，使用 `/audit status` 查看进度。

### Q: POC 执行失败？

A: 检查 Docker 环境是否正常，项目依赖是否安装完整。

### Q: 如何取消审计？

A: 使用 `/audit cancel <project_id>` 取消任务。

## 配置目录

```
~/.openclaw/<workspace>/code-audit-system/
├── <项目名称>/
│   ├── source/          # 源码
│   ├── reports/         # 报告
│   ├── pocs/            # POC 脚本
│   └── docker/          # Docker 配置
├── state/               # 任务状态
└── scripts/             # 工具脚本
```
