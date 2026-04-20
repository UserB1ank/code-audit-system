# 用 AI 多智能体系统做代码审计：一个面向 CVE 提交的审计引擎

> 给 AI 一份源代码，告诉它只找能提交 CVE 的漏洞——它是怎么做的？

## 引言

Code Audit System 是一个以 Skill 形式交付的多智能体代码审计系统。它能对 Git 仓库进行安全审计，发现可利用的漏洞，编写 POC，生成 CVE 提交报告包。

整个系统没有一行可执行代码，全部逻辑以 Markdown 文件定义——一个约 800 行的 Skill 定义文件（`SKILL.md`），加上模板和参考文档。系统的运行依赖 AI 编程助手的 Agent 编排能力，`SKILL.md` 定义的是工作流、约束和知识。

## 设计思路：多智能体协同

系统的核心设计是 MainAgent 与多个 SubAgent 的协同工作。MainAgent 负责全局编排，不直接审计代码；每个 SubAgent 拥有独立的提示词（`skill.md`）和工作空间（`workspace/agent-<module>/`），按照自己的提示词去理解任务、阅读背景文档、执行审计、输出报告。

每个 SubAgent 启动后做的事情是：

1. 读 `skill.md` — 理解自己的角色、约束和审计流程
2. 读 `background.md` — 了解自己负责的模块、文件列表、预期漏洞类型、调用流
3. 按照提示词中的四阶段流程执行审计
4. 将结果写入 `report.md`

SubAgent 之间互不干扰，各自在自己的工作空间内独立运行。MainAgent 通过文件系统与 SubAgent 通信——分发时写文件注入上下文，完成后读文件收集结果。

### 漏洞利用链约束

系统对漏洞报告有严格的约束，不是发现什么就报告什么。漏洞报告必须同时满足四个条件：

1. 有明确的用户输入入口（Source）
2. 有完整的调用链（Source → Sink），每一层标注文件名和行号
3. 无有效安全控制阻断
4. 可以编写可执行 POC

任何一个条件不满足，直接丢弃。

| 问题类型 | 处理方式 | 理由 |
|---------|---------|------|
| 可利用漏洞 | 报告 | 有输入入口 + 完整调用链 + 无有效阻断 |
| 理论漏洞 | 丢弃 | 没有用户输入入口 |
| 潜在漏洞 | 丢弃 | 需要不可能的条件 |
| 被阻断的漏洞 | 丢弃 | 有有效的安全控制 |

CVSS ≥ 7.0（High/Critical）是内化的提交门槛。子智能体自动过滤 Medium/Low 级别的问题，除非它们能串联成更高危的攻击链。

## 项目结构：审计工作的骨架

系统对目录结构有严格的标准约束。这不是随意的规定——审计过程会产生大量状态文件、工作区、报告和 POC 脚本，和源代码混在一起会导致管理混乱。

```
code-audit-projects/<project>/
├── source/              # 源代码（git clone 的目标，必须在子目录）
├── state/               # 审计状态追踪
│   ├── audit-state.json       # 项目状态、阶段进度、子智能体状态、漏洞发现
│   └── task-history.jsonl     # 追加写入的事件日志
├── workspace/           # 子智能体工作区
│   ├── 00-work-background.md  # 全局技术侦察结果
│   ├── 01-module-map.md       # 模块划分和文件映射
│   └── agent-<module>/        # 每个子智能体的独立工作区
│       ├── background.md      # MainAgent 创建的背景文档
│       ├── skill.md           # MainAgent 创建的审计指令
│       ├── execution.log      # 子智能体执行日志
│       └── report.md          # 子智能体输出的审计报告
├── pocs/                # POC 脚本
├── reports/             # CVE 报告
├── docker/              # Docker 验证环境
└── metadata.json        # 项目元数据（语言、框架、应用类型）
```

### 状态文件与中断继续

审计过程可能耗时很长，状态管理是工程上的刚需，不是锦上添花。

`audit-state.json` 追踪项目状态、阶段进度、每个子智能体的状态和已发现的漏洞。`task-history.jsonl` 是追加写入的事件日志，记录每个关键操作。系统还会定期保存检查点到 `state/checkpoint-<timestamp>.json`。

项目状态遵循明确的状态机转换：

```
init → cloning → auditing → poc_developing → verifying → reporting → completed
```

如果审计中途崩溃或暂停，恢复流程是：

1. 加载最近的检查点到 `audit-state.json`
2. 用 `jq` 查询所有状态为 `running` 的子智能体
3. 重启未完成的子智能体，继续审计

## 子智能体机制：带着地图去审计

系统采用主从多智能体架构。MainAgent 不直接审计代码，它负责全局编排。实际的代码审计由多个 SubAgent 并行执行，每个 SubAgent 负责一个独立的模块。

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Agent                                │
│  项目初始化 · 技术侦察 · 模块划分 · 任务分发 · 报告聚合           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  SubAgent 1   │   │   SubAgent 2    │   │  SubAgent N   │
│  workspace/   │   │   workspace/    │   │  workspace/   │
│  agent-auth/  │   │   agent-api/    │   │  agent-dao/   │
└───────────────┘   └─────────────────┘   └───────────────┘
```

### 背景文档：SubAgent 不是从零开始

每个 SubAgent 启动前，MainAgent 会为它创建一份 `background.md`。这份文档是 SubAgent 审计的起点，包含六个部分：

**1. 模块涉及文件列表** — 列出模块的核心文件和辅助文件，标注每个文件的 CVE 潜力（🔴高/🟡中/🟢低）。SubAgent 据此分配审计优先级。

**2. 预期漏洞类型** — 按优先级排列模块可能存在的漏洞类型，给出 CVSS 潜力范围和存在可能性评估。例如：

| 漏洞类型 | CVSS 潜力 | 存在可能性 | 审计优先级 |
|----------|-----------|------------|------------|
| RCE | 9.0-10.0 | 高 | 🔴 立即 |
| Auth Bypass | 8.0-10.0 | 中 | 🔴 立即 |
| SQL 注入 | 8.0-9.8 | 高 | 🔴 立即 |

**3. 预期的 Source → Sink 调用流** — 根据代码结构预测可能的调用路径，标注每一层的文件名、行号和处理逻辑：

```
[Source] userInput (Controller.java:10)
  ↓ 接收不可信的 HTTP 参数
[Process] validateInput() (Service.java:25)
  │ 仅检查 null，不验证内容
[Process] buildQuery() (DAO.java:40)
  │ 字符串拼接构造 SQL
[Sink] executeQuery() (DAO.java:55)
  ↓ 执行恶意查询
```

**4. 安全控制清单与绕过分析** — 列出模块中已有的安全控制（输入验证、权限检查、路径规范化等），分析每种控制的绕过方法。

**5. 输入输出流** — 描述模块的完整输入流（从 HTTP 请求到数据库操作）和输出流（从查询结果到 HTTP 响应）。

**6. 审计流程** — 为该模块定制的四阶段审计步骤。

这样设计的目的是让 SubAgent 带着充分的上下文开始工作，而不是在大量源代码中盲目搜索。

### SubAgent 的四阶段审计流程

每个 SubAgent 遵循固定的四阶段流程：

**Phase 1: 代码地图绘制** — 列出所有源文件，识别入口点（public 方法、REST 端点、事件处理器）和危险 Sink（SQL 执行、文件操作、命令执行、网络请求），绘制简化的调用关系图。

**Phase 2: 数据流追踪** — 从 Source 逐层向下追踪到 Sink，记录每层函数的文件名和行号，标注每层的处理逻辑（验证、过滤、转换）。这一步是审计的核心，要求完整追踪每一条 Source → Sink 路径。

**Phase 3: 安全控制分析** — 识别全局策略限制和局部验证逻辑，评估绕过可能性。对每种安全控制，分析其有效性：null 检查是否足够、白名单是否存在、权限检查是否可绕过。

**Phase 4: CVE 报告** — 确认可利用漏洞，计算 CVSS 评分，生成报告。报告必须包含完整的调用链、安全控制分析、绕过方法和影响评估。没有完整调用链的报告直接丢弃。

### SubAgent 工作区布局

每个 SubAgent 拥有独立的工作区目录，包含四个文件：

```
workspace/agent-<module>/
├── background.md    # MainAgent 创建的背景文档（审计前注入）
├── skill.md         # MainAgent 创建的审计指令（角色定义和约束）
├── execution.log    # 子智能体执行过程日志
└── report.md        # 子智能体输出的审计报告
```

`background.md` 和 `skill.md` 由 MainAgent 在分发任务前创建，`execution.log` 和 `report.md` 由 SubAgent 在执行过程中生成。文件系统充当了 MainAgent 和 SubAgent 之间的通信通道——MainAgent 通过写文件传递上下文，SubAgent 通过写文件回传结果。

## 任务分派哲学：侦察在先，分而治之

任务分派不是简单地把代码库切成几块分给不同的 SubAgent。它是一个三步决策过程：技术侦察 → 模块划分 → 调度执行。

### 第一步：技术侦察

MainAgent 先分析项目的整体情况，输出到 `workspace/00-work-background.md`：

1. 识别编程语言 — 扫描文件扩展名和包文件
2. 检测框架和组件 — 检查 `package.json`、`requirements.txt`、`pom.xml` 等
3. 判断应用类型 — Web 应用、系统服务、GUI、移动应用等
4. 映射攻击面 — 用户输入点、认证机制、文件操作、网络接口

这一步的产出决定了后续的模块划分策略。同样是 Java 项目，Spring Boot Web 应用和 Hadoop 数据管道的审计重点完全不同。

### 第二步：模块划分

系统内置了 8 种项目类型的模块划分模板：

| 项目类型 | 划分策略 |
|---------|---------|
| Web 应用（前后端分离） | Frontend / API 层 / Service 层 / Data 层 / 中间件 / Config |
| 单体 Web 应用（MVC） | Controllers / Services / Models / Views / Config / Utils |
| 系统服务（守护进程/CLI） | 入口点 / 核心守护进程 / 网络服务 / 配置解析 / 插件系统 |
| GUI 桌面应用 | Main Process / Renderer / Components / Services / Native 绑定 |
| 移动应用 | UI 层 / Data 层 / Domain 层 / DI 模块 / Network |
| 微服务 | 各个独立服务 / API 网关 / 共享库 / 部署配置 |
| 数据管道/ETL | Extract / Transform / Load / Jobs / DAGs / Config |
| 库/SDK | Core / API / Extras / Examples / Tests |

划分结果输出到 `workspace/01-module-map.md`，记录每个模块的文件列表、职责和审计重点。实际项目往往是混合型的，MainAgent 需要根据实际目录结构调整。

### 第三步：调度执行

模块划分完成后，进入调度阶段。调度策略只有一条规则：

- **模块之间无依赖** → 并行分发
- **模块之间有依赖** → 按依赖顺序分发

每个模块获得独立的 SubAgent 工作区，MainAgent 为其创建 `background.md` 和 `skill.md`，然后通过 Agent 工具派生子智能体。子智能体获得独立的上下文窗口，在自己的工作区内执行审计。

### 推送式完成通知

子智能体采用推送模型——SubAgent 完成审计后主动将报告回传给 MainAgent，而不是 MainAgent 轮询检查。这意味着：

- 用户不需要等所有模块都审计完才能看到结果
- 失败的子智能体能被快速检测到
- MainAgent 实时聚合报告

```
SubAgent 完成 → 回传 report.md → MainAgent 聚合 → 等待剩余
                                            ↓
                                    全部完成 → 输出汇总
```

## 语言特定的漏洞知识库

系统内置了 PHP 和 Java 的漏洞模式指南，覆盖 SQL 注入、命令注入、反序列化、JNDI 注入等主要漏洞类型。每种漏洞类型包含危险函数/API 清单、漏洞代码与安全代码的对比、审计检查清单和 Source → Sink 的典型模式。

这些指南精确到函数级别。SubAgent 在审计时被要求查阅相关语言指南，确保审计过程有据可循。

## 适用场景与局限

### 适合

- 开源项目的安全审计与 CVE 提交（目前覆盖 PHP、Java）
- 安全研究员快速评估一个新项目的安全状况
- 自动化生成 CVE 提交材料
- CTF 比赛中的代码审计环节

### 局限

- 审计质量依赖 AI 模型的代码理解能力，对超大代码库需要合理的模块划分
- 语言指南目前只覆盖 PHP 和 Java
- POC 验证依赖 Docker 环境，特殊架构的应用可能无法自动部署
- 作为 AI 系统，存在漏报的可能，不替代专业安全研究员的经验

## 结语

Code Audit System 的核心思路是：把安全审计的工作流——技术侦察、模块划分、背景注入、数据流追踪、安全控制分析——编码为可复现的结构化流程。MainAgent 负责全局编排和上下文注入，SubAgent 带着背景文档深入特定模块。文件系统充当通信通道，状态文件支撑断点续传。

```bash
git clone -b main https://github.com/UserB1ank/code-audit-system
```

---

*Code Audit System 是一个开源的 Claude Code Skill，项目地址：[GitHub](https://github.com/UserB1ank/code-audit-system)*
