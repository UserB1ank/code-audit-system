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
  "version": "3.2.0",
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

  "audit_mode": "standard",
  "cve_intelligence": null,

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
    "phase_2_0_intelligence": {
      "status": "skipped",
      "started_at": null,
      "completed_at": null,
      "outputs": {
        "cve_intelligence_report": "workspace/02-cve-intelligence.md"
      },
      "note": "仅专项审计模式执行此阶段，标准模式下 status 为 skipped"
    },
    "phase_2a_prescan": {
      "status": "completed",
      "started_at": "2026-04-02T13:05:00+08:00",
      "completed_at": "2026-04-02T13:10:00+08:00",
      "outputs": {
        "work_background_draft": "workspace/00-work-background.md",
        "module_map_draft": "workspace/01-module-map.md"
      },
      "note": "快速预扫描: 语言/框架识别、粗略模块划分、攻击面草图、立即派发子代理"
    },
    "phase_2b_deep_recon": {
      "status": "completed",
      "started_at": "2026-04-02T13:10:00+08:00",
      "completed_at": "2026-04-02T13:25:00+08:00",
      "progress": {
        "code_graph_indexed": true,
        "architecture_analyzed": true,
        "attack_surface_mapped": true,
        "module_deps_analyzed": true
      },
      "outputs": {
        "work_background_final": "workspace/00-work-background.md",
        "module_map_final": "workspace/01-module-map.md"
      },
      "note": "深度侦察与子代理审计并行: 代码图谱构建、精确攻击面映射、精确模块依赖分析"
    },
    "phase_2c_injection": {
      "status": "completed",
      "started_at": "2026-04-02T13:25:00+08:00",
      "completed_at": "2026-04-02T13:26:00+08:00",
      "injections": [
        {
          "target_agent": "agent-services",
          "injection_time": "2026-04-02T13:25:30+08:00",
          "type": "deep_recon_results",
          "new_findings": ["2 个新攻击面", "1 条跨模块调用路径"]
        },
        {
          "target_agent": "agent-connector",
          "injection_time": "2026-04-02T13:25:45+08:00",
          "type": "deep_recon_results",
          "new_findings": ["1 个新攻击面", "图谱追踪的 3 条调用链"]
        }
      ],
      "note": "增量情报注入: 深度侦察结果写入子代理 background.md 的补充情报章节"
    },
    "phase_2_discovery": {
      "status": "in_progress",
      "started_at": "2026-04-02T13:10:00+08:00",
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
      "source_path": "<project-root>/source/core/services/",
      "priority": "P0",
      "status": "running",
      "started_at": "2026-04-02T13:06:00+08:00",
      "background_version": "draft",
      "last_intelligence_update": "2026-04-02T13:25:30+08:00",
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
      "background_version": "draft",
      "last_intelligence_update": "2026-04-02T13:25:45+08:00",
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
      "background_version": "draft",
      "last_intelligence_update": null,
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
      "summary": "项目初始化完成"
    },
    {
      "timestamp": "2026-04-02T13:05:35+08:00",
      "phase": "phase_2a_prescan",
      "status": "completed",
      "summary": "快速预扫描完成，3 个子代理已并行派发"
    },
    {
      "timestamp": "2026-04-02T13:25:05+08:00",
      "phase": "phase_2b_deep_recon",
      "status": "completed",
      "summary": "深度侦察完成（与子代理并行），代码图谱已构建，精确攻击面已映射"
    },
    {
      "timestamp": "2026-04-02T13:26:00+08:00",
      "phase": "phase_2c_injection",
      "status": "completed",
      "summary": "增量情报注入完成，子代理已接收深度侦察结果"
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
{"timestamp": "2026-04-02T13:05:05+08:00", "event": "phase_2a_prescan_started"}
{"timestamp": "2026-04-02T13:05:10+08:00", "event": "quick_language_detected", "languages": ["Java"], "framework": "Spring Boot"}
{"timestamp": "2026-04-02T13:05:15+08:00", "event": "quick_module_division", "modules": 3, "method": "directory_structure"}
{"timestamp": "2026-04-02T13:05:20+08:00", "event": "quick_attack_surface_sketched", "sources_found": 12, "sinks_found": 8}
{"timestamp": "2026-04-02T13:05:25+08:00", "event": "draft_documents_created", "files": ["workspace/00-work-background.md", "workspace/01-module-map.md"]}
{"timestamp": "2026-04-02T13:05:30+08:00", "event": "subagent_workspaces_created", "count": 3}
{"timestamp": "2026-04-02T13:05:35+08:00", "event": "phase_2a_prescan_completed", "duration_seconds": 35}
{"timestamp": "2026-04-02T13:05:40+08:00", "event": "subagent_started", "id": "agent-services", "module": "core/services/", "background_version": "draft"}
{"timestamp": "2026-04-02T13:05:42+08:00", "event": "subagent_started", "id": "agent-connector", "module": "core/connector/", "background_version": "draft"}
{"timestamp": "2026-04-02T13:05:44+08:00", "event": "subagent_started", "id": "agent-viewer", "module": "core/viewer/", "background_version": "draft"}
{"timestamp": "2026-04-02T13:05:45+08:00", "event": "phase_2b_deep_recon_started", "note": "与子代理审计并行"}
{"timestamp": "2026-04-02T13:10:00+08:00", "event": "code_graph_indexed", "functions": 1250, "calls": 3400}
{"timestamp": "2026-04-02T13:15:00+08:00", "event": "architecture_analyzed", "type": "MVC Web Application"}
{"timestamp": "2026-04-02T13:20:00+08:00", "event": "attack_surface_mapped", "sources": 28, "sinks": 18}
{"timestamp": "2026-04-02T13:25:00+08:00", "event": "module_deps_analyzed", "cross_module_calls": 45}
{"timestamp": "2026-04-02T13:25:05+08:00", "event": "phase_2b_deep_recon_completed", "duration_seconds": 1160}
{"timestamp": "2026-04-02T13:25:10+08:00", "event": "phase_2c_injection_started"}
{"timestamp": "2026-04-02T13:25:30+08:00", "event": "intelligence_injected", "target": "agent-services", "type": "deep_recon_results"}
{"timestamp": "2026-04-02T13:25:45+08:00", "event": "intelligence_injected", "target": "agent-connector", "type": "deep_recon_results"}
{"timestamp": "2026-04-02T13:26:00+08:00", "event": "phase_2c_injection_completed"}
{"timestamp": "2026-04-02T13:10:00+08:00", "event": "subagent_progress", "id": "agent-services", "phase": "phase_0_exploration", "files_scanned": 15}
{"timestamp": "2026-04-02T13:26:00+08:00", "event": "subagent_checked_update", "id": "agent-services", "background_version": "final"}
{"timestamp": "2026-04-02T13:30:00+08:00", "event": "vulnerability_found", "id": "agent-services", "type": "JCR SQL Injection", "cvss": 9.8}
{"timestamp": "2026-04-02T13:35:00+08:00", "event": "subagent_completed", "id": "agent-services", "vulnerabilities": 3}
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
  "status": "init|cloning|intelligence_gathering|auditing|poc_developing|verifying|reporting|completed|paused|failed"
}
```

### 审计阶段 (Phase)

```json
{
  "phase": "phase_1_init|phase_2_0_intelligence|phase_2a_prescan|phase_2b_deep_recon|phase_2c_injection|phase_2_discovery|phase_3_poc|phase_4_verification|phase_5_report"
}
```

- `phase_1_init`: 项目初始化
- `phase_2_0_intelligence`: CVE 情报收集 (仅专项审计模式)
- `phase_2a_prescan`: 快速预扫描 + 立即派发子代理 (5 分钟内完成)
- `phase_2b_deep_recon`: 深度侦察 (与子代理审计并行)
- `phase_2c_injection`: 增量情报注入 (深度侦察结果传递给子代理)
- `phase_2_discovery`: 子代理审计执行 (与 2B 并行，2C 后继续)
- `phase_3_poc`: POC 编写
- `phase_4_verification`: 验证测试
- `phase_5_report`: 总结报告

### 审计模式

```json
{
  "audit_mode": "standard|specialized",
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

- `standard`: 标准模式，直接进行代码审计
- `specialized`: 专项审计模式，先收集 CVE 情报再进行漏洞猎杀
- `cve_intelligence`: 仅专项审计模式下非 null
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
   {"event": "subagent_started", "id": "agent-xxx", "module": "...", "background_version": "draft"}
   ```

2. **检查 background.md 更新**:
   ```json
   {"event": "subagent_checked_update", "id": "agent-xxx", "background_version": "final"}
   ```

3. **进度更新** (每 5 分钟):
   ```json
   {"event": "subagent_progress", "id": "agent-xxx", "phase": "...", "progress": {...}}
   ```

4. **发现漏洞时报告**:
   ```json
   {"event": "vulnerability_found", "id": "agent-xxx", "type": "...", "cvss": X.X}
   ```

5. **完成时报告**:
   ```json
   {"event": "subagent_completed", "id": "agent-xxx", "vulnerabilities": N}
   ```

### MainAgent 并行工作流事件

```json
{"event": "phase_2a_prescan_started"}
{"event": "quick_language_detected", "languages": [...], "framework": "..."}
{"event": "quick_module_division", "modules": N, "method": "directory_structure"}
{"event": "quick_attack_surface_sketched", "sources_found": N, "sinks_found": N}
{"event": "draft_documents_created", "files": [...]}
{"event": "phase_2a_prescan_completed", "duration_seconds": N}
{"event": "phase_2b_deep_recon_started", "note": "与子代理审计并行"}
{"event": "code_graph_indexed", "functions": N, "calls": N}
{"event": "attack_surface_mapped", "sources": N, "sinks": N}
{"event": "module_deps_analyzed", "cross_module_calls": N}
{"event": "phase_2b_deep_recon_completed", "duration_seconds": N}
{"event": "phase_2c_injection_started"}
{"event": "intelligence_injected", "target": "agent-xxx", "type": "deep_recon_results"}
{"event": "phase_2c_injection_completed"}
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
| Phase 2A 完成后暂停 | 从 Phase 2B 开始深度侦察，子代理继续审计 |
| Phase 2B 进行中子代理失败 | 子代理重启，2B 继续并行执行 |
| Phase 2C 未完成 | 重新注入深度侦察结果到子代理 |
| 子 Agent 运行中 | 继续等待完成 |
| 子 Agent 失败 | 重启子 Agent（background.md 已为最新版本） |
| 阶段失败 | 重试阶段 |
| 项目暂停 | 从最近检查点恢复 |

### 并行工作流检查点保存时机

1. **Phase 2A 完成时** — 快速预扫描完成，子代理已派发
2. **Phase 2B 每完成一个子任务时** — 代码图谱索引完成、攻击面映射完成、模块依赖分析完成
3. **Phase 2C 每次注入时** — 每更新一个子代理的 background.md 后
4. **子 Agent 完成时** — 与原有流程相同
5. **发现高危漏洞时** — 与原有流程相同

---

**所有审计项目必须使用此状态格式** 🔒
