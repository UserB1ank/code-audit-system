# Phase 2A/2B/2C: 并行审计工作流详细步骤

> 本文档包含 Phase 2 并行审计模型的详细操作步骤：快速预扫描（2A）、深度侦察（2B）、增量情报注入（2C）。从 SKILL.md 中提取。

---

## Phase 2A: 快速预扫描与并行派发 (5 分钟内完成)

**核心目标**: 用最短时间获取派发子代理所需的最小信息，在深度侦察完成前就启动子代理审计。

### 2A.1: 快速语言/框架识别 (30 秒)

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

### 2A.2: 快速目录结构与模块划分 (1-2 分钟)

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

### 2A.3: 快速攻击面草图 (1-2 分钟)

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

### 2A.4: 创建草稿文档并立即派发 (1 分钟)

1. **创建工作背景文档草稿** `workspace/00-work-background.md`:
   - 在文档头部标注 `> **状态: DRAFT v1**`
   - 填入快速识别的语言、框架、应用类型
   - 填入攻击面草图（入口点和 Sink 列表，标注为"初步扫描"）
   - 使用 `templates/work-background-template.md` 格式

2. **创建模块地图草稿** `workspace/01-module-map.md`:
   - 在文档头部标注 `> **状态: DRAFT v1**`
   - 填入粗略模块列表、文件映射
   - 模块依赖标记为"待分析"

3. **为每个模块创建子代理工作区**:
   ```
   workspace/agent-<module>/
   ├── background.md   # DRAFT v1 版本，从 templates/subagent-background-template.md 生成
   ├── skill.md        # 审计指令，从 templates/subagent-skill-template.md 生成
   ├── execution.log   # 执行日志，初始化为空或使用 templates/execution-log-template.md
   └── report.md       # 占位报告，待子代理填充
   ```
   - `background.md` 头部必须标注 `> **状态: DRAFT v1**`
   - `skill.md` 必须包含目标源码绝对路径、报告输出绝对路径、背景文档绝对路径和专项技能绝对路径
   - `report.md` 至少包含 `# <module> CVE 审计报告` 和 `> 状态: 待子代理填充`

4. **立即并行派发所有无依赖模块的子代理**
   - "派发"不是写一句计划，必须实际调用当前环境可用的子代理创建工具
   - 专项审计模式下，先把 `workspace/02-cve-intelligence.md` 中该模块的情报写入 `background.md`，再派发；派发后将 `cve_intelligence.subagent_injection_status` 更新为 `injected`
   - 如果运行环境提供 `multi_agent_v1.spawn_agent`，每个模块调用一次，并在任务描述中要求子代理首先读取自己的 `background.md` 和 `skill.md`
   - 如果使用其他平台，调用等价的 SubAgent/Task/Worker 创建工具
   - 如果当前环境没有子代理工具，Phase 2A 必须标记为 `failed` 或 `blocked`，向用户说明无法继续多代理审计，不能进入 Phase 2B 或后续阶段
   - 子代理启动后必须首先读取 `background.md` 和 `skill.md`
   - 子代理了解 background.md 为 DRAFT 版本，深度侦察完成后 MainAgent 将更新

5. **Phase 2A 完成前自检 (硬闸)**
   ```bash
   test -f workspace/00-work-background.md
   test -f workspace/01-module-map.md
   test -d workspace/agent-<module>
   test -f workspace/agent-<module>/background.md
   test -f workspace/agent-<module>/skill.md
   test -f workspace/agent-<module>/execution.log
   test -f workspace/agent-<module>/report.md
   ```

   对每个模块重复上述检查。随后在写入 `phase_2a_prescan.status = "completed"` 前检查状态文件已有子代理记录:
   ```bash
   jq -e '.subagents | length > 0' state/audit-state.json
   ```

   写入 `phase_2a_prescan.status = "completed"` 后，再复核完成门禁:
   ```bash
   jq -e '.phases.phase_2a_prescan.dispatch_gate.status == "passed"' state/audit-state.json
   jq -e '.phases.phase_2a_prescan.status == "completed"' state/audit-state.json
   ```

   `phase_2a_prescan_completed` 事件只能在以下事件之后写入 `state/task-history.jsonl`:
   - `draft_documents_created`
   - `subagent_workspaces_created`
   - 每个模块 1 条 `subagent_started`

   未通过自检时，禁止启动 Phase 2B、POC、验证测试或手动测试。

### 2A.5: 更新审计状态

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
        "module_map_draft": "workspace/01-module-map.md",
        "subagent_workspaces": [
          "workspace/agent-<module>"
        ]
      },
      "dispatch_gate": {
        "status": "passed",
        "module_count": 1,
        "workspace_count": 1,
        "started_count": 1,
        "checked_at": "2026-05-06T10:05:00+08:00"
      }
    },
    "phase_2b_deep_recon": { "status": "in_progress" }
  },
  "subagents": [{
    "id": "agent-<module>",
    "background_version": "draft",
    "status": "running",
    "started_at": "2026-05-06T10:05:00+08:00"
  }]
}
```

**禁止状态**:
- `phase_2a_prescan.status = "completed"` 但 `subagents` 为空
- `phase_2b_deep_recon.status = "in_progress"` 但没有任何 `workspace/agent-*`
- `phase_3_poc`、`phase_4_verification` 或手动测试已经开始，但 `phase_2_discovery.subagents.total = 0`

发现禁止状态时，MainAgent 必须立即回到 2A.4 补建并派发子代理。

---

## Phase 2B: MainAgent 深度侦察 (与子代理并行执行)

**关键**: Phase 2A 子代理派发后**立即开始**此阶段，与子代理审计并行进行。

### 2B.1: 代码知识图谱构建（codebase-memory MCP）

#### Step 1: 索引目标仓库
调用 `index_repository` 将源码目录构建为图数据库：
- 仓库路径: `code-audit-projects/<name>/source/`
- 索引完成后，所有函数、类、调用关系、HTTP 端点将以图结构存储

#### Step 2: 架构概览
调用 `get_architecture` 获取项目整体架构：
- 模块划分、入口点、核心数据流
- 自动识别的框架和设计模式

#### Step 3: 攻击面映射（基于图谱）
- `search_graph(relationship="HTTP_CALLS")` — 发现所有 HTTP 端点
- `search_graph(min_degree=10, relationship="CALLS", direction="inbound")` — 高扇入函数
- `search_graph(max_degree=0, exclude_entry_points=true)` — 死代码
- `trace_path(function_name="<handler>", direction="outbound", depth=5)` — 调用链追踪

#### Step 4: 危险 Sink 定位
- `search_graph(name_pattern=".*execute.*")` — SQL 执行函数
- `search_graph(name_pattern=".*system.*|.*popen.*|.*subprocess.*")` — 命令执行
- `search_graph(name_pattern=".*open.*|.*read.*|.*write.*")` — 文件操作
- `trace_path(direction="inbound")` 对每个 Sink 反向追踪

**何时使用图谱 vs 传统 grep**:
- **图谱优先**: 调用链追踪、依赖分析、架构理解、影响范围评估
- **grep 辅助**: 文本模式搜索、特定字符串查找、配置文件审查

### 2B.2: 深度攻击面映射

- **详细 Source 列表**: 每个入口函数的完整签名、参数类型、认证状态
- **详细 Sink 列表**: 每个危险函数的调用上下文、防护措施
- **信任边界分析**: 内部 API vs 外部 API、认证域边界

### 2B.3: 精确模块依赖分析

- `get_architecture` 获取自动识别的模块结构
- `query_graph` 使用 Cypher 查询跨模块调用关系：
  ```
  MATCH (a)-[r:CALLS]->(b) WHERE a.file_path STARTS WITH '/module-a/'
  AND b.file_path STARTS WITH '/module-b/' RETURN a.name, b.name, count(r)
  ORDER BY count(r) DESC LIMIT 20
  ```
- 基于图谱的实际调用依赖更新模块划分和依赖图

### 2B.4: 完善文档为 FINAL 版本

- 更新 `workspace/00-work-background.md`：状态改为 FINAL，填入深度分析结果
- 更新 `workspace/01-module-map.md`：状态改为 FINAL，填入精确模块边界和依赖

---

## Phase 2C: 增量情报注入 (深度侦察完成后)

**目标**: 将 Phase 2B 深度侦察的发现增量传递给正在运行的子代理。

### 2C.1: 更新子代理 background.md

为每个子代理更新 `workspace/agent-<module>/background.md`:

1. 在文件头部将 `DRAFT v1` 改为 `FINAL`
2. 追加新章节 `## 🔄 深度侦察补充情报`:
   ```markdown
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

### 2C.2: 更新子代理 skill.md (如需要)

如果深度侦察发现新的漏洞类型值得关注，追加到 skill.md 的 `## 🔄 深度侦察补充指令` 章节。

### 2C.3: 记录注入事件

```json
{
  "event": "intelligence_injected",
  "timestamp": "2026-05-06T10:20:00+08:00",
  "target_agents": ["agent-services", "agent-connector"],
  "injection_type": "deep_recon_results",
  "new_findings": ["3 个新攻击面", "2 条跨模块调用路径"]
}
```

### 2C.4: 子代理接收更新

子代理在审计过程中定期检查 background.md 是否有更新（见子代理 skill 模板中的增量更新检查流程）。发现 FINAL 版本后：
- 审阅深度侦察补充情报章节
- 将新发现纳入 Phase 2 深入分析
- 调整审计优先级
