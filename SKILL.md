---
name: code-audit-system
description: CVE-oriented multi-agent code audit system. Use when user provides a git repository URL for vulnerability discovery with the goal of submitting CVEs. This skill orchestrates subagents to find exploitable vulnerabilities (RCE, SQLi, Auth Bypass, etc.), write weaponized POCs, and generate CVE-ready reports. ALWAYS use this skill when the user mentions code auditing, vulnerability hunting, CVE discovery, or provides a git URL for security review.
---

# Code Audit System - CVE Discovery Engine

**核心理念**: 只报告可实际利用的漏洞，目标是提交 CVE，而非让代码变得更安全。

**语言要求**: 所有报告、总结、用户交互输出必须使用**中文**。代码注释中的技术描述也使用中文。仅以下内容可保留英文：漏洞类型名称（RCE、SQLi 等）、CWE/CVE 编号、CVSS 向量字符串、代码片段、POC 脚本中的变量名和函数名。

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

## 何时使用此技能

- 用户提供 git 仓库 URL 用于 **CVE 发现**
- 用户请求 **可利用漏洞** 猎杀
- 用户想发现 **CVE 级别** 问题 (RCE、SQLi、认证绕过等)
- 用户需要已识别漏洞的 **武器化 POC** 代码
- 用户需要包含利用细节的 **CVE 就绪报告**

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          主代理                                   │
│  - 编排工作流程                                                   │
│  - 管理子代理工作区                                               │
│  - 协调模块检测                                                   │
│  - 汇总报告                                                      │
│  - 与用户交互                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  子代理 1      │   │   子代理 2       │   │  子代理 N      │
│  模块 A       │   │   模块 B         │   │  模块 N        │
│  漏洞扫描器    │   │   漏洞扫描器     │   │  漏洞扫描器    │
└───────────────┘   └─────────────────┘   └───────────────┘
```

## 工作流程概览

1. **项目收集** - 用户提供 git URL
2. **漏洞发现** - 子代理审计代码模块
3. **环境部署** (可选) - Docker 搭建
4. **POC 编写** - 子代理编写利用脚本
5. **验证测试** (可选) - 在部署环境中测试 POC
6. **总结报告** - 主代理汇总所有发现

## 逐步操作说明

### 步骤 1: 项目初始化 (强制标准目录结构)

**⚠️ 重要**: 必须严格遵守标准目录结构，参考 `references/project-structure.md`

当用户提供 git 仓库 URL 时:

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

**阅读**: `state/audit-state-schema.md` 查看完整状态文件格式。

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

**阅读**: `references/project-structure.md` 查看完整目录标准。

### 步骤 2: CVE 发现 (核心流程)

这是核心漏洞猎杀阶段。主代理协调多个子代理。

#### Phase 2.1: 技术侦察

分析项目以发现 CVE:

1. **识别编程语言** - 扫描文件扩展名、包文件
2. **检测框架和组件** - 检查 package.json、requirements.txt、pom.xml 等
3. **确定应用类型** - Web 应用、系统服务、GUI、移动应用等
4. **映射攻击面** - 用户输入点、认证机制、文件操作、网络接口

在 `workspace/00-work-background.md` 创建 **工作背景** 文档，包含:
- 技术栈总结
- 应用类型分类
- **攻击面地图** (入口点、信任边界)
- **高风险区域** (认证、文件操作、序列化、命令执行)

**使用**: `references/module-detection.md` 获取按项目类型的模块结构模板。

#### Phase 2.2: 模块划分

将代码库划分为逻辑模块以进行并行审计:

1. 从目录结构识别模块边界
2. 将文件映射到每个模块
3. 识别模块间依赖关系
4. 创建模块依赖图

将模块映射存储在 `workspace/01-module-map.md`。

#### Phase 2.3: 子代理调度 (CVE 猎手)

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

**调度策略**:
- 如果模块间无依赖 → 并行调度
- 如果模块间有依赖 → 按依赖顺序调度

**阅读**:
- `templates/subagent-skill-template.md` 用于创建子代理技能
- `templates/subagent-background-template.md` 用于创建背景文档 ⭐

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

**子代理指令必须包含**:
- **目标源代码路径** (绝对路径): `<project-root>/source/<module>/`
- **报告输出位置** (绝对路径): `<project-root>/workspace/agent-<module>/report.md`
- **背景文档位置** (启动后必须阅读): `<project-root>/workspace/agent-<module>/background.md`
- **专项技能位置** (启动后必须阅读): `<project-root>/workspace/agent-<module>/skill.md`
- 仅关注可利用漏洞
- 追踪完整调用链 (Source → Sink)
- 记录安全控制措施和绕过方法
- 过滤理论性问题

**⚠️ 子代理启动强制流程**: 子代理被调度后，必须**首先使用 Read 工具读取 `background.md` 和 `skill.md`**，然后基于这些定制文档中的指导开展审计。这些文档包含了针对该模块的技术侦察结果、高价值目标、审计思路和绕过分析，是提升发现率的关键。

#### Phase 2.4: CVE 就绪漏洞报告

每个子代理必须生成 **CVE 就绪报告**，包含:

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

**使用**: `templates/vulnerability-report-template.md` 获取报告格式。

**CVE 提交标准**:
- CVSS ≥ 7.0 (高危/严重)
- 影响真实用户 (非仅本地/测试)
- 有明确受影响版本
- 可用 POC 演示

### 步骤 3: 环境部署 (可选 - 询问用户)

继续前，询问用户:
> "是否要在 Docker 环境中部署目标应用程序以进行漏洞验证? 这样可以在隔离环境中测试 POC。"

如果用户确认:

1. **检查现有 Docker 配置** - 在源代码仓库中查找 Dockerfile、docker-compose.yml
2. **创建 Docker 环境** (如果不存在):
   - 分析应用依赖 (包文件、构建工具、运行时需求)
   - 编写适当的 `Dockerfile`
   - 创建包含服务依赖的 `docker-compose.yml` (MySQL、PostgreSQL、Neo4j 等)

3. **编写 Docker 文件**:
   - 对于典型 Web 应用，创建多阶段 Dockerfile (构建和运行阶段)
   - 使用 `docker-compose.yml` 定义应用服务加数据库/依赖服务
   - 将 Docker 配置存储在项目的 `docker/` 目录

4. **Dockerfile 模板示例**:
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

5. **docker-compose.yml 模板示例**:
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

6. **启动环境**:
   ```bash
   docker-compose up -d
   ```

**注意**: 如果目标应用有特殊需求 (如特定中间件、缓存层或复杂网络)，需相应调整 Docker 配置。

### 步骤 4: 武器化 POC 编写

调度子代理为 CVE 提交编写 **武器化** 的概念验证利用:

1. **阅读步骤 2 的漏洞报告** (仅 CVE 级别)
2. **创建 POC 目录**: `<project-root>/pocs/`
3. **为每个 CVE 级别漏洞** 创建 Python 脚本:
   - `poc-001-rce-auth-bypass.py`
   - `poc-002-sqli-admin-takeover.py`
   - `poc-003-path-traversal-rce.py`

**POC 要求 (CVE 提交标准)**:
- 自包含的 Python 脚本 (除 requests 外无外部依赖)
- 清晰的使用说明和示例命令
- 可配置的目标 URL/主机/端口
- **默认武器化** (演示完整影响)
- 安全执行 (无永久损害，但证明利用)
- **利用前/后证据** (如 `whoami` 输出、创建的文件、提取的数据)
- 注释中的 CVSS 评分依据

**POC 结构**:
```python
#!/usr/bin/env python3
"""
CVE-XXXX-XXXXX: [漏洞名称]
目标: [产品名] [受影响版本]
发现者: [你的名字]
CVSS: [评分] [向量]

用法: python3 poc.py -t http://target:port

概念验证:
- 利用前: [正常状态]
- 利用中: [攻击动作]
- 利用后: [被攻陷状态]
"""
```

**阅读**: `templates/poc-template.py` 获取 POC 结构。

**CVE 提交包**:
为每个 CVE 级别漏洞准备:
1. POC 脚本 (武器化)
2. 视频演示 (可选但推荐)
3. 技术报告 (影响、受影响版本、修复建议)
4. CVSS v3.1 评分

### 步骤 5: 漏洞验证 (可选 - 询问用户)

询问用户:
> "是否要在部署的环境中验证 POC? 这将测试每个利用是否有效并生成验证报告。"

如果用户确认:

1. **部署目标** (未在步骤 3 中完成)
2. **对部署的 Docker 环境运行每个 POC**
3. **记录结果**:
   - 成功/失败
   - 输出/证据
   - 利用耗时

4. **创建验证报告**: `reports/verification-report.md`

验证报告在漏洞报告基础上增加:
- 验证状态: "成功" / "失败"
- POC 路径: POC 脚本的完整路径
- 执行输出: POC 运行的终端输出
- 证据: 截图、响应数据等

### 步骤 6: CVE 提交报告

主代理将所有发现汇总为 **CVE 就绪提交包**:

1. **收集所有报告**:
   - 子代理的独立漏洞报告 (仅 CVE 级别)
   - 武器化 POC 脚本
   - POC 验证结果 (如已验证)

2. **Generate CVE Submission Report** at `reports/cve-submission-report.md`:

```markdown
# CVE 提交报告

## 项目概览
- **产品**: [产品名称]
- **仓库地址**: <git-url>
- **厂商**: [厂商名称]
- **审计日期**: <date>
- **审计人员**: [你的名称/代号]

## 执行摘要 (CVE 导向)
- **CVE 级别漏洞**: <count> (CVSS ≥ 7.0)
- **严重 (CVSS 9.0-10.0)**: <count>
- **高危 (CVSS 7.0-8.9)**: <count>
- **已武器化 POC 总数**: <count>

## CVE 候选列表

| 编号 | 漏洞类型 | CVSS | 受影响版本 | POC | 状态 |
|------|----------|------|-----------|-----|------|
| CVE-XXXX-XXXXX | RCE | 9.8 | v1.0-v2.3 | ✅ | 准备提交 |
| CVE-XXXX-XXXXX | 认证绕过 | 8.5 | v1.5-v2.3 | ✅ | 准备提交 |

## 详细 CVE 报告

### CVE-XXXX-XXXXX: [漏洞名称]

**严重程度**: 严重 (CVSS 9.8)
**向量**: AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
**受影响版本**: v1.0 - v2.3
**已修复版本**: [如已知]

**技术细节**:
- **位置**: `file.py:行号`
- **根本原因**: [简要描述]
- **攻击向量**: [攻击者如何利用]
- **影响**: [攻击者可达成的目标]

**调用链**:
```
用户输入() → 漏洞函数() → 危险操作()
```

**POC**: `pocs/poc-001-rce.py`

**验证结果**: ✅ 成功 (详见验证报告)

**修复建议**: [厂商修复步骤]

## 提交检查清单

每个 CVE 需确认:
- [ ] 技术报告完成
- [ ] POC 已武器化并测试
- [ ] CVSS v3.1 评分已计算
- [ ] 受影响版本已确认
- [ ] 厂商联系方式 (如协调披露)
- [ ] 视频演示 (可选)

## 附录
- 完整报告: `reports/vulnerability-*.md`
- 武器化 POC: `pocs/`
- 验证报告: `reports/verification-report.md`
- 调用图: `reports/call-graphs/` (如有)
```

3. **CVE 提交渠道**:
   - **MITRE**: 主要 CVE CNA
   - **GitHub Security Advisories**: 开源项目
   - **厂商 PSIRT**: 协调披露
   - **NVD**: CVE 分配后

4. **存储结构化数据**:
   - 漏洞元数据 (用于追踪)
   - POC 元数据 (版本、目标、影响)
   - 验证结果 (成功/失败、证据)

## 数据存储

### MySQL 架构 (结构化数据)

需要的表:
- `vulnerabilities` - 核心漏洞记录
- `pocs` - POC 脚本元数据
- `verifications` - 验证结果
- `projects` - 项目元数据

### Neo4j 架构 (关系数据)

将调用链建模为:
```
(Node:Function {name: "userInput", output: "string"})
  -[:CALLS]->
(Node:Function {name: "sanitize", output: "string"})
  -[:CALLS]->
(Node:Function {name: "executeQuery", output: "result"})
```

每个实体包含:
- 输入参数属性
- 输出作为属性或边标签
- 源代码位置 (文件:行号)

## 子代理工作区创建

为每个子代理创建专用工作区:

1. **skill.md** - 模块特定审计指令
2. **work-background.md** - 技术背景
3. **module-info.md** - 文件列表、职责、接口
4. **report.md** - 输出模板

当模块独立时使用 `superpowers:dispatching-parallel-agents` 技能。

## 子代理完成通知 (推送模型)

**重要**: 子代理完成后必须 **主动通知** 主代理，而非等待轮询。

**推送机制**:
- 子代理完成审计后，立即将报告发送回主代理
- 主代理实时汇总收到的报告
- 所有子代理完成后，主代理向用户发送综合总结

**优势**:
- 用户无需等待所有代理即可收到及时更新
- 主代理可实时跟踪进度
- 失败的代理可被快速检测

**实现**:
```
子代理完成 → 返回报告 → 主代理接收 → 汇总 → 等待剩余代理
                                              ↓
                                      全部完成 → 用户总结
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

## 错误处理

- **克隆失败**: 报告给用户，跳过该仓库
- **子 Agent 超时**: 重试一次，然后标记为未完成 (专注其他模块)
- **Docker 失败**: 回退到静态分析 + POC (无验证)
- **POC 执行错误**: 记录输出，标记验证为失败 (仍在提交中包含 POC)
- **CVE 被拒**: 分析原因并调整发现策略

## 输出交付

向用户展示:

1. **CVE 提交报告** (主要交付物)
   - 仅包含 CVE 级别漏洞
   - 武器化 POC
   - CVSS 评分
   - 提交就绪格式

2. **独立漏洞报告** (详细技术分析)

3. **武器化 POC 脚本** (可用于演示)

4. **(可选) 验证结果** (如使用 Docker 环境)

5. **CVE 提交指南**:
   - 推荐的 CNA 提交渠道
   - 协调披露时间线
   - 厂商联系模板

---

## 语言特定漏洞参考

审计特定编程语言时，查阅这些指南获取语言特定的漏洞模式：

| 语言 | 指南 | 内容 |
|------|------|------|
| PHP | `references/php-guide.md` | SQL 注入、命令注入、文件包含、XSS、反序列化、路径穿越、SSRF、认证问题 |
| Java | `references/java-guide.md` | SQL 注入、命令注入、XXE、反序列化、路径穿越、SSRF、SSTI、JNDI 注入、Spring 特定问题 |

**重要**: 语言指南包含每种漏洞类型的 Source → Sink 模式。子 Agent 在审计该语言代码时必须查阅相关语言指南。

## 相关模板和参考

- `templates/vulnerability-report-template.md` - 漏洞报告格式 (中文)
- `templates/summary-report-template.md` - 总结报告格式 (中文)
- `templates/verification-report-template.md` - 验证报告格式 (中文)
- `templates/poc-template.py` - POC 脚本结构
- `templates/subagent-skill-template.md` - 子代理技能模板
- `templates/subagent-background-template.md` - 子代理背景文档模板
- `templates/work-background-template.md` - 工作背景模板 (中文)
- `templates/module-info-template.md` - 模块信息模板 (中文)
- `references/module-detection.md` - 按项目类型的模块检测
- `references/project-structure.md` - 项目存储结构
- `references/php-guide.md` - PHP 漏洞模式 (Source → Sink)
- `references/java-guide.md` - Java 漏洞模式 (Source → Sink)
