---
name: code-audit-system
description: CVE-oriented multi-agent code audit system. Use when user provides a git repository URL for vulnerability discovery with the goal of submitting CVEs. This skill orchestrates subagents to find exploitable vulnerabilities (RCE, SQLi, Auth Bypass, etc.), write weaponized POCs, and generate CVE-ready reports. ALWAYS use this skill when the user mentions code auditing, vulnerability hunting, CVE discovery, or provides a git URL for security review.
---

# Code Audit System - CVE Discovery Engine

**核心理念**: 只报告可实际利用的漏洞，目标是提交 CVE，而非让代码变得更安全。

**语言要求**: 所有报告、总结、用户交互输出必须使用**中文**。仅以下内容可保留英文：漏洞类型名称（RCE、SQLi 等）、CWE/CVE 编号、CVSS 向量字符串、代码片段、POC 脚本中的变量名和函数名。

本技能协调多代理系统发现可利用漏洞，唯一目标是提交 CVE。过滤理论性问题，仅关注具有完整利用链的漏洞。

## ⭐ CVE-Oriented Audit Principles

### 核心原则 (必须遵守)

1. **只报告可实际利用的漏洞**
   - ✅ 有明确用户输入入口 (Source)
   - ✅ 有完整调用链 (Source → Sink)
   - ✅ 无有效安全控制阻断
   - ✅ 可编写可执行 POC
   - ❌ 拒绝理论漏洞 (无输入入口)
   - ❌ 拒绝潜在漏洞 (需要不可能的条件)
   - ❌ 拒绝被安全控制完全阻断的漏洞

2. **CVE 提交标准**
   - 目标：CVSS ≥ 7.0 (High/Critical)
   - 必须有 POC 验证
   - 必须影响真实用户 (非本地/测试环境)
   - 必须有明确受影响版本

3. **深度优于广度**
   - 1 个可利用漏洞 > 10 个理论漏洞
   - 完整调用链追踪 > 表面扫描
   - 证据链支撑每个结论

### 漏洞判定标准

| 类型 | 报告？ | 说明 |
|------|--------|------|
| 可利用漏洞 | ✅ 报告 | 有入口 + 无阻断 + 可 POC |
| 理论漏洞 | ❌ 丢弃 | 无用户输入入口 |
| 潜在漏洞 | ❌ 丢弃 | 需要特殊/不可能的条件 |
| 被阻断漏洞 | ❌ 丢弃 | 有有效安全控制 |

---

## 审计模式

项目初始化完成后、开始漏洞发现前，**必须询问用户选择审计模式**:

> 请选择审计模式:
> 1. **标准模式** — 直接进行代码审计，适用于未知项目或首次审计
> 2. **专项审计模式** — 先通过 cve-search 查询产品的历史漏洞，分析攻击模式后拟合到当前代码，指导漏洞猎杀。适用于已知产品或有 CVE 历史的项目

| 模式 | 适用场景 | 额外步骤 | 优势 |
|------|----------|----------|------|
| **标准模式** | 首次审计、内部项目、无 CVE 历史 | 无 | 流程简洁，快速开始 |
| **专项审计模式** | 开源产品、有 CVE 历史、已知厂商 | Phase 2.0: CVE 情报收集 | 基于历史漏洞模式定向猎杀，发现率更高 |

**专项审计模式触发条件** (用户未明确选择时自动判断):
- 目标仓库属于知名开源组织 (apache, spring-projects, wordpress 等)
- 用户明确提到产品名称且可映射到 cve-search vendor/product
- 用户要求"深度审计"或"专项审计"
- 用户提到需要参考历史漏洞

---

## 何时使用此技能

- 用户提供 git 仓库 URL 用于 **CVE 发现**
- 用户请求 **可利用漏洞** 猎杀
- 用户想发现 **CVE 级别** 问题 (RCE、SQLi、认证绕过等)
- 用户需要已识别漏洞的 **武器化 POC** 代码
- 用户需要包含利用细节的 **CVE 就绪报告**
- 用户要求**专项审计** 或基于历史漏洞的定向分析

## 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                          主代理                                    │
│  - 编排工作流程                                                    │
│  - Phase 2A: 快速预扫描 + 立即派发子代理                           │
│  - Phase 2B: 深度侦察 (与子代理并行)                               │
│  - Phase 2C: 增量情报注入子代理                                    │
│  - 管理子代理工作区                                                │
│  - 汇总报告                                                       │
│  - 与用户交互                                                      │
└──────────────────────────────────────────────────────────────────┘
          │                           │
          │ Phase 2A: 立即派发         │ Phase 2B/2C: 深度侦察 + 情报注入
          │ (基于快速预扫描)           │ (与子代理并行, 持续更新)
          ▼                           ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  子代理 1         │   │   子代理 2        │   │  子代理 N         │
│  模块 A          │   │   模块 B          │   │  模块 N           │
│  漏洞扫描器       │   │   漏洞扫描器      │   │  漏洞扫描器        │
│                  │   │                  │   │                   │
│  DRAFT 背景启动   │   │  DRAFT 背景启动   │   │  DRAFT 背景启动    │
│  ↓               │   │  ↓               │   │  ↓                │
│  接收 FINAL 注入  │   │  接收 FINAL 注入  │   │  接收 FINAL 注入   │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

## 工作流程概览

1. **项目收集** - 用户提供 git URL
2. **CVE 情报收集** (专项审计模式) - 查询历史 CVE，分析攻击模式
3. **漏洞发现** - 快速预扫描后立即派发子代理，深度侦察与子代理审计并行
4. **环境部署** (可选) - Docker 搭建
5. **POC 编写** - 子代理编写利用脚本
6. **验证测试** (可选) - 在部署环境中测试 POC
7. **总结报告** - 主代理汇总所有发现

```
标准模式:  项目初始化 → 快速预扫描 → 子代理审计(并行) → POC → 验证 → 报告
                              ↘ MainAgent深度侦察(并行) ↗
专项审计:  项目初始化 → CVE情报收集 → 快速预扫描 → 子代理审计(并行) → POC → 验证 → 报告
                                          ↘ MainAgent深度侦察(并行) ↗
```

**并行模型**: 快速预扫描（2A）完成后立即派发子代理，MainAgent 随后在后台执行深度侦察（2B），侦察结果通过增量注入（2C）实时传递给子代理。总耗时由最长路径决定，而非各阶段累加。

---

## 步骤 1: 项目初始化

**⚠️ 重要**: 必须严格遵守标准目录结构。

当用户提供 git 仓库 URL 时:

1. 创建标准项目目录并克隆源码到 `source/` 子目录
2. 创建 `metadata.json` 记录项目元数据
3. 创建状态文件 (`state/audit-state.json`, `state/task-history.jsonl`) 支持断点续传
4. 检测是否存在历史审计日志，若有则进入增量审计模式

**详细步骤**: 参考 `references/phase1-project-init.md`
**目录标准**: 参考 `references/project-structure.md`
**状态格式**: 参考 `state/audit-state-schema.md`

---

## 步骤 2: CVE 发现 (核心流程)

主代理协调多个子代理并行审计，发现可利用漏洞。

### Phase 2.0: CVE 情报收集 (仅专项审计模式)

利用 `cve-search` MCP 工具收集目标产品的历史漏洞情报：厂商/产品识别 → CVE 数据收集 → 攻击模式分析 → 模式拟合与变体推测 → 情报报告生成与注入子代理。

**详细步骤**: 参考 `references/phase2-cve-intelligence.md`
**方法论**: 参考 `references/cve-intelligence-guide.md`

### Phase 2A: 快速预扫描与并行派发 (5 分钟内)

快速语言/框架识别、粗略模块划分、攻击面草图后，创建 DRAFT 文档并**立即并行派发所有无依赖子代理**。

### Phase 2B: MainAgent 深度侦察 (与子代理并行)

子代理审计的同时，MainAgent 执行代码知识图谱构建（codebase-memory MCP）、深度攻击面映射、精确模块依赖分析，完成后将文档升级为 FINAL。

### Phase 2C: 增量情报注入

将 Phase 2B 的发现写入子代理的 `background.md`（`## 🔄 深度侦察补充情报` 章节），子代理定期检查并调整审计重点。

**Phase 2A/2B/2C 详细步骤**: 参考 `references/parallel-audit-workflow.md`

### Phase 2.3: 子代理审计执行 (与 2B 并行)

子代理在 Phase 2A 派发后立即开始审计，与 MainAgent 深度侦察并行。

**工作区结构** (Phase 2A 已创建 DRAFT 版本):

```
workspace/
├── 00-work-background.md        # DRAFT → Phase 2B 升级为 FINAL
├── 01-module-map.md             # DRAFT → Phase 2B 升级为 FINAL
├── agent-<module-1>/
│   ├── background.md            # DRAFT → Phase 2C 升级为 FINAL
│   ├── skill.md                 # 审计指令 (Phase 2C 可追加)
│   ├── execution.log
│   └── report.md
└── agent-<module-N>/            # 每个模块独立工作区
```

**并行调度策略**:
- Phase 2A 完成后，所有无依赖模块立即并行派发
- MainAgent 深度侦察期间不阻塞子代理
- Phase 2C 增量注入时子代理无缝接收新情报

**子代理增量更新检查** ⭐:
1. Phase 0 完成后: 检查 `background.md` 是否从 DRAFT 更新为 FINAL
2. Phase 2 开始前: 再次检查是否有新内容
3. 发现 FINAL 版本时: 审阅 `## 🔄 深度侦察补充情报` 章节

**子代理指令要求**: 参考 `references/subagent-guide.md` 中的完整指令清单和图谱增强审计流程。

**MainAgent 创建子 Agent 背景文档**: 参考 `references/subagent-guide.md`
**子代理技能模板**: `templates/subagent-skill-template.md`
**背景文档模板**: `templates/subagent-background-template.md`

### Phase 2.4: CVE 就绪漏洞报告

每个子代理生成 **CVE 就绪报告**，包含:

| 字段 | 描述 |
|------|------|
| **漏洞类型** | RCE、SQLi、认证绕过、路径穿越等 |
| **可利用性** | ✅ 可利用 / ❌ 理论性 |
| **需要认证** | 不需要 / 低权限 / 高权限 |
| **漏洞位置** | 文件路径和行号 (如 `auth/login.py:45-52`) |
| **调用链** | 完整: `userInput() → process() → sink()` |
| **安全控制** | 存在什么控制、如何绕过 |
| **严重程度** | 严重/高危 (CVE 级别) / 中危 / 低危 |
| **CVSS 评分** | 基础分 0.0-10.0 (目标 ≥7.0) |
| **POC 可行性** | ✅ 可武器化 / ❌ 不可武器化 |
| **证据** | 带行号的代码片段 |

**CVE 提交标准**: CVSS ≥ 7.0，影响真实用户，有明确受影响版本，可用 POC 演示。

**使用**: `templates/vulnerability-report-template.md` 获取报告格式。

---

## 步骤 3: 环境部署 (可选)

询问用户是否在 Docker 环境中部署目标应用。如果确认：检查现有 Docker 配置或创建多阶段 Dockerfile + docker-compose.yml。

**Dockerfile 模板和详细步骤**: 参考 `references/phases-3to6.md`

---

## 步骤 4: 武器化 POC 编写

调度子代理为 CVE 级别漏洞编写 Python POC 脚本。要求: 自包含、可配置目标、默认武器化、有利用前/后证据。

**POC 结构和 CVE 提交包**: 参考 `references/phases-3to6.md`
**POC 模板**: `templates/poc-template.py`

---

## 步骤 5: 漏洞验证 (可选)

询问用户是否验证 POC。每验证一个漏洞**立即**写一份独立验证报告到 `reports/vulnerability-<id>-verification.md`。

**验证流程和报告格式**: 参考 `references/phases-3to6.md`
**验证报告模板**: `templates/per-vulnerability-verification-report-template.md`

---

## 步骤 6: CVE 提交报告

主代理汇总所有发现，生成 `reports/cve-submission-report.md`。总报告汇总所有单漏洞验证报告，必须包含 Executive Summary、CVE Candidates 表格、Detailed CVE Reports 和 Maximum Impact Exploit Chain 章节。

**完整报告格式和提交渠道**: 参考 `references/phases-3to6.md`
**总结报告模板**: `templates/summary-report-template.md`

---

## 子代理完成通知 (推送模型)

子代理完成后必须**主动通知**主代理，而非等待轮询：
```
子代理完成 → 返回报告 → 主代理接收 → 汇总 → 等待剩余代理 → 全部完成 → 用户总结
```

---

## ⏰ Auto-Reminder Mechanism

审计完成后，若用户未指示下一步，按 +1h/+2h/+3h 间隔提醒。最多 3 次。

**详细机制**: 参考 `references/operations.md`

---

## 错误处理

- **克隆失败**: 报告用户，跳过该仓库
- **子 Agent 超时**: 重试一次，然后标记为未完成
- **Docker 失败**: 回退到静态分析 + POC
- **POC 执行错误**: 记录输出，标记验证为失败
- **CVE 被拒**: 分析原因调整发现策略

## 输出交付

主要交付物: CVE 提交报告（CVE 级别漏洞 + 武器化 POC + CVSS 评分）、独立漏洞报告、POC 脚本、(可选) 验证结果、CVE 提交指南。

**详细运维机制**: 参考 `references/operations.md`

---

## 语言特定漏洞参考

审计特定编程语言时，查阅这些指南获取语言特定的漏洞模式：

| 语言 | 指南 | 内容 |
|------|------|------|
| Python | `references/python-guide.md` | SQL 注入、命令注入、路径遍历、反序列化、SSTI、XXE、SSRF 等 |
| PHP | `references/php-guide.md` | SQL 注入、命令注入、文件包含、XSS、反序列化、路径穿越、SSRF |
| Java | `references/java-guide.md` | SQL 注入、命令注入、XXE、反序列化、路径穿越、SSRF、SSTI、JNDI 注入 |
| Rust | `references/rust-guide.md` | Unsoundness、并发竞态、资源耗尽、整数与缓冲区、依赖供应链 |

子 Agent 在审计该语言代码时必须查阅相关语言指南。

---

## 相关模板和参考

### 模板
- `templates/vulnerability-report-template.md` - 漏洞报告格式
- `templates/per-vulnerability-verification-report-template.md` - 单漏洞验证报告格式
- `templates/summary-report-template.md` - 总结报告格式
- `templates/poc-template.py` - POC 脚本结构
- `templates/subagent-skill-template.md` - 子代理技能模板
- `templates/subagent-background-template.md` - 子代理背景文档模板
- `templates/work-background-template.md` - 工作背景模板
- `templates/module-info-template.md` - 模块信息模板
- `templates/cve-intelligence-report-template.md` - CVE 情报分析报告模板
- `templates/audit-log-template.md` - 长期审计日志模板

### 引用文档
- `references/project-structure.md` - 项目存储结构
- `references/module-detection.md` - 按项目类型的模块检测
- `references/phase1-project-init.md` - Phase 1 项目初始化详细步骤 + 长期审计机制
- `references/phase2-cve-intelligence.md` - Phase 2.0 CVE 情报收集详细步骤
- `references/parallel-audit-workflow.md` - Phase 2A/2B/2C 并行审计详细步骤
- `references/subagent-guide.md` - 子代理背景文档创建 + 图谱增强审计流程
- `references/phases-3to6.md` - Phase 3-6 详细操作步骤
- `references/operations.md` - Auto-reminder + 错误处理 + 输出交付
- `references/cve-intelligence-guide.md` - CVE 情报收集方法论
- `references/python-guide.md` - Python 漏洞模式 (Source → Sink)
- `references/php-guide.md` - PHP 漏洞模式 (Source → Sink)
- `references/java-guide.md` - Java 漏洞模式 (Source → Sink)
- `references/rust-guide.md` - Rust 漏洞模式
- `state/audit-state-schema.md` - 审计状态文件格式规范
- **codebase-memory MCP** - 代码知识图谱工具
