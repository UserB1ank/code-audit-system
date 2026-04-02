# Project Structure Reference (强制标准)

## ⭐ 标准目录布局 (必须严格遵守)

```
code-audit-projects/<project-name>/
├── source/                  # 源代码 (git clone 必须到此目录)
│   ├── src/                 # 源代码主目录
│   ├── package.json         # 或 pom.xml, Cargo.toml, requirements.txt
│   └── ...
│
├── state/                   # 任务状态追踪 (必须)
│   ├── audit-state.json     # 审计状态
│   └── task-history.jsonl   # 历史事件日志
│
├── workspace/               # CVE Hunter 工作区 (必须)
│   ├── 00-work-background.md    # 技术侦察报告 (MainAgent 创建)
│   ├── 01-module-map.md         # 模块划分图 (MainAgent 创建)
│   ├── agent-<module-1>/        # 子 Agent 1 工作区
│   │   ├── skill.md             # 子 Agent 审计指令
│   │   └── report.md            # CVE 审计报告 (子 Agent 输出)
│   ├── agent-<module-2>/        # 子 Agent 2 工作区
│   │   └── report.md
│   └── agent-<module-N>/        # 子 Agent N 工作区
│       └── report.md
│
├── pocs/                    # POC 脚本 (CVE 验证后创建)
│   ├── poc-001-rce-auth-bypass.py
│   ├── poc-002-sqli-admin-takeover.py
│   └── README.md
│
├── reports/                 # 审计报告 (最终输出)
│   ├── cve-submission-report.md   # CVE 提交主报告
│   ├── cve-2026-XXXXX-001.md      # 独立 CVE 报告
│   ├── cve-2026-XXXXX-002.md
│   └── verification-report.md     # POC 验证报告 (可选)
│
├── docker/                  # Docker 环境 (可选)
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── metadata.json            # 项目元数据 (必须)
```

---

## 🔧 关键规则 (必须遵守)

### 1. 源代码目录

**规则**: `git clone` 必须克隆到 `source/` 子目录

```bash
# ✅ 正确
cd code-audit-projects/<project-name>/
git clone <repo-url> source/

# ❌ 错误 (不要直接克隆到项目根目录)
git clone <repo-url> .
```

**原因**:
- 保持工作区整洁
- 避免与 `state/`, `workspace/`, `reports/` 混淆
- 统一所有项目结构

---

### 2. 状态文件位置

**规则**: 状态文件必须在 `state/` 目录

```
state/
├── audit-state.json     # 当前审计状态
└── task-history.jsonl   # 事件历史
```

**audit-state.json 格式**:
```json
{
  "project": "<project-name>",
  "repository": "<git-url>",
  "audit_start": "2026-04-02T00:14:00+08:00",
  "status": "in_progress",
  "subagents": [
    {
      "id": "agent-01-gui-types",
      "session_key": "agent:cybersecurity_expert:subagent:xxx",
      "module": "src/gui/types/",
      "priority": "P0",
      "status": "running"
    }
  ],
  "next_steps": ["等待子 Agent 完成", "汇总报告", "POC 开发"]
}
```

---

### 3. 工作区结构

**规则**: MainAgent 必须预先创建背景文档

```
workspace/
├── 00-work-background.md    # 技术栈、攻击面、CVE 发现策略
├── 01-module-map.md         # 模块划分、文件映射
└── agent-<module-name>/     # 每个子 Agent 独立工作区
    ├── skill.md             # 审计指令 (MainAgent 创建)
    └── report.md            # CVE 报告 (子 Agent 输出)
```

**00-work-background.md 必须包含**:
- 技术栈总结
- 应用类型分类
- 攻击面地图 (入口点、信任边界)
- 高风险区域 (认证、文件操作、序列化、命令执行)

**01-module-map.md 必须包含**:
- 模块边界定义
- 文件到模块的映射
- 模块间依赖关系
- 模块依赖图

---

### 4. 子 Agent 工作区

**规则**: 每个子 Agent 必须有独立工作区

```
workspace/agent-<module-name>/
├── skill.md         # MainAgent 创建的审计指令
└── report.md        # 子 Agent 完成的 CVE 报告
```

**skill.md 必须指定**:
- 审计模块名称
- 目标源代码路径 (绝对路径)
- 重点文件列表
- CVE 发现重点 (漏洞类型)
- 报告输出位置 (绝对路径)

**report.md 必须包含**:
- CVE 编号 (或 pending)
- 漏洞类型
- CVSS v3.1 评分
- 精确位置 (文件：行号)
- 完整调用链 (Source → Sink)
- 可利用 POC (或 POC 可行性证明)
- 修复建议

---

### 5. 报告命名规范

**CVE 报告**:
```
reports/cve-<NNN>-<type>-<module>.md
示例：
reports/cve-001-rce-auth-bypass.md
reports/cve-002-sqli-user-enumeration.md
reports/cve-003-path-traversal-downloads.md
```

**POC 脚本**:
```
pocs/poc-<NNN>-<type>-<location>.py
示例：
pocs/poc-001-rce-auth-bypass.py
pocs/poc-002-sqli-admin-takeover.py
pocs/poc-003-path-traversal-downloads.py
```

**子 Agent 工作区**:
```
workspace/agent-<module-name>/
示例：
workspace/agent-gui-types/
workspace/agent-networking/
workspace/agent-services/
```

---

## 📋 项目初始化流程

### Step 1: 创建项目目录

```bash
mkdir -p code-audit-projects/<project-name>/{source,state,workspace,pocs,reports,docker}
```

### Step 2: 克隆源代码

```bash
cd code-audit-projects/<project-name>/
git clone <repo-url> source/
```

### Step 3: 创建 metadata.json

```bash
cat > metadata.json << EOF
{
  "project_name": "<project-name>",
  "git_url": "<repo-url>",
  "clone_date": "$(date -Iseconds)",
  "commit_hash": "$(cd source && git rev-parse HEAD)",
  "language": ["<language>"],
  "framework": ["<framework>"],
  "app_type": "<web-app|system-service|gui|mobile>",
  "modules": [],
  "vulnerabilities_found": 0,
  "pocs_written": 0,
  "verification_status": "pending"
}
EOF
```

### Step 4: 创建技术背景文档

```bash
# MainAgent 创建 00-work-background.md
# MainAgent 创建 01-module-map.md
```

### Step 5: 启动子 Agent

```bash
# 为每个模块创建子 Agent 工作区
mkdir -p workspace/agent-<module-name>/
# 创建 skill.md
# 启动子 Agent
```

---

## 🚫 常见错误 (避免)

| 错误 | 正确做法 |
|------|----------|
| `git clone <url> .` (克隆到根目录) | `git clone <url> source/` |
| 状态文件放在 `workspace/` | 状态文件放在 `state/` |
| 子 Agent 直接输出到 `reports/` | 子 Agent 输出到 `workspace/agent-*/report.md` |
| MainAgent 不创建背景文档 | MainAgent 必须先创建 `00-work-background.md` |
| 报告命名无规律 | 使用 `cve-<NNN>-<type>.md` 格式 |

---

## ✅ 检查清单

项目初始化完成后检查：

- [ ] `source/` 目录存在且包含源代码
- [ ] `state/` 目录存在
- [ ] `workspace/` 目录存在
- [ ] `workspace/00-work-background.md` 已创建
- [ ] `workspace/01-module-map.md` 已创建
- [ ] `metadata.json` 已创建
- [ ] 每个子 Agent 有独立工作区 `workspace/agent-<name>/`
- [ ] 每个子 Agent 有 `skill.md` 指令文件

---

## 📦 项目归档

审计完成后：

```bash
cd code-audit-projects/
tar -czf <project-name>-audit-$(date +%Y%m%d).tar.gz <project-name>/
```

归档内容：
- 源代码 (`source/`)
- 状态文件 (`state/`)
- CVE 报告 (`reports/`)
- POC 脚本 (`pocs/`)
- 工作区文档 (`workspace/`)
