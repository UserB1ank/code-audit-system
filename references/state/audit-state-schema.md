# 审计状态文件格式规范

## 📁 文件位置

```
code-audit-projects/<project>/state/
├── audit-state.json       # 当前审计状态
├── task-history.jsonl     # 事件历史日志
└── checkpoint-<timestamp>.json  # 审计检查点 (可选)
```

---

## 📊 audit-state.json 格式

### 完整结构

```json
{
  "schema": "code-audit-system.audit-state.v2",
  "version": "3.1.0",
  "updated_at": "2026-04-02T13:30:00+08:00",
  
  "project": {
    "id": 4,
    "name": "ecms",
    "url": "https://github.com/exoplatform/ecms",
    "path": "./source",
    "language": "Java",
    "build_tool": "Maven",
    "files_count": 483
  },
  
  "status": "auditing",
  "phase": "phase_2_discovery",
  
  "phases": {
    "phase_1_init": {
      "status": "completed",
      "started_at": "2026-04-02T13:00:00+08:00",
      "completed_at": "2026-04-02T13:05:00+08:00",
      "outputs": {
        "work_background": "workspace/00-work-background.md",
        "module_map": "workspace/01-module-map.md"
      }
    },
    "phase_2_discovery": {
      "status": "in_progress",
      "started_at": "2026-04-02T13:05:00+08:00",
      "subagents": {
        "total": 3,
        "active": 3,
        "completed": 0,
        "failed": 0
      }
    },
    "phase_3_poc": {
      "status": "pending",
      "dependencies": ["phase_2_discovery"]
    },
    "phase_4_verification": {
      "status": "pending",
      "dependencies": ["phase_3_poc"]
    },
    "phase_5_report": {
      "status": "pending",
      "dependencies": ["phase_4_verification"]
    }
  },
  
  "subagents": [
    {
      "id": "agent-services",
      "label": "ecms-cve-hunter-services",
      "session_key": "agent:cybersecurity_expert:subagent:xxx",
      "module": "core/services/",
      "source_path": "/home/pc01/.openclaw/workspace-cybersecurity_expert/code-audit-projects/ecms/source/core/services/",
      "priority": "P0",
      "status": "running",
      "started_at": "2026-04-02T13:06:00+08:00",
      "progress": {
        "phase": "phase_2_discovery",
        "files_scanned": 15,
        "sources_found": 5,
        "sinks_found": 8,
        "chains_traced": 3,
        "vulnerabilities_found": 0
      },
      "output": {
        "background": "workspace/agent-services/background.md",
        "skill": "workspace/agent-services/skill.md",
        "log": "workspace/agent-services/execution.log",
        "report": "workspace/agent-services/report.md"
      }
    },
    {
      "id": "agent-connector",
      "label": "ecms-cve-hunter-connector",
      "session_key": "agent:cybersecurity_expert:subagent:yyy",
      "module": "core/connector/",
      "priority": "P0",
      "status": "running",
      "started_at": "2026-04-02T13:06:00+08:00",
      "progress": {
        "phase": "phase_2_discovery",
        "files_scanned": 10,
        "sources_found": 3,
        "sinks_found": 5,
        "chains_traced": 2,
        "vulnerabilities_found": 0
      }
    },
    {
      "id": "agent-viewer",
      "label": "ecms-cve-hunter-viewer",
      "session_key": "agent:cybersecurity_expert:subagent:zzz",
      "module": "core/viewer/",
      "priority": "P0",
      "status": "running",
      "started_at": "2026-04-02T13:06:00+08:00",
      "progress": {
        "phase": "phase_2_discovery",
        "files_scanned": 8,
        "sources_found": 2,
        "sinks_found": 4,
        "chains_traced": 1,
        "vulnerabilities_found": 0
      }
    }
  ],
  
  "vulnerabilities": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "total": 0,
    "cve_ready": 0,
    "details": []
  },
  
  "checkpoints": [
    {
      "timestamp": "2026-04-02T13:05:00+08:00",
      "phase": "phase_1_init",
      "status": "completed",
      "summary": "技术侦察完成，模块划分完成"
    },
    {
      "timestamp": "2026-04-02T13:06:00+08:00",
      "phase": "phase_2_discovery",
      "status": "started",
      "summary": "启动 3 个 CVE Hunter 子 Agent"
    }
  ],
  
  "next_actions": [
    "等待子 Agent 完成审计",
    "汇总 CVE 报告",
    "启动 POC 开发"
  ],
  
  "errors": [],
  
  "metadata": {
    "created_at": "2026-04-02T13:00:00+08:00",
    "last_updated": "2026-04-02T13:30:00+08:00",
    "update_count": 15
  }
}
```

---

## 📝 task-history.jsonl 格式

### 事件日志结构

```jsonl
{"timestamp": "2026-04-02T13:00:00+08:00", "event": "project_init", "project_id": 4, "name": "ecms"}
{"timestamp": "2026-04-02T13:00:05+08:00", "event": "directory_created", "path": "source/"}
{"timestamp": "2026-04-02T13:00:10+08:00", "event": "git_clone_started", "url": "https://github.com/exoplatform/ecms"}
{"timestamp": "2026-04-02T13:05:00+08:00", "event": "git_clone_completed", "files": 483}
{"timestamp": "2026-04-02T13:05:05+08:00", "event": "background_created", "file": "workspace/00-work-background.md"}
{"timestamp": "2026-04-02T13:05:10+08:00", "event": "module_map_created", "file": "workspace/01-module-map.md"}
{"timestamp": "2026-04-02T13:06:00+08:00", "event": "subagent_started", "id": "agent-services", "module": "core/services/"}
{"timestamp": "2026-04-02T13:06:01+08:00", "event": "subagent_started", "id": "agent-connector", "module": "core/connector/"}
{"timestamp": "2026-04-02T13:06:02+08:00", "event": "subagent_started", "id": "agent-viewer", "module": "core/viewer/"}
{"timestamp": "2026-04-02T13:10:00+08:00", "event": "subagent_progress", "id": "agent-services", "phase": "phase_2", "files_scanned": 15}
{"timestamp": "2026-04-02T13:15:00+08:00", "event": "vulnerability_found", "id": "agent-services", "type": "JCR SQL Injection", "cvss": 9.8}
{"timestamp": "2026-04-02T13:20:00+08:00", "event": "subagent_completed", "id": "agent-services", "vulnerabilities": 3}
```

---

## 🔄 检查点文件 (Checkpoint)

### 用途

- 审计过程中定期保存状态
- 支持断点续传
- 崩溃恢复

### 文件命名

```
state/checkpoint-<timestamp>.json
示例：checkpoint-20260402-133000.json
```

### 保存时机

1. **每个阶段完成时**
2. **发现高危漏洞时**
3. **子 Agent 完成时**
4. **定期保存** (每 10 分钟)

---

## 📋 状态枚举

### 项目状态

```json
{
  "status": "init|cloning|auditing|poc_developing|verifying|reporting|completed|paused|failed"
}
```

### 阶段状态

```json
{
  "status": "pending|in_progress|completed|failed|skipped"
}
```

### 子 Agent 状态

```json
{
  "status": "pending|running|completed|failed|timeout"
}
```

### 漏洞状态

```json
{
  "status": "identified|analyzing|poc_ready|verified|cve_submitted|rejected"
}
```

---

## 🔧 状态更新流程

### MainAgent 职责

1. **初始化状态文件**:
   ```python
   write state/audit-state.json
   ```

2. **阶段完成时更新**:
   ```python
   update state/audit-state.json
   append state/task-history.jsonl
   ```

3. **定期保存检查点**:
   ```python
   cp state/audit-state.json state/checkpoint-<timestamp>.json
   ```

### 子 Agent 职责

1. **启动时报告**:
   ```json
   {"event": "subagent_started", "id": "agent-xxx", "module": "..."}
   ```

2. **进度更新** (每 5 分钟):
   ```json
   {"event": "subagent_progress", "id": "agent-xxx", "phase": "...", "progress": {...}}
   ```

3. **发现漏洞时报告**:
   ```json
   {"event": "vulnerability_found", "id": "agent-xxx", "type": "...", "cvss": X.X}
   ```

4. **完成时报告**:
   ```json
   {"event": "subagent_completed", "id": "agent-xxx", "vulnerabilities": N}
   ```

---

## 📊 恢复流程

### 从检查点恢复

```bash
# 1. 找到最近的检查点
ls -lt state/checkpoint-*.json | head -1

# 2. 恢复状态
cp state/checkpoint-<timestamp>.json state/audit-state.json

# 3. 分析恢复点
cat state/audit-state.json | jq '.subagents[] | select(.status == "running")'

# 4. 重启未完成的子 Agent
# 5. 继续审计
```

### 恢复策略

| 场景 | 恢复动作 |
|------|----------|
| 子 Agent 运行中 | 继续等待完成 |
| 子 Agent 失败 | 重启子 Agent |
| 阶段失败 | 重试阶段 |
| 项目暂停 | 从最近检查点恢复 |

---

**所有审计项目必须使用此状态格式** 🔒
