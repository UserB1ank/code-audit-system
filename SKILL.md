---
name: code-audit-system
description: 以 CVE 为导向的多 Agent 代码审计系统。当用户提供 git 仓库 URL 进行漏洞发现、提交 CVE 时使用。本系统协调子 Agent 发现可利用漏洞（RCE、SQLi、Auth Bypass 等）、编写武器化 POC、生成 CVE 就绪报告。当用户提到代码审计、漏洞挖掘、CVE 发现，或提供 git URL 进行安全审查时，必须使用此 Skill。
---

# 代码审计系统 - CVE 发现引擎

> 所有的输出必须是中文！

**核心理念**: 只报告可实际利用的漏洞，目标是提交 CVE，而非让代码变得更安全。

本 Skill 协调多 Agent 系统发现可利用漏洞，唯一的目的是 CVE 提交。它过滤掉理论问题，只关注具有完整漏洞利用链的漏洞。

## ⭐ CVE 导向审计原则

### 核心原则（必须遵守）

1. **只报告可实际利用的漏洞**
   - ✅ 有明确用户输入入口（Source）
   - ✅ 有完整调用链（Source → Sink）
   - ✅ 无有效安全控制阻断
   - ✅ 可编写可执行 POC
   - ❌ 拒绝理论漏洞（无输入入口）
   - ❌ 拒绝潜在漏洞（需要不可能的条件）
   - ❌ 拒绝被安全控制完全阻断的漏洞

2. **CVE 提交标准**
   - 目标：CVSS ≥ 7.0（高危/严重）
   - 必须有 POC 验证
   - 必须影响真实用户（非本地/测试环境）
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
| 潜在漏洞 | ❌ 丢弃 | 需要特殊/不可能条件 |
| 被阻断漏洞 | ❌ 丢弃 | 有有效安全控制 |

---

## 何时使用本 Skill

- 用户提供 git 仓库 URL 进行 **CVE 发现**
- 用户请求 **可利用漏洞** 挖掘
- 用户想找到 **CVE 级别** 的问题（RCE、SQLi、Auth Bypass 等）
- 用户需要 **武器化 POC** 代码
- 用户需要 **CVE 就绪报告**，包含漏洞利用详情

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        主 Agent                                   │
│  - 协调工作流程                                                   │
│  - 管理子 Agent 工作区                                           │
│  - 协调模块检测                                                  │
│  - 聚合报告                                                     │
│  - 与用户交互                                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  子 Agent 1   │   │   子 Agent 2    │   │  子 Agent N   │
│  模块 A       │   │   模块 B        │   │   模块 N      │
│  漏洞扫描器   │   │   漏洞扫描器    │   │   漏洞扫描器  │
└───────────────┘   └─────────────────┘   └───────────────┘
```

## 工作流程概述

1. **项目收集** - 用户提供 git URL
2. **漏洞发现** - 子 Agent 审计代码模块
3. **POC 编写** - 子 Agent 编写漏洞利用脚本
4. **环境部署**（可选）- Docker 安装
5. **验证**（可选）- 在部署环境中测试 POC
6. **总结报告** - 主 Agent 聚合所有发现

## 步骤详解

### 步骤 1：项目初始化（标准目录结构）

**⚠️ 重要**: 必须严格遵守标准目录结构，参考 `references/project-structure.md`

当用户提供 git 仓库 URL 时：

1. **创建标准项目目录**:
   ```bash
   mkdir -p code-audit-projects/<project-name>/{source,state,workspace,pocs,reports,docker}
   ```

2. **克隆源代码到 source/**（必须）:
   ```bash
   cd code-audit-projects/<project-name>/
   git clone <git-url> source/
   ```

   **❌ 错误**: `git clone <url> .`（直接克隆到根目录）
   **✅ 正确**: `git clone <url> source/`（克隆到 source/ 子目录）

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

4. **创建技术背景文档**（主 Agent 负责）:
   - `workspace/00-work-background.md` - 技术栈、攻击面、CVE 发现策略
   - `workspace/01-module-map.md` - 模块划分、文件映射

5. **创建状态文件**（必须，支持断点续传）:
   - `state/audit-state.json` - 审计状态追踪 ⭐
   - `state/task-history.jsonl` - 事件历史日志 ⭐

**状态文件作用**:
- ✅ 记录审计进度（阶段、子 Agent 状态、漏洞发现）
- ✅ 支持断点续传（崩溃/暂停后恢复）
- ✅ 定期保存检查点（`state/checkpoint-<timestamp>.json`）
- ✅ 实时日志追加（`task-history.jsonl`）

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

**Read**: `references/state/audit-state-schema.md` 查看完整状态文件格式

**完整目录结构**:
```
code-audit-projects/<project-name>/
├── source/              # ✅ 源代码（git clone 必须到此）
├── state/               # ✅ 状态追踪
│   ├── audit-state.json
│   └── task-history.jsonl
├── workspace/           # ✅ CVE Hunter 工作区
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   └── agent-<module>/
│       ├── skill.md
│       └── report.md
├── pocs/                # ✅ POC 脚本（CVE 验证后）
├── reports/             # ✅ CVE 报告（最终输出）
└── metadata.json        # ✅ 项目元数据
```

**Read**: `references/project-structure.md` 查看完整目录标准

### 步骤 2：CVE 发现（主流程）

这是核心漏洞挖掘阶段。主 Agent 协调多个子 Agent。

#### 阶段 2.1：技术侦察

分析项目进行 CVE 发现：

1. **识别编程语言** - 扫描文件扩展名、包文件
2. **检测框架和组件** - 检查 package.json、requirements.txt、pom.xml 等
3. **确定应用类型** - Web 应用、系统服务、GUI、移动端等
4. **绘制攻击面** - 用户输入点、认证机制、文件操作、网络接口

在 `workspace/00-work-background.md` 创建**工作背景**文档：
- 技术栈总结
- 应用类型分类
- **攻击面地图**（入口点、信任边界）
- **高风险区域**（认证、文件操作、序列化、命令执行）

**Use**: `references/module-detection.md` 查看按项目类型的模块结构模板

#### 阶段 2.2：模块划分

将代码库划分为逻辑模块以便并行审计：

1. 从目录结构识别模块边界
2. 将文件映射到各模块
3. 识别模块间依赖
4. 创建模块依赖图

在 `workspace/01-module-map.md` 存储模块映射

#### 阶段 2.3：子 Agent 调度（CVE 猎人）

**⚠️ 目录结构要求**: 必须使用标准工作区布局

**主 Agent 必须为每个子 Agent 创建独立背景文档**

为每个模块创建专用子 Agent 工作区：

```
workspace/
├── 00-work-background.md        # ✅ 主 Agent 创建（全局技术侦察）
├── 01-module-map.md             # ✅ 主 Agent 创建（模块划分）
├── agent-<module-1>/            # ✅ 子 Agent 1 工作区
│   ├── background.md            # 主 Agent 创建（独立背景文档）⭐
│   ├── skill.md                 # 主 Agent 创建（审计指令）
│   ├── execution.log            # ⭐ 子 Agent 执行日志（自动保存）
│   └── report.md                # 子 Agent 输出（CVE 报告）
├── agent-<module-2>/            # ✅ 子 Agent 2 工作区
│   ├── background.md            # ⭐ 新增
│   ├── execution.log            # ⭐ 新增
│   └── report.md
└── agent-<module-N>/            # ✅ 子 Agent N 工作区
    ├── background.md            # ⭐ 新增
    ├── execution.log            # ⭐ 新增
    └── report.md
```

**调度策略**:
- 如果模块之间**没有依赖** → 使用线程池并行调度
- 如果模块之间**有依赖** → 按依赖顺序调度

**Read**:
- `templates/subagent/subagent-skill-template.md` - 创建子 Agent skill
- `templates/subagent/subagent-background-template.md` - 创建背景文档

---

### 主 Agent 创建子 Agent 背景文档（必须）

**每个子 Agent 启动前**，主 Agent 必须创建 `workspace/agent-<module>/background.md`：

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

**子 Agent 指令必须包含**:
- **目标源代码路径**（绝对路径）: `/home/pc01/.openclaw/workspace-cybersecurity_expert/code-audit-projects/<project>/source/<module>/`
- **报告输出位置**（绝对路径）: `/home/pc01/.openclaw/workspace-cybersecurity_expert/code-audit-projects/<project>/workspace/agent-<module>/report.md`
- **背景文档位置**（必须阅读）: `/home/pc01/.openclaw/workspace-cybersecurity_expert/code-audit-projects/<project>/workspace/agent-<module>/background.md`
- 仅关注可利用漏洞
- 追踪完整调用链（Source → Sink）
- 记录安全控制及绕过方法
- 过滤理论问题

#### 阶段 2.4：CVE 就绪漏洞报告

每个子 Agent 必须生成 **CVE 就绪报告**：

| 字段 | 描述 |
|-----|------|
| **漏洞类型** | RCE、SQLi、Auth Bypass、Path Traversal 等 |
| **可利用性** | ✅ 可利用 / ❌ 理论 |
| **需要认证** | 无 / 低权限 / 高权限 |
| **位置** | 文件路径和行号（如 `auth/login.py:45-52`） |
| **调用链** | 完整：`userInput() → process() → sink()` |
| **安全控制** | 存在什么、如何绕过 |
| **严重性** | Critical/High（CVE 级别）/ Medium / Low |
| **CVSS 评分** | 基础分 0.0-10.0（目标 ≥7.0） |
| **POC 可行性** | ✅ 可武器化 / ❌ 无法武器化 |
| **证据** | 带行号的代码片段 |

**Use**: `templates/reports/vulnerability-report-template.md` 查看报告格式

**CVE 提交标准**:
- CVSS ≥ 7.0（高危/严重）
- 影响真实用户（非本地/测试）
- 有明确的受影响版本
- 可以用 POC 演示

### 步骤 3：环境部署（可选 - 询问用户）

继续之前先询问用户：
> "是否要在 Docker 环境中部署目标应用进行漏洞验证？这允许在隔离环境中测试 POC。"

如果用户确认：

1. **检查现有 Docker 配置** - 查找 Dockerfile、docker-compose.yml
2. **创建 Docker 环境**（如不存在）:
   - 分析应用依赖
   - 编写适当的 Dockerfile
   - 创建 docker-compose.yml（含 MySQL、Neo4j 等服务依赖）

3. **使用 skills 部署**:
   - 使用 `docker-essentials` skill 进行容器设置
   - 使用 `docker-sandbox` skill 进行隔离测试环境

4. **启动环境**:
   ```bash
   docker-compose up -d
   ```

**Store**: Docker 配置到 `workspace/docker/`

### 步骤 4：武器化 POC 编写

调度子 Agent 为 CVE 提交编写**武器化**概念验证漏洞利用：

1. **读取漏洞报告**（步骤 2 中的 CVE 级别报告）
2. **创建 POC 目录**: `<project-root>/pocs/`
3. **为每个 CVE 级别漏洞**创建 Python 脚本：
   - `poc-001-rce-auth-bypass.py`
   - `poc-002-sqli-admin-takeover.py`
   - `poc-003-path-traversal-rce.py`

**POC 要求（CVE 提交标准）**:
- 自包含 Python 脚本（除 requests 外无外部依赖）
- 带有示例命令的清晰使用说明
- 可配置目标 URL/主机/端口
- **默认武器化**（展示完整影响）
- 安全执行（无持久损害，但证明漏洞利用）
- **执行前后证据**（如 `whoami` 输出、创建的文件、提取的数据）
- 评论中的 CVSS 评分说明

**POC 结构**:
```python
#!/usr/bin/env python3
"""
CVE-XXXX-XXXXX: [漏洞名称]
目标: [产品] [受影响版本]
作者: [你的名字]
CVSS: [评分] [向量]

用法: python3 poc.py -t http://target:port

概念验证:
- 执行前: [正常状态]
- 漏洞利用: [动作]
- 执行后: [被攻击状态]
"""
```

**Read**: `templates/reports/poc-template.py` 查看 POC 结构

**CVE 提交包**:
为每个 CVE 级别漏洞准备：
1. POC 脚本（武器化）
2. 视频演示（可选但推荐）
3. 技术报告（影响、受影响版本、修复方案）
4. CVSS v3.1 评分

### 步骤 5：漏洞验证（可选 - 询问用户）

询问用户：
> "是否要在部署环境中验证 POC？这将测试每个漏洞利用是否有效并生成验证报告。"

如果用户确认：

1. **部署目标**（步骤 3 未完成）
2. **在沙盒环境中运行每个 POC**
3. **记录结果**:
   - 成功/失败
   - 输出/证据
   - 利用时间

4. **创建验证报告**: `reports/verification-report.md`

验证报告在漏洞报告基础上增加：
- 验证状态："成功" / "失败"
- POC 路径：POC 脚本完整路径
- 执行输出：POC 运行时的终端输出
- 证据：截图、响应数据等

### 步骤 6：CVE 提交报告

主 Agent 聚合所有发现生成 **CVE 提交包**：

1. **收集所有报告**:
   - 子 Agent 的单独漏洞报告（仅 CVE 级别）
   - 武器化 POC 脚本
   - POC 验证结果（如已验证）

2. **在 `reports/cve-submission-report.md` 生成 CVE 提交报告**:

```markdown
# CVE 提交报告

## 项目概述
- **产品**: [产品名称]
- **仓库**: <git-url>
- **供应商**: [供应商名称]
- **审计日期**: <日期>
- **审计员**: [你的名字/昵称]

## 执行摘要（CVE 重点）
- **CVE 级别漏洞**: <数量>（CVSS ≥ 7.0）
- **严重（CVSS 9.0-10.0）**: <数量>
- **高危（CVSS 7.0-8.9）**: <数量>
- **武器化 POC 总数**: <数量>

## CVE 候选

| ID | 类型 | CVSS | 受影响版本 | POC | 状态 |
|----|------|------|-------------------|-----|--------|
| CVE-XXXX-XXXXX | RCE | 9.8 | v1.0-v2.3 | ✅ | 准备提交 |
| CVE-XXXX-XXXXX | Auth Bypass | 8.5 | v1.5-v2.3 | ✅ | 准备提交 |

## 详细 CVE 报告

### CVE-XXXX-XXXXX: [漏洞名称]

**严重性**: 严重（CVSS 9.8）
**向量**: AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
**受影响版本**: v1.0 - v2.3
**修复版本**: [如有]

**技术详情**:
- **位置**: `file.py:line`
- **根因**: [简要描述]
- **攻击向量**: [攻击者如何利用]
- **影响**: [攻击者实现什么]

**调用链**:
```
userInput() → vulnerable_function() → sink()
```

**POC**: `pocs/poc-001-rce.py`

**验证**: ✅ 成功（见验证报告）

**修复方案**: [供应商修复步骤]

## 提交清单

每个 CVE:
- [ ] 技术报告完整
- [ ] POC 武器化并测试
- [ ] CVSS v3.1 评分已计算
- [ ] 受影响版本已确认
- [ ] 供应商联系信息（如协调披露）
- [ ] 视频演示（可选）

## 附录
- 完整报告: `reports/vulnerability-*.md`
- 武器化 POC: `pocs/`
- 验证: `reports/verification-report.md`
- 调用图: `reports/call-graphs/`（如有）
```

3. **CVE 提交目标**:
   - **MITRE**: 主要 CVE CNA
   - **GitHub 安全公告**: 开源项目
   - **供应商 PSIRT**: 协调披露
   - **NVD**: CVE 分配后

4. **存储结构化数据**:
   - 漏洞元数据（用于跟踪）
   - POC 元数据（版本、目标、影响）
   - 验证结果（成功/失败、证据）

## 数据存储

### MySQL 模式（结构化数据）

需要的表：
- `vulnerabilities` - 核心漏洞记录
- `pocs` - POC 脚本元数据
- `verifications` - 验证结果
- `projects` - 项目元数据

### Neo4j 模式（关系数据）

将调用链建模为：
```
(Node:Function {name: "userInput", output: "string"})
  -[:CALLS]->
(Node:Function {name: "sanitize", output: "string"})
  -[:CALLS]->
(Node:Function {name: "executeQuery", output: "result"})
```

每个实体有：
- 输入参数属性
- 输出作为属性或边标签
- 源位置（file:line）

## 子 Agent 工作区创建

为每个子 Agent 创建专用工作区：

1. **skill.md** - 模块特定审计指令
2. **background.md** - 技术上下文
3. **module-info.md** - 文件列表、职责、接口
4. **report.md** - 输出模板

当模块独立时，使用 `superpowers:dispatching-parallel-agents` skill

## 子 Agent 完成通知（推送模型）

**重要**: 子 Agent 必须在完成时**主动通知**主 Agent，而不是等待轮询。

**推送机制**:
- 子 Agent 完成审计时，立即将报告发送回主 Agent
- 主 Agent 实时聚合收到的报告
- 所有子 Agent 完成后，主 Agent 向用户发送汇总摘要

**好处**:
- 用户无需等待所有 Agent 即可收到及时更新
- 主 Agent 可以实时跟踪进度
- 快速检测失败的 Agent

**实现**:
```
子 Agent 完成 → 返回报告 → 主 Agent 接收 → 聚合 → 等待剩余
                                                              ↓
                                                    全部完成 → 用户摘要
```

---

## ⏰ 自动提醒机制

**触发条件**: 审计完成后，用户未指示下一步操作

### 提醒计划

| 时间点 | 行为 |
|--------|------|
| 完成时 | 显示审计结果 + 下一步建议选项 |
| +1 小时 | 询问是否需要继续（POC 开发/CVE 提交）|
| +2 小时 | 再次提醒 + 强调 Critical 漏洞风险 |
| +3 小时 | 最后提醒 + 建议暂停/归档项目 |

### 提醒消息模板

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

### 实现

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
- 达到最大提醒次数（3 次）

---

## 错误处理

- **克隆失败**: 报告给用户，跳过仓库
- **子 Agent 超时**: 重试一次，然后标记为不完整（专注于其他模块）
- **Docker 失败**: 回退到静态分析 + 仅 POC（无验证）
- **POC 执行错误**: 记录输出，标记验证为失败（仍包含在提交中）
- **CVE 拒绝**: 分析原因并调整发现策略

## 输出交付

向用户展示：

1. **CVE 提交报告**（主要交付物）
   - 仅 CVE 级别漏洞
   - 武器化 POC
   - CVSS 评分
   - 提交就绪格式

2. **单独漏洞报告**（详细技术分析）

3. **武器化 POC 脚本**（准备演示）

4. **（可选）验证结果**（如使用了 Docker 环境）

5. **CVE 提交指导**:
   - 推荐用于提交的 CNA
   - 协调披露时间线
   - 供应商联系模板

---

## 文件引用

### 引用文件总览

| 分类 | 文件名 | 作用 | 路径 |
|------|--------|------|------|
| **Skill 核心** | SKILL.md | 主 Skill 文件，包含完整工作流程和调度指令 | `./SKILL.md` |
| **References 参考文档** | | | |
| | project-structure.md | 审计项目标准目录结构规范 | `./references/project-structure.md` |
| | module-detection.md | 按项目类型的模块划分模板 | `./references/module-detection.md` |
| | audit-state-schema.md | 状态文件格式规范（audit-state.json、task-history.jsonl）| `./references/state/audit-state-schema.md` |
| **Templates 模板** | | | |
| | work-background-template.md | 工作背景文档模板 | `./templates/work-background-template.md` |
| **子 Agent 模板** | | | |
| | subagent-skill-template.md | 子 Agent 审计指令模板 | `./templates/subagent/subagent-skill-template.md` |
| | subagent-background-template.md | 子 Agent 独立背景文档模板 | `./templates/subagent/subagent-background-template.md` |
| | execution-log-template.md | 子 Agent 执行日志格式规范 | `./templates/subagent/execution-log-template.md` |
| | module-info-template.md | 模块信息文档模板 | `./templates/subagent/module-info-template.md` |
| **报告模板** | | | |
| | vulnerability-report-template.md | CVE 漏洞报告模板 | `./templates/reports/vulnerability-report-template.md` |
| | summary-report-template.md | 综合 CVE 提交报告模板 | `./templates/reports/summary-report-template.md` |
| | verification-report-template.md | POC 验证报告模板 | `./templates/reports/verification-report-template.md` |
| | poc-template.py | POC 脚本结构模板 | `./templates/reports/poc-template.py` |
| **Evals 评估** | | | |
| | evals.json | Skill 测试用例 | `./evals/evals.json` |
| | trigger-evals.json | Skill 触发评估集 | `./evals/trigger-evals.json` |

---

## 快速参考

### 标准目录结构

```
code-audit-projects/<project-name>/
├── source/                  # 源代码（git clone 必须到此目录）
├── state/                   # 任务状态追踪（必须）
│   ├── audit-state.json     # 审计状态
│   └── task-history.jsonl   # 历史事件日志
├── workspace/               # CVE Hunter 工作区（必须）
│   ├── 00-work-background.md    # 技术侦察报告（主 Agent 创建）
│   ├── 01-module-map.md         # 模块划分图（主 Agent 创建）
│   ├── agent-<module-1>/        # 子 Agent 1 工作区
│   │   ├── skill.md             # 子 Agent 审计指令
│   │   └── report.md            # CVE 审计报告（子 Agent 输出）
│   └── agent-<module-N>/        # 子 Agent N 工作区
│       └── report.md
├── pocs/                    # POC 脚本（CVE 验证后创建）
├── reports/                 # 审计报告（最终输出）
├── docker/                  # Docker 环境（可选）
└── metadata.json            # 项目元数据（必须）
```

### 关键规则

1. `git clone` 必须克隆到 `source/` 子目录
2. 状态文件必须在 `state/` 目录
3. 主 Agent 必须预先创建背景文档
4. 每个子 Agent 必须有独立工作区
5. 仅报告 CVE 级别漏洞（CVSS ≥ 7.0）
