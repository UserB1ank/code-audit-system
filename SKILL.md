---
name: code-audit-system
description: CVE-oriented multi-agent code audit system. Use when user provides a git repository URL for vulnerability discovery with the goal of submitting CVEs. This skill orchestrates subagents to find exploitable vulnerabilities (RCE, SQLi, Auth Bypass, etc.), write weaponized POCs, and generate CVE-ready reports. ALWAYS use this skill when the user mentions code auditing, vulnerability hunting, CVE discovery, or provides a git URL for security review.
---

# Code Audit System - CVE Discovery Engine

**核心理念**: 只报告可实际利用的漏洞，目标是提交 CVE，而非让代码变得更安全。

This skill orchestrates a multi-agent system to discover exploitable vulnerabilities with the sole purpose of CVE submission. It filters out theoretical issues and focuses only on vulnerabilities with complete exploit chains.

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

## When to Use This Skill

- User provides a git repository URL for **CVE discovery**
- User requests **exploitable vulnerability** hunting
- User wants to find **CVE-worthy** issues (RCE, SQLi, Auth Bypass, etc.)
- User needs **weaponized POC** code for identified vulnerabilities
- User wants **CVE-ready reports** with exploitation details

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Agent                                │
│  - Orchestrates workflow                                         │
│  - Manages subagent workspaces                                   │
│  - Coordinates module detection                                  │
│  - Aggregates reports                                            │
│  - Interfaces with user                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  SubAgent 1   │   │   SubAgent 2    │   │  SubAgent N   │
│  Module A     │   │   Module B      │   │  Module N     │
│  Vulnerability│   │   Vulnerability │   │  Vulnerability│
│  Scanner      │   │   Scanner       │   │  Scanner      │
└───────────────┘   └─────────────────┘   └───────────────┘
```

## Workflow Overview

1. **Project Collection** - User provides git URLs
2. **Vulnerability Discovery** - SubAgents audit code modules
3. **Environment Deployment** (optional) - Docker setup
4. **POC Writing** - SubAgents write exploit scripts
5. **Verification** (optional) - Test POCs against deployed environment
6. **Summary Report** - MainAgent aggregates all findings

## Step-by-Step Instructions

### Step 1: Project Initialization (强制标准目录结构)

**⚠️ 重要**: 必须严格遵守标准目录结构，参考 `references/project-structure.md`

When the user provides a git repository URL:

1. **创建标准项目目录**:
   ```bash
   mkdir -p code-audit-projects/<project-name>/{source,state,workspace,pocs,reports,docker}
   ```

2. **克隆源代码到 source/** (必须):
   ```bash
   cd code-audit-projects/<project-name>/
   git clone <git-url> source/
   ```
   
   **❌ 错误**: `git clone <url> .` (直接克隆到根目录)  
   **✅ 正确**: `git clone <url> source/` (克隆到 source/ 子目录)

3. **创建 metadata.json**:
   ```json
   {
     "project_name": "<project-name>",
     "git_url": "<repo-url>",
     "clone_date": "2026-04-02T10:30:00Z",
     "commit_hash": "<git rev-parse HEAD>",
     "language": ["Java", "Python", "Rust", ...],
     "framework": ["Spring", "Django", ...],
     "app_type": "web-application|system-service|gui|mobile",
     "modules": [],
     "vulnerabilities_found": 0,
     "pocs_written": 0
   }
   ```

4. **创建技术背景文档** (MainAgent 负责):
   - `workspace/00-work-background.md` - 技术栈、攻击面、CVE 发现策略
   - `workspace/01-module-map.md` - 模块划分、文件映射

5. **创建状态文件** (必须，支持断点续传):
   - `state/audit-state.json` - 审计状态追踪 ⭐
   - `state/task-history.jsonl` - 事件历史日志 ⭐

**状态文件作用**:
- ✅ 记录审计进度 (阶段、子 Agent 状态、漏洞发现)
- ✅ 支持断点续传 (崩溃/暂停后恢复)
- ✅ 定期保存检查点 (`state/checkpoint-<timestamp>.json`)
- ✅ 实时日志追加 (`task-history.jsonl`)

**暂停/恢复流程**:
```bash
# 暂停时保存检查点
cp state/audit-state.json state/checkpoint-$(date +%Y%m%d-%H%M%S).json

# 恢复时加载最近检查点
cp state/checkpoint-<latest>.json state/audit-state.json

# 分析未完成的子 Agent
cat state/audit-state.json | jq '.subagents[] | select(.status == "running")'

# 重启未完成的子 Agent，继续审计
```

**Read**: `state/audit-state-schema.md` for complete state file format.

**完整目录结构**:
```
code-audit-projects/<project-name>/
├── source/              # ✅ 源代码 (git clone 必须到此)
├── state/               # ✅ 状态追踪
│   ├── audit-state.json
│   └── task-history.jsonl
├── workspace/           # ✅ CVE Hunter 工作区
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   └── agent-<module>/
│       ├── skill.md
│       └── report.md
├── pocs/                # ✅ POC 脚本 (CVE 验证后)
├── reports/             # ✅ CVE 报告 (最终输出)
└── metadata.json        # ✅ 项目元数据
```

**Read**: `references/project-structure.md` for complete directory standards.

### Step 2: CVE Discovery (Main Process)

This is the core vulnerability hunting phase. The MainAgent coordinates multiple SubAgents.

#### Phase 2.1: Technology Reconnaissance

Analyze the project for CVE discovery:

1. **Identify programming languages** - Scan file extensions, package files
2. **Detect frameworks and components** - Check package.json, requirements.txt, pom.xml, etc.
3. **Determine application type** - Web app, system service, GUI, mobile, etc.
4. **Map attack surface** - User input points, auth mechanisms, file operations, network interfaces

Create a **Work Background** document at `workspace/00-work-background.md` containing:
- Technology stack summary
- Application type classification
- **Attack surface map** (entry points, trust boundaries)
- **High-risk areas** (auth, file ops, serialization, command execution)

**Use**: `references/module-detection.md` for module structure templates by project type.

#### Phase 2.2: Module Partitioning

Partition the codebase into logical modules for parallel auditing:

1. Identify module boundaries from directory structure
2. Map files to each module
3. Identify inter-module dependencies
4. Create module dependency graph

Store module mapping at `workspace/01-module-map.md`.

#### Phase 2.3: SubAgent Dispatch (CVE Hunters)

**⚠️ 目录结构要求**: 必须使用标准工作区布局

**MainAgent 必须为每个子 Agent 创建独立背景文档**

For each module, create a dedicated SubAgent workspace:

```
workspace/
├── 00-work-background.md        # ✅ MainAgent 创建 (全局技术侦察)
├── 01-module-map.md             # ✅ MainAgent 创建 (模块划分)
├── agent-<module-1>/            # ✅ 子 Agent 1 工作区
│   ├── background.md            # MainAgent 创建 (独立背景文档) ⭐
│   ├── skill.md                 # MainAgent 创建 (审计指令)
│   ├── execution.log          # ⭐ 子 Agent 执行日志 (自动保存)
│   └── report.md                # 子 Agent 输出 (CVE 报告)
├── agent-<module-2>/            # ✅ 子 Agent 2 工作区
│   ├── background.md            # ⭐ 新增
│   ├── execution.log          # ⭐ 新增
│   └── report.md
└── agent-<module-N>/            # ✅ 子 Agent N 工作区
    ├── background.md            # ⭐ 新增
    ├── execution.log          # ⭐ 新增
    └── report.md
```

**Dispatch Strategy**:
- If modules have NO dependencies on each other → dispatch in parallel using thread pool
- If modules have dependencies → dispatch in dependency order

**Read**: 
- `templates/subagent-skill-template.md` for creating SubAgent skills
- `templates/subagent-background-template.md` for creating background documents ⭐

---

### MainAgent 创建子 Agent 背景文档 (必须)

**每个子 Agent 启动前**, MainAgent 必须创建 `workspace/agent-<module>/background.md`，包含：

#### 1. 模块涉及文件列表

```markdown
## 涉及文件

**核心文件** (重点审计):
1. `File1.java` (行数：XXX) - 功能描述 - CVE 潜力 🔴
2. `File2.java` (行数：XXX) - 功能描述 - CVE 潜力 🔴

**辅助文件**:
- `File3.java` - 辅助功能
- ...
```

#### 2. 可能存在的漏洞类型

```markdown
## 高价值目标 (P0)

| 漏洞类型 | CVSS 潜力 | 存在可能性 | 审计优先级 |
|----------|-----------|------------|------------|
| RCE | 9.0-10.0 | 高 | 🔴 立即 |
| Auth Bypass | 8.0-10.0 | 中 | 🔴 立即 |

## 中等价值目标 (P1)
...
```

#### 3. 审计流程与思路

```markdown
## 审计流程

### Phase 1: 代码地图绘制 (10 分钟)
- 列出所有源文件及其行数
- 识别入口点 (public 方法、REST 端点)
- 识别危险 Sink (SQL、文件操作、命令执行)

### Phase 2: 数据流追踪 (25-35 分钟)
- 从 Source 逐层向下追踪到 Sink
- 记录每层函数的文件名和行号
- 标注每层的处理逻辑 (验证、过滤、转换)

### Phase 3: 安全控制分析 (10 分钟)
- 识别全局策略限制
- 分析绕过可能性

### Phase 4: CVE 发现与报告 (10-15 分钟)
- 验证可利用性
- 计算 CVSS 评分
```

#### 4. 调用流追踪指南

```markdown
## 调用流追踪

**Source (用户输入)**:
- `XXX.java:10` - `@RequestParam("query") String query`

**Process (处理层)**:
- `XXX.java:25` - `buildQuery(query)` - 字符串拼接
- `XXX.java:40` - `validateInput(query)` - 仅检查 null

**Sink (危险操作)**:
- `XXX.java:55` - `queryManager.createQuery(query, Query.SQL)`

**完整调用链**:
userInput → buildQuery → validateInput (不足) → createQuery → CVE
```

#### 5. 输入输出流追踪

```markdown
## 输入输出流

**输入流**:
- HTTP 请求 → REST 端点 → Service 层 → DAO 层 → JCR 查询
- 文件上传 → 验证 (不足) → 存储 → 执行

**输出流**:
- JCR 查询结果 → Service 层 → REST 响应 → 攻击者
- 文件内容 → InputStream → OutputStream → 攻击者
```

#### 6. 全局策略限制分析

```markdown
## 全局策略

**现有控制**:
- WCMCoreUtils.getUserSessionProvider() - 获取用户会话
- ACL 权限检查 - 理论上限制节点访问

**绕过方法**:
- 使用 `getSystemSessionProvider()` 替代 → 完全绕过 ACL
- 代码中多处使用系统会话 (见 `BaseConnector.java:306`)
```

#### 7. 绕过可能性分析

```markdown
## 绕过分析

**安全控制 vs 绕过方法**:

| 安全控制 | 绕过方法 | 可利用性 |
|----------|----------|----------|
| ACL 权限检查 | getSystemSessionProvider() | ✅ 高 |
| 路径验证 | URL 编码绕过 (%2e%2e%2f) | ✅ 中 |
| null 检查 | 发送非 null 恶意值 | ✅ 高 |
```

---

**SubAgent Instructions Must Include**:
- **目标源代码路径** (绝对路径): `<project-root>/source/<module>/`
- **报告输出位置** (绝对路径): `<project-root>/workspace/agent-<module>/report.md`
- **背景文档位置** (必须阅读): `<project-root>/workspace/agent-<module>/background.md`
- Focus on exploitable vulnerabilities only
- Trace complete call chains (Source → Sink)
- Document security controls and bypass methods
- Filter out theoretical issues

#### Phase 2.4: CVE-Ready Vulnerability Report

Each SubAgent must produce a **CVE-ready report** covering:

| Field | Description |
|-------|-------------|
| **Vulnerability Type** | RCE, SQLi, Auth Bypass, Path Traversal, etc. |
| **Exploitability** | ✅ Exploitable / ❌ Theoretical |
| **Authentication Required** | None / Low-Priv / High-Priv |
| **Location** | File path and line numbers (e.g., `auth/login.py:45-52`) |
| **Call Chain** | Complete: `userInput() → process() → sink()` |
| **Security Controls** | What exists, how to bypass |
| **Severity** | Critical/High (CVE-worthy) / Medium / Low |
| **CVSS Score** | Base score 0.0-10.0 (aim for ≥7.0) |
| **POC Feasibility** | ✅ Can weaponize / ❌ Cannot weaponize |
| **Evidence** | Code snippets with line numbers |

**Use**: `templates/vulnerability-report-template.md` for report format.

**CVE Submission Criteria**:
- CVSS ≥ 7.0 (High/Critical)
- Affects real users (not local/test only)
- Has clear affected versions
- Can be demonstrated with POC

### Step 3: Environment Deployment (Optional - Ask User)

Before proceeding, ask the user:
> "Do you want to deploy the target application in a Docker environment for vulnerability verification? This allows testing POCs in an isolated environment."

If user confirms:

1. **Check for existing Docker config** - Look for Dockerfile, docker-compose.yml in the source repository
2. **Create Docker environment** if none exists:
   - Analyze application dependencies (package files, build tool, runtime requirements)
   - Write appropriate `Dockerfile`
   - Create `docker-compose.yml` with service dependencies (MySQL, PostgreSQL, Neo4j, etc.)

3. **Write Docker files**:
   - For a typical web application, create a multi-stage Dockerfile with build and runtime stages
   - Use `docker-compose.yml` to define the application service plus database/dependency services
   - Store Docker configs at `docker/` directory in the project

4. **Example Dockerfile template**:
   ```dockerfile
   # Build stage
   FROM maven:3.9-eclipse-temurin-21 AS builder
   WORKDIR /app
   COPY pom.xml .
   RUN mvn dependency:go-offline
   COPY src ./src
   RUN mvn package -DskipTests

   # Runtime stage
   FROM eclipse-temurin:21-jre
   WORKDIR /app
   COPY --from=builder /app/target/*.jar app.jar
   EXPOSE 8080
   ENTRYPOINT ["java", "-jar", "app.jar"]
   ```

5. **Example docker-compose.yml template**:
   ```yaml
   version: '3.8'
   services:
     app:
       build: .
       ports:
         - "8080:8080"
       environment:
         - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/appdb
         - SPRING_DATASOURCE_USERNAME=appuser
         - SPRING_DATASOURCE_PASSWORD=apppass
       depends_on:
         db:
           condition: service_healthy
     db:
       image: postgres:16
       environment:
         POSTGRES_DB: appdb
         POSTGRES_USER: appuser
         POSTGRES_PASSWORD: apppass
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U appuser"]
         interval: 5s
         timeout: 5s
         retries: 5
   ```

6. **Start the environment**:
   ```bash
   docker-compose up -d
   ```

**Note**: If the target application has special requirements (e.g., specific middleware, caching layers, or complex networking), adapt the Docker configuration accordingly.

### Step 4: Weaponized POC Writing

Dispatch SubAgents to write **weaponized** proof-of-concept exploits for CVE submission:

1. **Read vulnerability reports** from Step 2 (CVE-worthy only)
2. **Create POC directory**: `<project-root>/pocs/`
3. **For each CVE-worthy vulnerability**, create a Python script:
   - `poc-001-rce-auth-bypass.py`
   - `poc-002-sqli-admin-takeover.py`
   - `poc-003-path-traversal-rce.py`

**POC Requirements (CVE Submission Standard)**:
- Self-contained Python script (no external dependencies beyond requests)
- Clear usage instructions with example command
- Configurable target URL/host/port
- **Weaponized by default** (demonstrates full impact)
- Safe execution (no permanent damage, but proves exploit)
- **Before/After evidence** (e.g., `whoami` output, file created, data extracted)
- CVSS scoring justification in comments

**POC Structure**:
```python
#!/usr/bin/env python3
"""
CVE-XXXX-XXXXX: [Vulnerability Name]
Target: [Product] [Affected Versions]
Author: [Your Name]
CVSS: [Score] [Vector]

Usage: python3 poc.py -t http://target:port

Proof of Concept:
- Before: [normal state]
- Exploit: [action]
- After: [compromised state]
"""
```

**Read**: `templates/poc-template.py` for POC structure.

**CVE Submission Package**:
For each CVE-worthy vulnerability, prepare:
1. POC script (weaponized)
2. Video demonstration (optional but recommended)
3. Technical writeup (impact, affected versions, mitigation)
4. CVSS v3.1 scoring

### Step 5: Vulnerability Verification (Optional - Ask User)

Ask the user:
> "Do you want to verify the POCs against the deployed environment? This will test if each exploit works and produce a verification report."

If user confirms:

1. **Deploy target** (not done in Step 3)
2. **Run each POC** against the deployed Docker environment
3. **Record results**:
   - Success/Failure
   - Output/evidence
   - Time to exploit

4. **Create verification report**: `reports/verification-report.md`

Verification report extends vulnerability report with:
- Verification status: "成功" (Success) / "失败" (Failure)
- POC path: Full path to POC script
- Execution output: Terminal output from POC run
- Evidence: Screenshots, response data, etc.

### Step 6: CVE Submission Report

MainAgent aggregates all findings into a **CVE-ready submission package**:

1. **Collect all reports**:
   - Individual vulnerability reports from SubAgents (CVE-worthy only)
   - Weaponized POC scripts
   - POC verification results (if verified)

2. **Generate CVE Submission Report** at `reports/cve-submission-report.md`:

```markdown
# CVE Submission Report

## Project Overview
- **Product**: [Product Name]
- **Repository**: <git-url>
- **Vendor**: [Vendor Name]
- **Audit Date**: <date>
- **Auditor**: [Your Name/Handle]

## Executive Summary (CVE Focus)
- **CVE-Worthy Vulnerabilities**: <count> (CVSS ≥ 7.0)
- **Critical (CVSS 9.0-10.0)**: <count>
- **High (CVSS 7.0-8.9)**: <count>
- **Total POCs Weaponized**: <count>

## CVE Candidates

| ID | Type | CVSS | Affected Versions | POC | Status |
|----|------|------|-------------------|-----|--------|
| CVE-XXXX-XXXXX | RCE | 9.8 | v1.0-v2.3 | ✅ | Ready to submit |
| CVE-XXXX-XXXXX | Auth Bypass | 8.5 | v1.5-v2.3 | ✅ | Ready to submit |

## Detailed CVE Reports

### CVE-XXXX-XXXXX: [Vulnerability Name]

**Severity**: Critical (CVSS 9.8)  
**Vector**: AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H  
**Affected Versions**: v1.0 - v2.3  
**Fixed Versions**: [If known]  

**Technical Details**:
- **Location**: `file.py:line`
- **Root Cause**: [Brief description]
- **Attack Vector**: [How attacker exploits]
- **Impact**: [What attacker achieves]

**Call Chain**:
```
userInput() → vulnerable_function() → sink()
```

**POC**: `pocs/poc-001-rce.py`

**Verification**: ✅ Successful (see verification report)

**Mitigation**: [Vendor remediation steps]

## Submission Checklist

For each CVE:
- [ ] Technical writeup complete
- [ ] POC weaponized and tested
- [ ] CVSS v3.1 scoring calculated
- [ ] Affected versions confirmed
- [ ] Vendor contact info (if coordinated disclosure)
- [ ] Video demonstration (optional)

## Appendix
- Full reports: `reports/vulnerability-*.md`
- Weaponized POCs: `pocs/`
- Verification: `reports/verification-report.md`
- Call graphs: `reports/call-graphs/` (if available)
```

3. **CVE Submission Targets**:
   - **MITRE**: Primary CVE CNA
   - **GitHub Security Advisories**: For open source projects
   - **Vendor PSIRT**: For coordinated disclosure
   - **NVD**: After CVE assignment

4. **Store structured data**:
   - Vulnerability metadata (for tracking)
   - POC metadata (version, target, impact)
   - Verification results (success/failure, evidence)

## Data Storage

### MySQL Schema (Structured Data)

Tables needed:
- `vulnerabilities` - Core vulnerability records
- `pocs` - POC script metadata
- `verifications` - Verification results
- `projects` - Project metadata

### Neo4j Schema (Relationship Data)

Model call chains as:
```
(Node:Function {name: "userInput", output: "string"})
  -[:CALLS]->
(Node:Function {name: "sanitize", output: "string"})
  -[:CALLS]->
(Node:Function {name: "executeQuery", output: "result"})
```

Each entity has:
- Properties for input parameters
- Output as property or edge label
- Source location (file:line)

## SubAgent Workspace Creation

For each SubAgent, create a dedicated workspace with:

1. **skill.md** - Module-specific audit instructions
2. **work-background.md** - Technology context
3. **module-info.md** - File list, responsibilities, interfaces
4. **report.md** - Output template

Use the `superpowers:dispatching-parallel-agents` skill when modules are independent.

## SubAgent Completion Notification (Push Model)

**Important**: SubAgents must **actively notify** the MainAgent upon completion, not wait for polling.

**Push Mechanism**:
- When a SubAgent completes its audit, it sends its report back to the MainAgent immediately
- MainAgent aggregates reports as they arrive (real-time)
- After all SubAgents complete, MainAgent sends consolidated summary to user

**Benefits**:
- User receives timely updates without waiting for all agents
- MainAgent can track progress in real-time
- Failed agents are detected quickly

**Implementation**:
```
SubAgent completes → Returns report → MainAgent receives → Aggregates → Waits for remaining
                                                              ↓
                                                    All complete → User summary
```

---

## ⏰ Auto-Reminder Mechanism (自动提醒机制)

**触发条件**: 审计完成后，用户未指示下一步操作

### Reminder Schedule

| 时间点 | 行为 |
|--------|------|
| 完成时 | 显示审计结果 + 下一步建议选项 |
| +1 小时 | 询问是否需要继续 (POC 开发/CVE 提交) |
| +2 小时 | 再次提醒 + 强调 Critical 漏洞风险 |
| +3 小时 | 最后提醒 + 建议暂停/归档项目 |

### Reminder Message Template

```markdown
🔒 **PHPok 代码审计 - 等待指示**

**审计完成时间**: {completion_time}
**发现漏洞**: {total_vulns} 个 (Critical: {critical_count})

📋 待执行操作:
1. 生成综合 CVE 提交报告 📄
2. 开发 Top 5 POC 验证脚本 🔧
3. 联系 PHPok 官方 (admin@phpok.com) 📧
4. 提交 CVE 编号 (MITRE/CNVD) 🏷️

需要我执行哪项操作？
```

### Implementation

**主 Agent 职责**:
1. 审计完成后记录完成时间到 `state/audit-state.json`
2. 设置提醒标记 `reminder_pending: true`
3. 每次用户消息到达时检查是否超过 1 小时
4. 如超时而用户无新指令，发送提醒消息

**状态追踪**:
```json
{
  "reminder": {
    "enabled": true,
    "interval_hours": 1,
    "max_reminders": 3,
    "sent_count": 0,
    "last_reminder": null,
    "next_reminder": "2026-04-05T14:00:00+08:00"
  }
}
```

**取消条件**:
- 用户明确指示下一步操作
- 用户要求停止/暂停
- 达到最大提醒次数 (3 次)

---

## Error Handling

- **Clone failures**: Report to user, skip repository
- **SubAgent timeout**: Retry once, then mark as incomplete (focus on other modules)
- **Docker failures**: Fall back to static analysis + POC only (no verification)
- **POC execution errors**: Log output, mark verification as failed (still include POC in submission)
- **CVE rejection**: If CVE is rejected, analyze reason and adjust discovery strategy

## Output Delivery

Present to user:

1. **CVE Submission Report** (primary deliverable)
   - CVE-worthy vulnerabilities only
   - Weaponized POCs
   - CVSS scoring
   - Submission-ready format

2. **Individual Vulnerability Reports** (detailed technical analysis)

3. **Weaponized POC Scripts** (ready for demonstration)

4. **(Optional) Verification Results** (if Docker environment was used)

5. **CVE Submission Guidance**:
   - Recommended CNAs for submission
   - Coordinated disclosure timeline
   - Vendor contact templates

---

## 语言特定漏洞参考

审计特定编程语言时，查阅这些指南获取语言特定的漏洞模式：

| 语言 | 指南 | 内容 |
|------|------|------|
| PHP | `references/php-guide.md` | SQL 注入、命令注入、文件包含、XSS、反序列化、路径穿越、SSRF、认证问题 |
| Java | `references/java-guide.md` | SQL 注入、命令注入、XXE、反序列化、路径穿越、SSRF、SSTI、JNDI 注入、Spring 特定问题 |

**重要**: 语言指南包含每种漏洞类型的 Source → Sink 模式。子 Agent 在审计该语言代码时必须查阅相关语言指南。

## 相关模板和参考

- `templates/vulnerability-report-template.md` - 报告格式
- `templates/poc-template.py` - POC 脚本结构
- `templates/subagent-skill-template.md` - 子 Agent 技能模板
- `references/module-detection.md` - 按项目类型的模块检测
- `references/project-structure.md` - 项目存储结构
- `references/php-guide.md` - PHP 漏洞模式 (Source → Sink)
- `references/java-guide.md` - Java 漏洞模式 (Source → Sink)
