# 代码审计系统 — 多智能体 CVE 发现引擎

**以 CVE 提交为目标的多智能体代码审计系统**，以 Claude Code Skill 形式实现。通过并行子代理（SubAgent）对 Git 仓库进行可利用漏洞发现，编写武器化 POC，在真实部署环境中验证，并生成 CVE 就绪报告。

> **核心理念**：只报告可实际利用的漏洞。目标是提交 CVE，而非让代码变得更安全。

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                     主代理 (MainAgent)                     │
│  · 快速预扫描 → 立即派发子代理                              │
│  · 深度侦察（与子代理并行）                                  │
│  · 增量情报注入子代理                                       │
│  · 工作区和状态管理                                         │
│  · 最终报告汇总                                            │
└──────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  子代理 1     │  │  子代理 2     │  │  子代理 N     │
│  模块 A      │  │  模块 B      │  │  模块 N      │
│              │  │              │  │              │
│  技术侦察     │  │  技术侦察     │  │  技术侦察     │
│  Source→Sink │  │  Source→Sink │  │  Source→Sink │
│  可利用性评估 │  │  可利用性评估 │  │  可利用性评估 │
│  CVE 报告    │  │  CVE 报告    │  │  CVE 报告    │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 核心特性

- **并行子代理审计** — 模块同时审计，非串行排队
- **双审计模式** — 标准模式（直接代码审计）和专项审计模式（基于历史 CVE 定向猎杀）
- **图谱增强侦察** — `codebase-memory` MCP 构建代码知识图谱，实现 Source→Sink 跨模块追踪
- **增量情报注入** — MainAgent 在审计进行中将深度侦察发现实时推送给子代理
- **实际 POC 验证** — 通过 Docker 部署目标，对真实运行的服务验证漏洞
- **严格可利用性过滤** — 丢弃理论性/被阻断问题，仅报告可验证的漏洞
- **断点续传** — 状态文件支持崩溃恢复和进度重载

## 工作流程

```
标准模式：   初始化 → 预扫描 → 子代理并行审计 → POC → 验证 → 报告
                                ↗ MainAgent 并行深度侦察 ↗

专项审计：   初始化 → CVE情报 → 预扫描 → 子代理并行审计 → POC → 验证 → 报告
                                            ↗ MainAgent 并行深度侦察 ↗
```

### Phase 1 — 项目初始化
克隆目标仓库到 `source/`，创建 `metadata.json`、状态文件和工作区骨架。

### Phase 2 — CVE 发现（核心）
- **2A（快速预扫描）**：语言/框架识别、粗略模块划分、攻击面草图。完成后立即并行派发所有子代理。
- **2B（深度侦察）**：MainAgent 通过 `codebase-memory` MCP 构建代码知识图谱，执行深度攻击面映射和模块依赖分析 — 与子代理审计完全并行。
- **2C（增量注入）**：深度侦察发现实时写入子代理的背景文档，子代理据此调整审计重点。
- **2.3（子代理审计）**：每个子代理执行四阶段审计（侦察 → 深度追踪 → 可利用性评估 → CVE 报告）。
- **2.4（漏洞报告）**：生成 CVE 就绪报告，含完整 Source→Sink 调用链、CVSS 评分和可利用性判定。

### Phase 3 — 环境部署（可选）
通过 Docker 部署目标应用，用于 POC 验证。

### Phase 4 — POC 编写
为 CVE 级漏洞编写 Python 武器化利用脚本。

### Phase 5 — 验证测试（可选）
在部署环境中运行 POC 验证漏洞。**不接受纯源码分析结论** — 必须在运行实例上验证。无法验证则如实标记为未验证。

### Phase 6 — 总结报告
汇总所有验证通过的发现，生成 CVE 提交包。

## 审计模式

| 模式 | 适用场景 | 额外步骤 | 优势 |
|------|----------|----------|------|
| **标准模式** | 首次审计、内部项目、无 CVE 历史 | 无 | 流程简洁，快速启动 |
| **专项审计模式** | 知名开源产品、有 CVE 历史、已知厂商 | Phase 2.0：通过 `cve-search` 收集 CVE 情报 | 基于历史漏洞模式定向猎杀，发现率更高 |

专项审计模式对知名开源组织（Apache、Spring、WordPress 等）自动触发，用户也可显式指定。

## 使用示例

调用方式：提供 Git 仓库 URL 即可启动审计：

```
/code-audit-system https://github.com/InsForge/InsForge.git 专项审计
```

### 完整审计流程

```bash
# 1. 项目初始化 — 克隆目标到隔离工作区
mkdir -p code-audit-projects/InsForge/{source,state,workspace,pocs,reports,docker}
git clone https://github.com/InsForge/InsForge.git code-audit-projects/InsForge/source/

# 2. CVE 情报收集（专项审计模式）— 查询历史漏洞
#    通过 cve-search MCP 收集目标产品的历史 CVE 数据，
#    分析攻击模式，拟合到当前代码版本

# 3. 快速预扫描 + 并行派发子代理
#    MainAgent 识别技术栈、划分模块，
#    立即并行启动所有子代理

# 4. 深度侦察（与子代理并行）
#    MainAgent 通过 codebase-memory MCP 构建代码知识图谱，
#    执行 Source→Sink 深度映射，增量注入子代理

# 5. 对确认的可利用漏洞编写 POC 脚本

# 6. 环境部署与 POC 验证
#    在 POC 验证机上通过 Docker 部署目标环境，
#    从分析机发起 POC 请求验证漏洞：
#
#    ssh verifier@<poc-host> "sudo docker compose -f /path/to/docker-compose.yml up -d"
#    python poc-001-rce.py --target http://<poc-host>:8080
#
#    源码分析不能替代实际验证 — 必须 POC 在运行环境中确认生效。
#    无法部署或无法验证的漏洞，如实标记为"未验证"。

# 7. 针对验证通过的漏洞生成 CVE 提交报告
```

### 验证环境

系统支持在专用 POC 验证机上部署目标：

- **部署方式**：基于 Docker，通过 `docker compose` 在验证机上启动目标服务
- **连接方式**：分析机通过 SSH 远程执行部署命令，通过 HTTP 发起 POC 请求
- **权限配置**：验证机配置免密码 `sudo` 用于容器生命周期管理
- **验证原则**：仅运行时 POC 验证通过的漏洞才纳入最终 CVE 报告；纯静态分析发现无法验证的，标记为未验证

> **注意**：验证机凭据和网络配置按部署环境独立设置，不存储在本仓库中。

## CVE 提交标准

| 标准 | 要求 |
|------|------|
| CVSS 分数 | ≥ 7.0（高危/严重） |
| 可利用性 | 必须有完整 Source→Sink 调用链 |
| POC | 必须可武器化且功能正常 |
| 影响范围 | 影响真实用户（非本地/测试环境） |
| 版本 | 明确指出受影响版本 |

## 项目目录结构

```
code-audit-projects/<项目名>/
├── source/                  # 克隆的源代码（git clone 必须到此目录）
├── state/                   # 审计状态和任务历史（断点续传）
│   ├── audit-state.json
│   └── task-history.jsonl
├── workspace/               # 子代理工作区
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   └── agent-<模块名>/
│       ├── background.md
│       ├── skill.md
│       └── report.md
├── pocs/                    # 武器化 POC 脚本
├── reports/                 # CVE 提交报告
├── docker/                  # Docker 部署配置
└── metadata.json
```

## MCP 集成

| MCP 服务 | 用途 |
|----------|------|
| `codebase-memory` | 构建代码知识图谱，实现跨模块 Source→Sink 追踪 |
| `cve-search` | 查询历史 CVE 数据，分析攻击模式（专项审计模式） |

## 语言特定漏洞指南

| 语言 | 覆盖漏洞类型 |
|------|-------------|
| Python | SQL 注入、命令注入、路径遍历、反序列化、SSTI、XXE、SSRF |
| PHP | SQL 注入、命令注入、文件包含、XSS、反序列化、路径穿越、SSRF |
| Java | SQL 注入、命令注入、XXE、反序列化、路径穿越、SSRF、SSTI、JNDI 注入 |
| Rust | Unsoundness、并发竞态、资源耗尽、整数/缓冲区问题、依赖供应链 |

## 交付物

1. **CVE 提交报告** — 汇总报告，含执行摘要、CVE 候选表和逐漏洞详细分析
2. **独立漏洞报告** — 含 Source→Sink 调用链、CVSS 向量和证据代码片段
3. **武器化 POC 脚本** — 自包含的 Python 利用脚本
4. **验证报告** — 逐漏洞的运行时验证结果

## 文件地图

```
SKILL.md                         # 核心 Skill 定义 — 完整审计工作流
references/                      # 语言指南和操作参考
  ├── python-guide.md            # Python 漏洞模式
  ├── php-guide.md               # PHP 漏洞模式
  ├── java-guide.md              # Java 漏洞模式
  ├── rust-guide.md              # Rust 漏洞模式
  ├── module-detection.md        # 按项目类型的模块检测
  ├── project-structure.md       # 标准目录布局
  ├── parallel-audit-workflow.md # Phase 2A/2B/2C 并行审计详细步骤
  ├── subagent-guide.md          # 子代理背景文档创建指南
  ├── phase1-project-init.md     # 项目初始化详细步骤
  ├── phase2-cve-intelligence.md # CVE 情报收集（专项审计模式）
  ├── phases-3to6.md             # 部署、POC、验证、报告
  ├── cve-intelligence-guide.md  # CVE 情报收集方法论
  └── operations.md              # 错误处理、提醒机制、交付物
templates/                       # 输出模板
  ├── vulnerability-report-template.md
  ├── subagent-skill-template.md
  ├── subagent-background-template.md
  ├── summary-report-template.md
  ├── verification-report-template.md
  ├── poc-template.py
  └── ...
state/                           # 状态格式定义
  └── audit-state-schema.md
evals/                           # 触发评估测试用例
  ├── evals.json
  └── trigger-evals.json
```

## 运行要求

- [Claude Code](https://claude.ai/code) CLI
- Git
- Docker（用于 POC 验证）
- Python 3.x（用于 POC 执行）
- MCP 服务：`codebase-memory`、`cve-search`（专项审计模式可选）

## 许可证

本项目为 Claude Code 的 Skill 定义。使用风险自负。系统仅限授权安全测试和漏洞研究用途。
