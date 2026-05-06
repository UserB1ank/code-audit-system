# Phase 1: 项目初始化与长期审计机制

> 本文档包含 Phase 1 项目初始化的详细步骤和长期/增量审计机制的完整说明。目录结构标准参见 `references/project-structure.md`。

---

## 项目初始化详细步骤

### 1. 创建标准项目目录并克隆源码

遵循 `references/project-structure.md` 定义的标准目录布局。必须克隆到 `source/` 子目录：

```bash
mkdir -p code-audit-projects/<project-name>/{source,state,workspace,pocs,reports,docker}
cd code-audit-projects/<project-name>/
git clone <git-url> source/
```

**❌ 错误**: `git clone <url> .` (直接克隆到根目录)
**✅ 正确**: `git clone <url> source/` (克隆到 source/ 子目录)

### 2. 创建 metadata.json

基准字段参见 `references/project-structure.md`。首次审计时额外包含：

```json
{
  "project_name": "<project-name>",
  "git_url": "<repo-url>",
  "clone_date": "2026-04-02T10:30:00Z",
  "commit_hash": "<git rev-parse HEAD>",
  "language": ["Java", "Python", "Rust", "..."],
  "framework": ["Spring", "Django", "..."],
  "app_type": "web-application|system-service|gui|mobile",
  "modules": [],
  "vulnerabilities_found": 0,
  "pocs_written": 0
}
```

### 创建技术背景文档 (MainAgent 负责)

- `workspace/00-work-background.md` - 技术栈、攻击面、CVE 发现策略
- `workspace/01-module-map.md` - 模块划分、文件映射

### 创建状态文件 (必须，支持断点续传)

- `state/audit-state.json` - 审计状态追踪
- `state/task-history.jsonl` - 事件历史日志
- `state/audit-logs/` - 长期审计日志目录

**状态文件作用**:
- 记录审计进度 (阶段、子 Agent 状态、漏洞发现)
- 支持断点续传 (崩溃/暂停后恢复)
- 定期保存检查点 (`state/checkpoint-<timestamp>.json`)
- 实时日志追加 (`task-history.jsonl`)
- 长期审计追踪 (`state/audit-logs/audit-<N>-<timestamp>.md`)

### 暂停/恢复流程

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

### 完整目录结构

```
code-audit-projects/<project-name>/
├── source/              # 源代码 (git clone 必须到此)
├── state/               # 状态追踪
│   ├── audit-state.json
│   ├── task-history.jsonl
│   └── audit-logs/           # 长期审计日志
│       ├── audit-001-<timestamp>.md
│       └── audit-002-<timestamp>.md
├── workspace/           # CVE Hunter 工作区
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   └── agent-<module>/
│       ├── skill.md
│       └── report.md
├── pocs/                # POC 脚本 (CVE 验证后)
├── reports/             # CVE 报告 (最终输出)
└── metadata.json        # 项目元数据
```

**参考**: `references/project-structure.md` 查看完整目录标准。

---

## 长期审计与增量审计机制

对同一项目进行多轮审计时，系统自动记录每轮审计的版本基线和变更范围，支持增量审计和漏洞状态追踪。

### 审计日志管理

每轮审计完成后，生成一份审计日志到 `state/audit-logs/`：

- **命名规则**: `audit-<序号>-<YYYYMMDD>-<HHMMSS>.md`
- **模板**: `templates/audit-log-template.md`
- **核心内容**: 审计日期、基准 Commit、依赖快照、变更摘要、漏洞发现、上轮漏洞追踪

### 首次审计（全量）

```
1. git clone → 记录初始 Commit 为基准版本
2. 执行完整审计流程（Phase 1-6）
3. 生成 audit-001-<timestamp>.md，记录基准 Commit 和全部发现
4. 记录 metadata.json 中的 audit_count 和 last_audit_commit
```

### 增量审计（第 2 轮起）

当 MainAgent 检测到项目中已存在 `state/audit-logs/` 时，自动进入增量审计模式。

#### Step 1: 版本对比

1. 读取上轮审计日志中的基准 Commit
2. 执行 `git pull` 拉取最新代码
3. 生成变更摘要：
   - `git log --oneline <上轮commit>..HEAD` — 新 Commit 列表
   - `git diff --stat <上轮commit>..HEAD` — 变更文件统计
   - `git diff --stat <上轮commit>..HEAD -- '*.py' '*.java' '*.rs' '*.php'` — 按语言过滤

#### Step 2: 图谱变更检测

使用 codebase-memory MCP 的 `detect_changes` 检测结构变更：
- `detect_changes(base_commit="<上轮commit>")` — 获取受影响的函数/类/调用链
- 对变更函数执行 `trace_path(direction="both")` — 分析上下游影响

#### Step 3: 确定审计策略

| 条件 | 策略 |
|------|------|
| 变更文件 ≤ 总文件数 30% | 增量审计（聚焦变更及影响范围） |
| 变更文件 > 总文件数 30% | 全量审计 |
| 距上轮审计超过 90 天 | 全量审计 |
| 主版本号升级 | 全量审计 |

#### Step 4: 增量审计范围

- **直接审计**: 新增文件和修改文件中的新代码
- **影响分析**: 变更函数的上下游调用链（从图谱获取）
- **供应链审计**: 新增/升级依赖的安全性
- **结构影响**: 图谱检测到的受影响路径
- **复用上轮**: 未变更模块标记"复用上轮结论"

#### Step 5: 上轮漏洞状态追踪

对上轮发现的每个漏洞，检查当前版本状态：
- 代码未变 → 标记"未修复"
- 相关代码已修改 → 重新验证（可能已修复或变体）
- 文件已删除 → 标记"已失效"

#### Step 6: 生成审计日志

使用 `templates/audit-log-template.md` 生成 `state/audit-logs/audit-<N>-<timestamp>.md`

### metadata.json 增量字段

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
