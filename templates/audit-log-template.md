# 长期审计日志模板

每次对同一项目执行审计时生成一份审计日志，记录本次审计的版本基线、变更范围和审计结果。日志保存至 `state/audit-logs/` 目录。

## 📁 文件位置

```
code-audit-projects/<project>/state/audit-logs/
├── audit-001-20260402-130000.md    # 第 1 轮审计日志
├── audit-002-20260415-100000.md    # 第 2 轮审计日志（增量）
└── audit-003-20260428-090000.md    # 第 3 轮审计日志（增量）
```

**命名规则**: `audit-<序号>-<YYYYMMDD>-<HHMMSS>.md`

---

## 📝 日志模板

```markdown
# 审计日志 #<序号>

## 基本信息

| 字段 | 值 |
|------|-----|
| **项目名称** | <project-name> |
| **审计轮次** | 第 <N> 轮 |
| **审计日期** | <YYYY-MM-DD HH:MM:SS> |
| **审计模式** | standard / specialized |
| **审计人员** | <agent 标识> |

## 版本基线

| 字段 | 值 |
|------|-----|
| **仓库 URL** | <git-url> |
| **审计基准 Commit** | `<full-commit-hash>` |
| **基准 Commit 日期** | <commit 日期> |
| **基准 Commit 消息** | <commit message 首行> |
| **分支** | <branch-name> |
| **代码文件总数** | <count> |
| **代码总行数** | <count> |

### 依赖版本快照

<从 requirements.txt / package-lock.json / Cargo.lock / pom.xml 等提取关键依赖版本>

| 依赖 | 版本 |
|------|------|
| <dep-1> | <version> |
| <dep-2> | <version> |

## 与上轮审计的差异

<仅第 2 轮及之后填写。第 1 轮标注"首次审计，无上轮基线"。>

### 上轮审计基线

| 字段 | 值 |
|------|-----|
| **上轮审计日期** | <YYYY-MM-DD HH:MM:SS> |
| **上轮基准 Commit** | `<full-commit-hash>` |
| **上轮审计序号** | #<N-1> |

### Git 变更摘要

```bash
# 生成命令（审计时执行）：
cd source/ && git log --oneline <上轮commit>..HEAD
cd source/ && git diff --stat <上轮commit>..HEAD
cd source/ && git diff --stat <上轮commit>..HEAD -- '*.py' '*.java' '*.rs' '*.php' '*.js' '*.ts'
```

**Commit 差异**: <上轮commit>..HEAD 共 <N> 个新 commit

| 指标 | 值 |
|------|-----|
| **新增 Commit** | <N> 个 |
| **变更文件数** | <N> 个 |
| **新增行数** | +<N> |
| **删除行数** | -<N> |
| **净增行数** | ±<N> |

### 变更文件分类

#### 新增文件

| 文件路径 | 行数 | 功能描述 | 审计关注 |
|----------|------|----------|----------|
| `path/to/new_file.py` | <N> | <描述> | 🔴/🟡/🟢 |

#### 修改文件

| 文件路径 | 变更量 | 变更类型 | 审计关注 |
|----------|--------|----------|----------|
| `path/to/modified.py` | +N/-M | 功能修改/Bug 修复/重构 | 🔴/🟡/🟢 |

#### 删除文件

| 文件路径 | 原行数 | 说明 |
|----------|--------|------|
| `path/to/deleted.py` | <N> | <说明> |

### 高变更风险区域

<基于 diff 分析，标注变更中与安全相关的代码区域>

| 风险区域 | 变更内容 | 潜在影响 |
|----------|----------|----------|
| 认证模块 | 新增 OAuth 回调 | 新攻击面 |
| SQL 查询层 | 修改查询构建逻辑 | 注入风险变化 |

## 图谱变更检测

<使用 codebase-memory MCP 的 detect_changes 工具>

| 工具调用 | 结果摘要 |
|----------|----------|
| `detect_changes(base_commit="<上轮commit>")` | 受影响的函数/类/调用链数量 |
| `trace_path(function_name="<变更函数>", direction="both")` | 变更函数的上下游影响 |

### 受影响的调用链

| 变更函数 | 上游调用者 | 下游被调用者 | 风险评估 |
|----------|------------|--------------|----------|
| `<func>` | `<caller-1>, <caller-2>` | `<sink-1>` | 🔴 高 |

## 审计范围与策略

### 全量审计（第 1 轮）

<首次审计，覆盖全部代码>

### 增量审计（第 2 轮起）

**聚焦范围**:
1. 变更文件中的新代码（直接审计）
2. 变更函数的上下游调用链（影响分析）
3. 新增依赖的安全性（供应链审计）
4. 图谱检测到的受影响路径（结构性影响）

**复用上轮结论**:
- 上轮已审计且未变更的模块 → 标记"复用上轮结论"
- 上轮发现的漏洞在本次变更中是否被修复 → 重新验证

## 审计执行摘要

### 子 Agent 执行情况

| 子 Agent | 模块 | 状态 | 发现漏洞 | 耗时 |
|----------|------|------|----------|------|
| agent-<mod-1> | <module-1> | completed/failed | <N> | <duration> |
| agent-<mod-2> | <module-2> | completed/failed | <N> | <duration> |

### 漏洞发现汇总

| 编号 | 漏洞类型 | 位置 | CVSS | 状态 | 是否为新增 |
|------|----------|------|------|------|------------|
| V-01 | <type> | <file:line> | <score> | CVE 就绪/已过滤 | 是/否/上轮遗留 |

### 上轮漏洞状态追踪

<仅第 2 轮起填写>

| 上轮编号 | 上轮漏洞类型 | 上轮位置 | 当前状态 |
|----------|--------------|----------|----------|
| V-01 | <type> | <file:line> | 未修复/已修复/部分修复/变更 |
| V-02 | <type> | <file:line> | 未修复/已修复 |

## 审计结论

### 本次审计总结

<一段话总结本次审计发现和风险变化>

### 风险趋势

| 指标 | 上轮 | 本轮 | 变化 |
|------|------|------|------|
| CVE 就绪漏洞数 | <N> | <N> | +N/-N |
| 高危模块数 | <N> | <N> | +N/-N |
| 未修复漏洞 | <N> | <N> | +N/-N |
| 代码变更量 | - | +<N>/-<N> | - |

### 下次审计建议

- <建议 1：如哪些模块需要重点关注>
- <建议 2：如新增攻击面需要深入审计>
- <建议 3：如哪些漏洞需要重新验证>
```

---

## 🔧 使用流程

### 第 1 轮审计（全量）

```bash
# 1. 克隆项目
cd code-audit-projects/<name>/ && git clone <url> source/

# 2. 记录基准版本
cd source/ && git rev-parse HEAD  # 记录到审计日志
cd source/ && git log -1 --format="%H %ai %s"  # 完整 commit 信息

# 3. 创建审计日志目录
mkdir -p state/audit-logs/

# 4. 执行全量审计（标准流程）
# 5. 生成审计日志: state/audit-logs/audit-001-<timestamp>.md
```

### 第 2 轮起（增量）

```bash
# 1. 拉取最新代码
cd code-audit-projects/<name>/source/ && git pull

# 2. 读取上轮审计日志的基准 Commit
# 从 state/audit-logs/audit-<N-1>-*.md 中提取

# 3. 生成变更摘要
cd source/ && git log --oneline <上轮commit>..HEAD
cd source/ && git diff --stat <上轮commit>..HEAD

# 4. 使用 codebase-memory 检测结构变更
# detect_changes(base_commit="<上轮commit>")

# 5. 确定增量审计范围（仅审计变更及其影响范围）
# 6. 执行增量审计
# 7. 生成审计日志: state/audit-logs/audit-<N>-<timestamp>.md
```

### 判断全量 vs 增量

| 条件 | 审计策略 |
|------|----------|
| 第 1 轮审计 | 全量审计 |
| 变更文件 ≤ 总文件数 30% | 增量审计（聚焦变更） |
| 变更文件 > 总文件数 30% | 建议全量审计 |
| 距上轮审计超过 90 天 | 建议全量审计 |
| 大版本升级（主版本号变化） | 全量审计 |
```
