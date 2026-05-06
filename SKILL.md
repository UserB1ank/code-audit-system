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
2. **CVE 情报收集** (专项审计模式) - 查询历史 CVE，分析攻击模式，拟合到当前代码
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

**并行模型**: 快速预扫描（2A）完成后立即派发子代理，MainAgent 随后在后台执行深度侦察（2B），侦察结果通过增量注入（2C）实时传递给子代理。子代理审计与 MainAgent 深度侦察同时进行，总耗时由最长路径决定，而非各阶段累加。

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
   - `state/audit-logs/` - 长期审计日志目录 ⭐

**状态文件作用**:
- ✅ 记录审计进度 (阶段、子 Agent 状态、漏洞发现)
- ✅ 支持断点续传 (崩溃/暂停后恢复)
- ✅ 定期保存检查点 (`state/checkpoint-<timestamp>.json`)
- ✅ 实时日志追加 (`task-history.jsonl`)
- ✅ 长期审计追踪 (`state/audit-logs/audit-<N>-<timestamp>.md`)

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
│   ├── task-history.jsonl
│   └── audit-logs/           # ⭐ 长期审计日志
│       ├── audit-001-<timestamp>.md
│       └── audit-002-<timestamp>.md
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

### 长期审计与增量审计机制

对同一项目进行多轮审计时，系统自动记录每轮审计的版本基线和变更范围，支持增量审计和漏洞状态追踪。

#### 审计日志管理

每轮审计完成后，生成一份审计日志到 `state/audit-logs/`：

- **命名规则**: `audit-<序号>-<YYYYMMDD>-<HHMMSS>.md`
- **模板**: `templates/audit-log-template.md`
- **核心内容**: 审计日期、基准 Commit、依赖快照、变更摘要、漏洞发现、上轮漏洞追踪

#### 首次审计（全量）

```
1. git clone → 记录初始 Commit 为基准版本
2. 执行完整审计流程（Phase 1-6）
3. 生成 audit-001-<timestamp>.md，记录基准 Commit 和全部发现
4. 记录 metadata.json 中的 audit_count 和 last_audit_commit
```

#### 增量审计（第 2 轮起）

当 MainAgent 检测到项目中已存在 `state/audit-logs/` 时，自动进入增量审计模式：

```markdown
## 增量审计流程

### Step 1: 版本对比
1. 读取上轮审计日志中的基准 Commit
2. 执行 `git pull` 拉取最新代码
3. 生成变更摘要：
   - `git log --oneline <上轮commit>..HEAD` — 新 Commit 列表
   - `git diff --stat <上轮commit>..HEAD` — 变更文件统计
   - `git diff --stat <上轮commit>..HEAD -- '*.py' '*.java' '*.rs' '*.php'` — 按语言过滤

### Step 2: 图谱变更检测
使用 codebase-memory MCP 的 `detect_changes` 检测结构变更：
- `detect_changes(base_commit="<上轮commit>")` — 获取受影响的函数/类/调用链
- 对变更函数执行 `trace_path(direction="both")` — 分析上下游影响

### Step 3: 确定审计策略

| 条件 | 策略 |
|------|------|
| 变更文件 ≤ 总文件数 30% | 增量审计（聚焦变更及影响范围） |
| 变更文件 > 总文件数 30% | 全量审计 |
| 距上轮审计超过 90 天 | 全量审计 |
| 主版本号升级 | 全量审计 |

### Step 4: 增量审计范围
- **直接审计**: 新增文件和修改文件中的新代码
- **影响分析**: 变更函数的上下游调用链（从图谱获取）
- **供应链审计**: 新增/升级依赖的安全性
- **结构影响**: 图谱检测到的受影响路径
- **复用上轮**: 未变更模块标记"复用上轮结论"

### Step 5: 上轮漏洞状态追踪
对上轮发现的每个漏洞，检查当前版本状态：
- 代码未变 → 标记"未修复"
- 相关代码已修改 → 重新验证（可能已修复或变体）
- 文件已删除 → 标记"已失效"

### Step 6: 生成审计日志
使用 `templates/audit-log-template.md` 生成 `state/audit-logs/audit-<N>-<timestamp>.md`
```

#### metadata.json 增量字段

```json
{
  "project_name": "<project-name>",
  "audit_count": 3,
  "last_audit_date": "2026-04-25T10:00:00+08:00",
  "last_audit_commit": "abc1234def5678...",
  "first_audit_date": "2026-04-02T13:00:00+08:00",
  "first_audit_commit": "111aaa222bbb..."
}
```

**使用**: `templates/audit-log-template.md` 查看完整日志格式。

### 步骤 2: CVE 发现 (核心流程)

这是核心漏洞猎杀阶段。主代理协调多个子代理。

#### Phase 2.0: CVE 情报收集 (仅专项审计模式)

> ⚠️ 此阶段仅在**专项审计模式**下执行。标准模式直接进入 Phase 2.1。

**目标**: 利用 `cve-search` MCP 工具收集目标产品的历史漏洞情报，提取攻击模式，拟合到当前代码版本，生成可操作的审计指导。

**使用**: `references/cve-intelligence-guide.md` 获取详细的情报收集方法论。

##### 2.0.1: 厂商与产品识别

1. **从仓库信息提取 vendor/product**:
   - 解析 git URL 中的组织名和仓库名
   - 参照 `references/cve-intelligence-guide.md` 第 5 节常见厂商映射表
   - 准备多个变体名称 (如 `apache` / `apache_software_foundation`)

2. **确认 cve-search 中的名称**:
   - 调用 `mcp__cve-search__browse_vendors()` 确认 vendor 名称
   - 调用 `mcp__cve-search__browse_products(vendor="xxx")` 确认 product 名称
   - 如未命中，尝试模糊匹配或从 `metadata.json` 中的 framework 字段推断

##### 2.0.2: CVE 数据收集

1. **查询产品 CVE**:
   - 调用 `mcp__cve-search__search_cves(vendor="xxx", product="xxx")` 获取完整 CVE 列表
   - 记录总数和各严重级别数量

2. **获取关键 CVE 详情**:
   - 对 Critical (CVSS ≥ 9.0) 的 CVE: 逐一调用 `mcp__cve-search__get_cve(cve_id="CVE-XXXX-XXXXX")` 获取详情
   - 对 High (7.0-8.9) 的 CVE: 选择性获取详情 (优先近 3 年的)
   - 重点关注: Root Cause、Source → Sink 链、修复方式、绕过技术

3. **查询相关组件 CVE** (可选):
   - 从 `metadata.json` 中的 framework 依赖列表
   - 对主要依赖 (如 spring-framework、django、flask) 执行相同的 CVE 查询
   - 这可以发现供应链层面的已知漏洞

##### 2.0.3: 攻击模式分析

对收集到的 CVE 数据进行分析:

1. **统计漏洞类型分布** — 按 CWE 分类，识别 Top 5 高频漏洞类型
2. **提取攻击向量** — 分析 CVSS 向量字符串，确定主要攻击入口 (网络/本地/物理)
3. **识别高频组件** — 哪些组件/模块在历史 CVE 中最常被攻击
4. **提取 Source → Sink 模式** — 从 CVE 详情中抽象出可复用的攻击模式
5. **分析时间趋势** — 近年漏洞类型变化，推测未来趋势

##### 2.0.4: 模式拟合与变体推测

将历史攻击模式**拟合**到当前代码版本:

1. **补丁完整性检查**:
   - 获取关键 CVE 的修复补丁 (通过 git log 或 commit 信息)
   - 检查修复是否只覆盖了报告点，同类型其他位置是否遗漏

2. **未修复变体推测**:
   - 基于历史 CVE 的根因模式，在当前代码中搜索同类不安全代码
   - 推测修复补丁可能引入的新攻击面
   - 识别功能相似但未受补丁覆盖的代码路径

3. **攻击面拟合**:
   - 历史漏洞的 Source 入口在当前版本是否仍可达
   - 历史漏洞的 Sink 函数在当前版本是否仍存在
   - 评估每种模式在当前代码中的存在概率 (🔴 高 / 🟡 中 / 🟢 低)

##### 2.0.5: 情报报告生成与注入

1. **生成 CVE 情报报告**: `workspace/02-cve-intelligence.md`
   - 使用 `templates/cve-intelligence-report-template.md` 格式
   - 包含: 统计分析、高风险组件、攻击模式拟合、未修复变体推测

2. **更新工作背景文档**: 将情报摘要注入 `workspace/00-work-background.md`
   - 使用 `templates/work-background-template.md` 中的 CVE 情报章节

3. **注入子代理背景文档**: 为每个子代理的 `background.md` 增加专项指导
   - 使用 `templates/subagent-background-template.md` 中的 CVE 情报章节
   - 包含: 该模块相关的历史 CVE、推测的未修复变体、搜索策略
   - 优先级调整建议

4. **更新审计状态**:
   ```json
   {
     "audit_mode": "specialized",
     "cve_intelligence": {
       "vendor": "apache",
       "product": "tomcat",
       "total_known_cves": 245,
       "critical_count": 18,
       "high_count": 67,
       "intelligence_report": "workspace/02-cve-intelligence.md",
       "predicted_variants": 5,
       "high_probability_variants": 2
     }
   }
   ```

**专项模式下子代理行为差异**:
- 子代理在 Phase 1 (代码地图绘制) 中，**优先搜索历史 CVE 的同类代码模式**
- 子代理在 Phase 2 (数据流追踪) 中，**优先追踪推测的未修复变体**
- 子代理在 Phase 3 (安全控制分析) 中，**优先分析历史修复补丁的完整性**
- 子代理在 Phase 4 (CVE 发现与报告) 中，需标注发现的漏洞是否为历史 CVE 的变体

#### Phase 2A: 快速预扫描与并行派发 (5 分钟内完成, 与 2B/2C 衔接)

**核心目标**: 用最短时间获取派发子代理所需的最小信息，在深度侦察完成前就启动子代理审计。

##### 2A.1: 快速语言/框架识别 (30 秒)

```bash
# 统计文件扩展名分布
find source/ -type f -name "*.java" | wc -l
find source/ -type f -name "*.py" | wc -l
find source/ -type f -name "*.rs" | wc -l
find source/ -type f -name "*.php" | wc -l
find source/ -type f -name "*.go" | wc -l
find source/ -type f -name "*.js" -o -name "*.ts" | wc -l
```

解析关键包文件（存在则读取）:
- `package.json` → 项目名、框架、Node.js 版本
- `pom.xml` / `build.gradle` → Java 框架、依赖
- `requirements.txt` / `setup.py` / `pyproject.toml` → Python 框架
- `Cargo.toml` → Rust 依赖
- `go.mod` → Go 模块
- `composer.json` → PHP 框架

**无需深度分析框架版本和完整依赖关系** — 这是 Phase 2B 的工作。

##### 2A.2: 快速目录结构与模块划分 (1-2 分钟)

```bash
# 列出顶层目录结构
ls -la source/

# 统计各子目录文件数
find source/ -maxdepth 3 -type f | cut -d/ -f2- | sort | uniq -c | sort -rn | head -30
```

基于目录名和 `references/module-detection.md` 快速匹配项目类型:
- 有 `controllers/` + `models/` + `views/` → MVC Web 应用
- 有 `services/` 下多个子目录 → 微服务
- 有 `cmd/` + `internal/` + `pkg/` → Go 项目
- 有 `src/main/java/` + `src/main/resources/` → Java Maven 项目

**粗略模块划分**（仅基于目录边界，不深入依赖分析）:
- 每个顶层目录或核心子目录 = 一个模块
- 模块依赖关系暂时标记为"未知"，在 2B 中精确分析

##### 2A.3: 快速攻击面草图 (1-2 分钟)

grep 关键模式获取入口点和危险函数的初步分布:

```bash
# HTTP 端点入口
grep -rn "@RequestMapping\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" source/ | head -50
grep -rn "app\.\(get\|post\|put\|delete\|patch\)(" source/ | head -50
grep -rn "Route::\|@route\|\$_GET\|\$_POST\|\$_REQUEST" source/ | head -50
grep -rn "#\[\(get\|post\|put\|delete\)\]" source/ | head -50

# 危险 Sink
grep -rn "\.execute\(\|\.executeQuery\(\|\.executeUpdate\(" source/ | head -30
grep -rn "system\(\|exec\(\|popen\(\|subprocess\|Runtime\.exec\|ProcessBuilder" source/ | head -30
grep -rn "pickle\.\|yaml\.load\(\|unserialize\(\|json\.parse\|readObject" source/ | head -30
grep -rn "\.read\(\)\|\.write\(\)\|\.open\(\|FileInputStream\|FileOutputStream" source/ | head -30
```

**不追踪调用链，仅记录位置** — 完整追踪是子代理的工作。

##### 2A.4: 创建草稿文档并立即派发 (1 分钟)

1. **创建工作背景文档草稿** `workspace/00-work-background.md`:
   - 在文档头部标注 `> **状态: DRAFT v1** — 快速预扫描结果，深度侦察完成后将更新为 FINAL`
   - 填入快速识别的语言、框架、应用类型
   - 填入攻击面草图（入口点和 Sink 列表，标注为"初步扫描"）
   - 使用 `templates/work-background-template.md` 格式

2. **创建模块地图草稿** `workspace/01-module-map.md`:
   - 在文档头部标注 `> **状态: DRAFT v1** — 快速模块划分结果`
   - 填入粗略模块列表、文件映射
   - 模块依赖标记为"待分析"
   - 使用 `templates/module-info-template.md` 格式

3. **为每个模块创建子代理工作区**:
   ```
   workspace/agent-<module>/
   ├── background.md   # DRAFT 版本
   ├── skill.md        # 审计指令
   ├── execution.log   # 执行日志
   └── report.md       # 待子代理填充
   ```

4. **✨ 立即并行派发所有无依赖模块的子代理**
   - 子代理启动后必须首先读取 `background.md` 和 `skill.md`
   - 子代理了解 current `background.md` 为 DRAFT 版本，深度侦察完成后 MainAgent 将更新

##### 2A.5: 更新审计状态

```json
{
  "phase": "phase_2a_prescan",
  "phases": {
    "phase_2a_prescan": {
      "status": "completed",
      "started_at": "2026-05-06T10:00:00+08:00",
      "completed_at": "2026-05-06T10:05:00+08:00",
      "outputs": {
        "work_background_draft": "workspace/00-work-background.md",
        "module_map_draft": "workspace/01-module-map.md"
      }
    },
    "phase_2b_deep_recon": {
      "status": "in_progress"
    }
  },
  "subagents": [
    {
      "id": "agent-<module>",
      "background_version": "draft",
      "status": "running",
      "started_at": "2026-05-06T10:05:00+08:00"
    }
  ]
}
```

#### Phase 2B: MainAgent 深度侦察 (与子代理并行执行)

**⚠️ 关键**: Phase 2A 子代理派发后**立即开始**此阶段，与子代理审计并行进行。

**目标**: 对项目进行深度技术侦察，产出精确的工作背景和模块划分，供 Phase 2C 增量注入子代理。

##### 2B.1: 代码知识图谱构建（codebase-memory MCP）

在子代理审计的同时，**使用 codebase-memory MCP 将目标仓库构建为代码知识图谱**:

### Step 1: 索引目标仓库
调用 `index_repository` 将源码目录构建为图数据库：
- 仓库路径: `code-audit-projects/<name>/source/`
- 索引完成后，所有函数、类、调用关系、HTTP 端点将以图结构存储

### Step 2: 架构概览
调用 `get_architecture` 获取项目整体架构：
- 模块划分、入口点、核心数据流
- 自动识别的框架和设计模式

### Step 3: 攻击面映射（基于图谱）
- `search_graph(relationship="HTTP_CALLS")` — 发现所有 HTTP 端点（API 入口）
- `search_graph(min_degree=10, relationship="CALLS", direction="inbound")` — 发现高扇入函数（被大量调用的核心逻辑）
- `search_graph(max_degree=0, exclude_entry_points=true)` — 发现死代码（可能包含遗留危险逻辑）
- `trace_path(function_name="<handler>", direction="outbound", depth=5)` — 从入口追踪完整调用链

### Step 4: 危险 Sink 定位
- `search_graph(name_pattern=".*execute.*")` — 查找 SQL 执行函数
- `search_graph(name_pattern=".*system.*|.*popen.*|.*subprocess.*")` — 查找命令执行
- `search_graph(name_pattern=".*open.*|.*read.*|.*write.*")` — 查找文件操作
- `trace_path(direction="inbound")` 对每个 Sink 反向追踪调用来源

**何时使用图谱 vs 传统 grep**:
- **图谱优先**: 调用链追踪、依赖分析、架构理解、影响范围评估
- **grep 辅助**: 文本模式搜索、特定字符串查找、配置文件审查

##### 2B.2: 深度攻击面映射

基于图谱和代码阅读，产出精确的攻击面分析：

- **详细 Source 列表**: 每个入口函数的完整签名、参数类型、认证状态
- **详细 Sink 列表**: 每个危险函数的调用上下文、防护措施
- **信任边界分析**: 内部 API vs 外部 API、认证域边界

##### 2B.3: 精确模块依赖分析

- `get_architecture` 获取自动识别的模块结构
- `query_graph` 使用 Cypher 查询跨模块调用关系：
  ```
  MATCH (a)-[r:CALLS]->(b) WHERE a.file_path STARTS WITH '/module-a/' AND b.file_path STARTS WITH '/module-b/' RETURN a.name, b.name, count(r) ORDER BY count(r) DESC LIMIT 20
  ```
- 基于图谱的实际调用依赖（而非仅目录结构）更新模块划分
- 更新模块依赖图

##### 2B.4: 完善文档为 FINAL 版本

将 Phase 2A 创建的 DRAFT 文档升级为 FINAL:
- 更新 `workspace/00-work-background.md`：状态改为 FINAL，填入深度分析结果
- 更新 `workspace/01-module-map.md`：状态改为 FINAL，填入精确模块边界和依赖

**使用**: `references/module-detection.md` 获取按项目类型的模块结构模板。

#### Phase 2C: 增量情报注入 (深度侦察完成后立即执行)

**目标**: 将 Phase 2B 深度侦察的发现增量传递给正在运行的子代理。

##### 2C.1: 更新子代理 background.md

为每个正在运行的子代理更新其 `workspace/agent-<module>/background.md`:

1. 在文件头部将 `DRAFT v1` 改为 `FINAL`
2. 追加新章节 `## 🔄 深度侦察补充情报`:
   ```markdown
   ## 🔄 深度侦察补充情报 (注入时间: <timestamp>)

   ### 新增攻击面信息
   - [2B 深度侦察中发现的该模块新攻击面]

   ### 精确模块依赖
   - [该模块与其他模块的实际调用关系]

   ### 图谱追踪结果
   - [该模块关键 Source→Sink 路径的图谱追踪结果]

   ### 高风险区域补充
   - [2B 中新识别的高风险代码区域]
   ```

3. 如有必要，调整审计优先级和重点关注区域

##### 2C.2: 更新子代理 skill.md (如需要)

如果深度侦察发现新的漏洞类型值得关注，追加到 skill.md：
```markdown
## 🔄 深度侦察补充指令 (注入时间: <timestamp>)

基于代码图谱分析，新增以下搜索目标：
- [新的高价值 Sink]
- [新发现的攻击入口]
- [图谱识别的关键调用路径]
```

##### 2C.3: 记录注入事件

```json
{
  "event": "intelligence_injected",
  "timestamp": "2026-05-06T10:20:00+08:00",
  "target_agents": ["agent-services", "agent-connector", "agent-viewer"],
  "injection_type": "deep_recon_results",
  "new_findings": ["3 个新攻击面", "2 条跨模块调用路径"]
}
```

##### 2C.4: 子代理接收更新

子代理在审计过程中应定期检查 background.md 是否有更新（见子代理 skill 模板中的增量更新检查流程）。发现 FINAL 版本后：
- 审阅深度侦察补充情报章节
- 如发现新的攻击面或高风险区域，将其纳入 Phase 2 深入分析
- 调整审计优先级

#### Phase 2.3: 子代理审计执行 (与 2B 并行)

子代理在 Phase 2A 被派发后立即开始审计，与 MainAgent 的深度侦察（2B）并行执行。

**⚠️ 目录结构要求**: 必须使用标准工作区布局

**MainAgent 必须为每个子 Agent 创建独立背景文档**

工作区结构（Phase 2A 已创建）:

```
workspace/
├── 00-work-background.md        # ✅ MainAgent 创建 (DRAFT → Phase 2B 升级为 FINAL)
├── 01-module-map.md             # ✅ MainAgent 创建 (DRAFT → Phase 2B 升级为 FINAL)
├── agent-<module-1>/            # ✅ 子 Agent 1 工作区
│   ├── background.md            # MainAgent 创建 (DRAFT → Phase 2C 升级为 FINAL)
│   ├── skill.md                 # MainAgent 创建 (审计指令，Phase 2C 可追加)
│   ├── execution.log            # ⭐ 子 Agent 执行日志 (自动保存)
│   └── report.md                # 子 Agent 输出 (CVE 报告)
├── agent-<module-2>/            # ✅ 子 Agent 2 工作区
│   ├── background.md
│   ├── skill.md
│   ├── execution.log
│   └── report.md
└── agent-<module-N>/            # ✅ 子 Agent N 工作区
    ├── background.md
    ├── skill.md
    ├── execution.log
    └── report.md
```

**并行调度策略**:
- Phase 2A 完成后，所有无依赖模块立即并行派发
- 有依赖的模块按依赖顺序派发（但仍比原串行流程更早启动）
- MainAgent 在 Phase 2B 深度侦察期间不阻塞子代理
- Phase 2C 增量注入时子代理仍在运行，无缝接收新情报

**子代理增量更新检查流程** ⭐:

子代理在审计过程中必须:
1. **Phase 0 完成后**: 检查 `background.md` 是否从 DRAFT 更新为 FINAL
2. **Phase 2 开始前**: 再次检查 `background.md` 是否有新内容
3. **发现 FINAL 版本时**: 审阅 `## 🔄 深度侦察补充情报` 章节，将新发现纳入审计范围

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
- **⭐ 增量更新检查**: Phase 0 完成后和 Phase 2 开始前，检查 background.md 是否从 DRAFT 更新为 FINAL，如有更新则审阅补充情报并调整审计重点
- **⭐ 使用 codebase-memory MCP 图谱工具辅助审计**（见下方图谱增强审计流程）

**⭐ 图谱增强审计流程（codebase-memory MCP）**:

子代理在审计过程中，应充分利用代码知识图谱进行结构化分析。图谱在 Phase 2.1 已由 MainAgent 构建完成，子代理可直接查询：

```markdown
## Phase 1: 代码地图绘制 — 图谱增强

### 1.1 模块结构概览
- `get_architecture` — 获取模块整体架构和自动识别的设计模式
- `get_graph_schema` — 了解该项目的节点/边类型

### 1.2 入口点与 Sink 发现
- `search_graph(label="Function", name_pattern=".*<module-pattern>.*")` — 发现模块内所有函数
- `search_graph(relationship="HTTP_CALLS")` — 发现 HTTP 端点（攻击入口 Source）
- `search_graph(name_pattern=".*execute.*|.*query.*|.*system.*|.*popen.*")` — 发现危险 Sink
- `search_code(query="<dangerous_function>")` — 文本搜索补充图谱未覆盖的模式

## Phase 2: Source → Sink 追踪 — 图谱核心价值

### 2.1 正向追踪（Source → Sink）
从用户输入入口追踪到危险操作：
```
trace_path(function_name="<handler>", direction="outbound", depth=5, risk_labels=true)
```
- `risk_labels=true` 自动标注路径中的高风险节点

### 2.2 反向追踪（Sink → Source）
从危险函数反向追踪所有调用来源：
```
trace_path(function_name="<dangerous_sink>", direction="inbound", depth=5)
```
- 快速判断是否存在用户可控数据到达 Sink 的路径

### 2.3 完整调用上下文
```
trace_path(function_name="<target>", direction="both", depth=3)
```
- 同时获取调用者和被调用者，快速定位验证/过滤层

### 2.4 跨模块调用链
```cypher
MATCH path = (src)-[:CALLS*1..6]->(sink)
WHERE src.name =~ '.*<handler>.*' AND sink.name =~ '.*execute.*'
RETURN path
```

## Phase 3: 安全控制分析 — 图谱辅助
- `trace_path(direction="outbound")` 检查路径上是否有验证/过滤节点
- 对比有/无安全控制的路径差异
- `get_code_snippet(qualified_name="<validator>")` 快速查看验证函数实现

## Phase 4: 报告阶段
调用链记录应包含图谱 trace 的完整结果：
- 调用深度、中间节点、风险标注
- 每个节点的文件路径和行号（从 `get_code_snippet` 获取）
```

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
> "是否要在部署的环境中验证 POC? 每验证一个漏洞将生成一份独立验证报告，最终汇总为 CVE 提交总报告。"

如果用户确认:

1. **部署目标** (未在步骤 3 中完成)
2. **逐个漏洞进行验证** — 对每个 CVE 级别漏洞:

   a. **运行 POC** 于部署的 Docker/本地环境
   b. **记录结果**:
      - 成功/失败
      - 输出/证据
      - 利用耗时

   c. **立即编写单漏洞验证报告** (小报告):
      - 路径: `reports/vulnerability-<id>-verification.md`
      - 格式: 参考 `templates/per-vulnerability-verification-report-template.md`
      - 内容必须包含:
        - 漏洞标题、一句话概述
        - 严重性评估 (CVSS、CWE)
        - 受影响组件 (核心组件 + 关联组件)
        - 影响 (具体攻击后果)
        - 技术复现步骤 (部署、确认、利用命令及输出)
        - 漏洞根因 (带行号的代码片段 + 问题分析)
        - 展示的影响 (信任边界穿越论证、范围检查)
        - 环境 (版本、Commit、OS、权限等)
        - 补救建议 (含修复代码示例)
      - 若验证失败，报告中需包含失败分析和可能原因

   d. **更新审计状态**:
      ```json
      {
        "vulnerabilities": [
          {
            "id": "VULN-XXX",
            "verification_report": "reports/vulnerability-XXX-verification.md",
            "verification_status": "verified|failed|skipped",
            "verification_date": "2026-04-22T10:00:00Z"
          }
        ]
      }
      ```

3. **(可选) 生成验证汇总报告** `reports/verification-report.md`:
   - 在所有单漏洞验证报告完成后，可选择生成汇总表
   - 仅作为索引，详细内容指向各单漏洞验证报告

**关键规则**:
- **每验证一个漏洞必须立即写一份小报告**，禁止等全部验证完成后再统一写
- 小报告是 CVE 提交总报告的核心素材，必须详实、可复现
- 使用中文撰写，保留技术术语英文

### 步骤 6: CVE 提交报告

主代理将所有发现汇总为 **CVE 就绪提交包**:

1. **收集所有报告**:
   - 子代理的独立漏洞报告 (仅 CVE 级别)
   - 武器化 POC 脚本
   - POC 验证结果 (如已验证)

2. **生成 CVE 提交总报告** `reports/cve-submission-report.md`:

   总报告汇总所有已验证的单漏洞报告，格式如下：

```markdown
# CVE Submission Report — [产品名]

## Project Overview
- **Product**: [产品名称]
- **Repository**: <git-url>
- **Vendor**: [厂商名称]
- **Audit Date**: <date>
- **Commit**: <commit-hash>
- **Auditor**: [你的名称/代号]

## Executive Summary
- **CVE-Worthy Vulnerabilities**: <count> (CVSS ≥ 7.0)
- **Critical (CVSS 9.0-10.0)**: <count>
- **High (CVSS 7.0-8.9)**: <count>
- **Total with Complete Exploit Chains**: <count>
- **POC-Ready**: <count>

## CVE Candidates

| ID | Type | CVSS | CWE | Location | POC | Status |
|----|------|------|-----|----------|-----|--------|
| CVE-XXXX-XXXXX | [漏洞类型] | [评分] | CWE-XXX | `file.py:行号` | Yes | Ready |

---

## Detailed CVE Reports

### CVE-XXXX-XXXXX: [漏洞名称]

**Severity**: [严重级别] (CVSS [评分])
**Vector**: [CVSS向量字符串]
**CWE**: CWE-XXX ([CWE名称])
**Affected Versions**: [版本范围]

**Location**: `[文件路径:行号范围]`

**Root Cause**: [根本缺陷的详细说明，具体指出缺少什么验证]

**Call Chain**:
```
[1] Source: [函数]() 位于 [文件:行号]
    ↓ [数据流描述]
[2] Process: [函数]() 位于 [文件:行号]
    ↓ [数据流描述]
[3] Sink: [函数]() 位于 [文件:行号]
    ↓ [最终结果]
```

**Impact**: [攻击者可达成的具体目标，如系统完全控制、敏感信息泄露等]

**POC**:
```bash
[可执行的 POC 命令或脚本路径]
```

**Verification**: ✅ 成功 (详见 `reports/vulnerability-XXX-verification.md`)

---

### CVE-XXXX-XXXXX: [下一个漏洞]
...

## Maximum Impact Exploit Chain

An attacker can chain multiple vulnerabilities for complete system compromise:

```
1. [步骤1]: [利用某个漏洞进行侦察/初始访问]
2. [步骤2]: [利用某个漏洞提升权限/窃取凭证]
3. [步骤3]: [利用某个漏洞实现 RCE/持久化]
4. [步骤4]: [利用某个漏洞横向移动/数据窃取]
```

**Total time to full compromise**: <时间> with default configuration.

## Submission Targets

| CNA | URL | Priority |
|-----|-----|----------|
| MITRE | https://cveform.mitre.org/ | Primary |
| GitHub Security Advisories | https://github.com/[vendor]/[repo]/security/advisories | High |
| Vendor PSIRT | [vendor-specific] | Medium |

## Submission Checklist

For each CVE candidate:
- [ ] Technical writeup complete (引用单漏洞验证报告)
- [ ] POC weaponized and tested
- [ ] CVSS v3.1 scoring calculated
- [ ] Affected versions confirmed
- [ ] Vendor notification (如协调披露)
- [ ] Video demonstration (optional)

## Appendix
- Individual verification reports: `reports/vulnerability-*-verification.md`
- Weaponized POCs: `pocs/`
- Background: `workspace/00-work-background.md`
- Module map: `workspace/01-module-map.md`
```

**总报告生成规则**:
- 总报告中的每个漏洞详细描述必须引用对应的单漏洞验证报告 (`reports/vulnerability-<id>-verification.md`)
- 总报告侧重于**汇总和提交就绪状态**，技术细节以单漏洞验证报告为准
- 必须包含 **Maximum Impact Exploit Chain** 章节，展示漏洞组合利用的最大影响
- 使用中文撰写，保留技术术语英文

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
| Python | `references/python-guide.md` | SQL 注入、命令注入、路径遍历、反序列化（pickle/yaml）、SSTI、XXE、SSRF、开放重定向、信息泄露、弱加密、权限绕过、文件上传 |
| PHP | `references/php-guide.md` | SQL 注入、命令注入、文件包含、XSS、反序列化、路径穿越、SSRF、认证问题 |
| Java | `references/java-guide.md` | SQL 注入、命令注入、XXE、反序列化、路径穿越、SSRF、SSTI、JNDI 注入、Spring 特定问题 |
| Rust | `references/rust-guide.md` | Unsoundness（unsafe 契约/型变/Send+Sync 误实现/内联汇编）、逻辑漏洞、并发竞态、资源耗尽（OOM/DoS）、整数与缓冲区、标准库 unsafe API 误用、依赖供应链 |

**重要**: 语言指南包含每种漏洞类型的 Source → Sink 模式。子 Agent 在审计该语言代码时必须查阅相关语言指南。

## 相关模板和参考

- `templates/vulnerability-report-template.md` - 漏洞报告格式 (中文)
- `templates/per-vulnerability-verification-report-template.md` - 单漏洞验证报告格式 (中文，每验证一个漏洞生成一份)
- `templates/summary-report-template.md` - 总结报告格式 (中文)
- `templates/verification-report-template.md` - 验证汇总报告格式 (中文，可选索引)
- `templates/poc-template.py` - POC 脚本结构
- `templates/subagent-skill-template.md` - 子代理技能模板
- `templates/subagent-background-template.md` - 子代理背景文档模板
- `templates/work-background-template.md` - 工作背景模板 (中文)
- `templates/module-info-template.md` - 模块信息模板 (中文)
- `templates/cve-intelligence-report-template.md` - CVE 情报分析报告模板 (专项审计模式)
- `templates/audit-log-template.md` - 长期审计日志模板 (增量审计，记录版本基线与变更对比)
- `references/module-detection.md` - 按项目类型的模块检测
- `references/project-structure.md` - 项目存储结构
- `references/python-guide.md` - Python 漏洞模式 (Source → Sink)
- `references/php-guide.md` - PHP 漏洞模式 (Source → Sink)
- `references/java-guide.md` - Java 漏洞模式 (Source → Sink)
- `references/rust-guide.md` - Rust 漏洞模式 (unsafe 契约、并发竞态、资源耗尽、供应链审计)
- `references/cve-intelligence-guide.md` - CVE 情报收集与分析指南 (专项审计模式)
- **codebase-memory MCP** - 代码知识图谱工具，用于结构化代码理解、调用链追踪、架构分析 (审计流程各阶段均可使用)
