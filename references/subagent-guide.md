# 子代理审计指南：背景文档创建与图谱增强审计

> 本文档包含 MainAgent 创建子代理背景文档的详细模板，以及子代理使用 codebase-memory 图谱的增强审计流程。从 SKILL.md 中提取。

---

## MainAgent 创建子 Agent 背景文档 (必须)

**每个子 Agent 启动前**, MainAgent 必须创建 `workspace/agent-<module>/background.md`，包含以下 7 个部分：

### 1. 模块涉及文件列表

```markdown
## 涉及文件

**核心文件** (重点审计):
1. `File1.java` (行数：XXX) - 功能描述 - CVE 潜力 🔴
2. `File2.java` (行数：XXX) - 功能描述 - CVE 潜力 🔴

**辅助文件**:
- `File3.java` - 辅助功能
```

### 2. 可能存在的漏洞类型

```markdown
## 高价值目标 (P0)

| 漏洞类型 | CVSS 潜力 | 存在可能性 | 审计优先级 |
|----------|-----------|------------|------------|
| RCE | 9.0-10.0 | 高 | 🔴 立即 |
| Auth Bypass | 8.0-10.0 | 中 | 🔴 立即 |

## 中等价值目标 (P1)
...
```

### 3. 审计流程与思路

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
- 识别全局策略限制、分析绕过可能性

### Phase 4: CVE 发现与报告 (10-15 分钟)
- 验证可利用性、计算 CVSS 评分
```

### 4. 调用流追踪指南

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

### 5. 输入输出流追踪

```markdown
## 输入输出流

**输入流**:
- HTTP 请求 → REST 端点 → Service 层 → DAO 层 → JCR 查询
- 文件上传 → 验证 (不足) → 存储 → 执行

**输出流**:
- JCR 查询结果 → Service 层 → REST 响应 → 攻击者
```

### 6. 全局策略限制分析

```markdown
## 全局策略

**现有控制**:
- WCMCoreUtils.getUserSessionProvider() - 获取用户会话
- ACL 权限检查 - 理论上限制节点访问

**绕过方法**:
- 使用 `getSystemSessionProvider()` 替代 → 完全绕过 ACL
```

### 7. 绕过可能性分析

```markdown
## 绕过分析

| 安全控制 | 绕过方法 | 可利用性 |
|----------|----------|----------|
| ACL 权限检查 | getSystemSessionProvider() | ✅ 高 |
| 路径验证 | URL 编码绕过 (%2e%2e%2f) | ✅ 中 |
| null 检查 | 发送非 null 恶意值 | ✅ 高 |
```

---

## 子代理指令必须包含

- **目标源代码路径** (绝对路径): `<project-root>/source/<module>/`
- **报告输出位置** (绝对路径): `<project-root>/workspace/agent-<module>/report.md`
- **背景文档位置** (启动后必须阅读): `<project-root>/workspace/agent-<module>/background.md`
- **专项技能位置** (启动后必须阅读): `<project-root>/workspace/agent-<module>/skill.md`
- 仅关注可利用漏洞
- 追踪完整调用链 (Source → Sink)
- 记录安全控制措施和绕过方法
- 过滤理论性问题
- **增量更新检查**: Phase 0 完成后和 Phase 2 开始前，检查 background.md 是否从 DRAFT 更新为 FINAL
- **使用 codebase-memory MCP 图谱工具辅助审计**

---

## 图谱增强审计流程（codebase-memory MCP）

子代理在审计过程中，应充分利用代码知识图谱进行结构化分析。图谱在 Phase 2B 已由 MainAgent 构建完成，子代理可直接查询：

### Phase 1: 代码地图绘制 — 图谱增强

#### 1.1 模块结构概览
- `get_architecture` — 获取模块整体架构和自动识别的设计模式
- `get_graph_schema` — 了解该项目的节点/边类型

#### 1.2 入口点与 Sink 发现
- `search_graph(label="Function", name_pattern=".*<module-pattern>.*")` — 发现模块内所有函数
- `search_graph(relationship="HTTP_CALLS")` — 发现 HTTP 端点（攻击入口 Source）
- `search_graph(name_pattern=".*execute.*|.*query.*|.*system.*|.*popen.*")` — 发现危险 Sink
- `search_code(query="<dangerous_function>")` — 文本搜索补充图谱未覆盖的模式

### Phase 2: Source → Sink 追踪 — 图谱核心价值

#### 2.1 正向追踪（Source → Sink）
从用户输入入口追踪到危险操作：
```
trace_path(function_name="<handler>", direction="outbound", depth=5, risk_labels=true)
```
- `risk_labels=true` 自动标注路径中的高风险节点

#### 2.2 反向追踪（Sink → Source）
从危险函数反向追踪所有调用来源：
```
trace_path(function_name="<dangerous_sink>", direction="inbound", depth=5)
```
- 快速判断是否存在用户可控数据到达 Sink 的路径

#### 2.3 完整调用上下文
```
trace_path(function_name="<target>", direction="both", depth=3)
```
- 同时获取调用者和被调用者，快速定位验证/过滤层

#### 2.4 跨模块调用链
```cypher
MATCH path = (src)-[:CALLS*1..6]->(sink)
WHERE src.name =~ '.*<handler>.*' AND sink.name =~ '.*execute.*'
RETURN path
```

### Phase 3: 安全控制分析 — 图谱辅助
- `trace_path(direction="outbound")` 检查路径上是否有验证/过滤节点
- 对比有/无安全控制的路径差异
- `get_code_snippet(qualified_name="<validator>")` 快速查看验证函数实现

### Phase 4: 报告阶段
调用链记录应包含图谱 trace 的完整结果：
- 调用深度、中间节点、风险标注
- 每个节点的文件路径和行号（从 `get_code_snippet` 获取）

---

## 子代理启动强制流程

子代理被调度后，必须**首先使用 Read 工具读取 `background.md` 和 `skill.md`**，然后基于这些定制文档中的指导开展审计。这些文档包含了针对该模块的技术侦察结果、高价值目标、审计思路和绕过分析，是提升发现率的关键。
