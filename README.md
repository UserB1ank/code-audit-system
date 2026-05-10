# Code Audit System — Multi-Agent CVE Discovery Engine

A **CVE-oriented multi-agent code audit system** implemented as a Claude Code skill. It orchestrates parallel subagents to discover exploitable vulnerabilities in git repositories, write weaponized POCs, verify them against live deployments, and generate CVE-ready reports.

> **Core philosophy**: Only report actually exploitable vulnerabilities. The goal is CVE submission, not making code safer.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     MainAgent (Orchestrator)              │
│  · Fast pre-scan → immediate subagent dispatch            │
│  · Deep reconnaissance (parallel with subagents)          │
│  · Incremental intelligence injection into subagents      │
│  · Workspace & state management                           │
│  · Final report aggregation                               │
└──────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Subagent 1  │  │  Subagent 2  │  │  Subagent N  │
│  Module A    │  │  Module B    │  │  Module N    │
│              │  │              │  │              │
│  Recon       │  │  Recon       │  │  Recon       │
│  Source→Sink │  │  Source→Sink │  │  Source→Sink │
│  Exploit Eval│  │  Exploit Eval│  │  Exploit Eval│
│  CVE Report  │  │  CVE Report  │  │  CVE Report  │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Key Features

- **Parallel subagent auditing** — modules are audited simultaneously, not sequentially
- **Two audit modes** — Standard (direct code audit) and Specialized (CVE-history-driven hunting)
- **Graph-enhanced reconnaissance** — `codebase-memory` MCP builds code knowledge graphs for Source→Sink tracing
- **Incremental intelligence injection** — MainAgent feeds deep recon findings to subagents mid-audit
- **Live POC verification** — deploy targets via Docker, verify exploits against real running services
- **Strict exploitability filter** — theoretical/blocked issues are discarded; only verifiable exploits are reported
- **Crash recovery** — state files enable checkpointing and resume

## Workflow

```
Standard:   Init → Pre-scan → Subagent Audit (parallel) → POC → Verify → Report
                                   ↗ MainAgent Deep Recon (parallel) ↗

Specialized: Init → CVE Intel → Pre-scan → Subagent Audit (parallel) → POC → Verify → Report
                                               ↗ MainAgent Deep Recon (parallel) ↗
```

### Phase 1 — Project Initialization
Clone target repo into `source/`, create `metadata.json`, state files, and workspace skeleton.

### Phase 2 — CVE Discovery (Core)
- **2A (Fast Pre-scan)**: Language/framework detection, rough module partitioning, attack surface sketch. Immediately dispatch all subagents in parallel.
- **2B (Deep Recon)**: MainAgent builds code knowledge graphs via `codebase-memory` MCP, performs deep attack surface mapping and module dependency analysis — all in parallel with subagent auditing.
- **2C (Incremental Injection)**: Deep recon findings are pushed to subagents' background documents as they work.
- **2.3 (Subagent Audit)**: Each subagent performs 4-phase audit (recon → deep dive → exploitability assessment → CVE report).
- **2.4 (Reporting)**: CVE-ready reports with Source→Sink call chains, CVSS scoring, and exploitability verdict.

### Phase 3 — Environment Deployment (optional)
Deploy target application in Docker for POC verification.

### Phase 4 — POC Writing
Write weaponized Python exploit scripts for CVE-level vulnerabilities.

### Phase 5 — Verification (optional)
Test POCs against deployed environment. **Source-code-only verification is not accepted** — exploits must be validated against a running instance. If verification is not possible, that is stated plainly.

### Phase 6 — Summary Report
Aggregate all verified findings into a CVE submission package.

## Audit Modes

| Mode | When to Use | Extra Steps | Advantage |
|------|-------------|-------------|-----------|
| **Standard** | First-time audit, internal projects, no CVE history | None | Fast start, simple flow |
| **Specialized** | Known open-source products, existing CVE history | Phase 2.0: CVE intelligence gathering via `cve-search` | History-driven定向 hunting, higher discovery rate |

Specialized mode triggers automatically for well-known open-source organizations (Apache, Spring, WordPress, etc.) or when the user explicitly requests it.

## Usage Example

Invoke the skill with a git repository URL:

```
/code-audit-system https://github.com/InsForge/InsForge.git 专项审计
```

### Full Audit Walkthrough

```bash
# 1. Project initialization — clone target into isolated workspace
mkdir -p code-audit-projects/InsForge/{source,state,workspace,pocs,reports,docker}
git clone https://github.com/InsForge/InsForge.git code-audit-projects/InsForge/source/

# 2. CVE intelligence (Specialized mode) — query historical CVEs
#    Uses cve-search MCP to gather vendor/product CVE history,
#    analyze attack patterns, and fit them to current codebase

# 3. Fast pre-scan + subagent dispatch
#    MainAgent identifies tech stack, partitions modules,
#    dispatches subagents in parallel immediately

# 4. Deep reconnaissance (parallel with subagents)
#    MainAgent uses codebase-memory MCP to build code knowledge graph,
#    performs deep Source→Sink mapping, injects findings into subagents

# 5. POC development for confirmed vulnerabilities

# 6. Environment deployment for verification
#    Deploy target on a verification host (e.g., Debian-based POC environment)
#    Submit exploit requests from analysis host to verify vulnerabilities:
#
#    ssh verifier@<poc-host> "sudo docker compose -f /path/to/docker-compose.yml up -d"
#    python poc-001-rce.py --target http://<poc-host>:8080
#
#    Source-code review alone is NOT sufficient — only runtime POC
#    verification counts. If unverifiable, report it as unverified.

# 7. Generate CVE submission reports for verified vulnerabilities
```

### Verification Environment

The system supports deploying targets on a dedicated POC verification host:

- **Deployment**: Docker-based, via `docker compose` on the verification host
- **Connectivity**: SSH from analysis workstation to verification host for command execution and HTTP for exploit delivery
- **Privilege**: passwordless `sudo` on verification host for container lifecycle management
- **Principle**: Only vulnerabilities confirmed via runtime POC execution are included in final CVE reports. Static analysis findings without live verification are marked as unverified.

> **Note**: Verification host credentials and network details are configured per-deployment and not stored in this repository.

## CVE Submission Threshold

| Criterion | Requirement |
|-----------|------------|
| CVSS Score | ≥ 7.0 (High/Critical) |
| Exploitability | Must have complete Source→Sink call chain |
| POC | Must be weaponized and functional |
| Impact | Affects real users (not local/test-only) |
| Version | Clearly identified affected versions |

## Project Structure

```
code-audit-projects/<project-name>/
├── source/                  # Cloned source code (git clone MUST target this)
├── state/                   # Audit state & task history (checkpoint recovery)
│   ├── audit-state.json
│   └── task-history.jsonl
├── workspace/               # Subagent workspaces
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   └── agent-<module>/
│       ├── background.md
│       ├── skill.md
│       └── report.md
├── pocs/                    # Weaponized POC scripts
├── reports/                 # CVE submission reports
├── docker/                  # Docker deployment configs
└── metadata.json
```

## MCP Integrations

| MCP Server | Purpose |
|-----------|---------|
| `codebase-memory` | Build code knowledge graphs, enable Source→Sink tracing across module boundaries |
| `cve-search` | Query historical CVE data for specialized audit mode, analyze attack patterns |

## Language-Specific Vulnerability Guides

| Language | Coverage |
|----------|----------|
| Python | SQL injection, command injection, path traversal, deserialization, SSTI, XXE, SSRF |
| PHP | SQL injection, command injection, file inclusion, XSS, deserialization, path traversal, SSRF |
| Java | SQL injection, command injection, XXE, deserialization, path traversal, SSRF, SSTI, JNDI injection |
| Rust | Unsoundness, concurrency races, resource exhaustion, integer/buffer issues, supply chain |

## Deliverables

1. **CVE Submission Report** — aggregated report with Executive Summary, CVE candidate table, and detailed per-vulnerability analysis
2. **Per-Vulnerability Reports** — individual CVE reports with Source→Sink chains, CVSS vectors, and evidence
3. **Weaponized POC Scripts** — self-contained Python exploit scripts
4. **Verification Reports** — per-vulnerability verification results against live deployments

## File Map

```
SKILL.md                         # Core skill definition — full audit workflow
references/                      # Language guides & operational references
  ├── python-guide.md            # Python vulnerability patterns
  ├── php-guide.md               # PHP vulnerability patterns
  ├── java-guide.md              # Java vulnerability patterns
  ├── rust-guide.md              # Rust vulnerability patterns
  ├── module-detection.md        # Module partitioning by project type
  ├── project-structure.md       # Standard directory layout
  ├── parallel-audit-workflow.md # Phase 2A/2B/2C parallel audit details
  ├── subagent-guide.md          # Subagent background doc creation
  ├── phase1-project-init.md     # Initialization detailed steps
  ├── phase2-cve-intelligence.md # CVE intelligence gathering (specialized mode)
  ├── phases-3to6.md             # Deployment, POC, verification, reporting
  ├── cve-intelligence-guide.md  # CVE intelligence methodology
  └── operations.md              # Error handling, reminders, deliverables
templates/                       # Output templates
  ├── vulnerability-report-template.md
  ├── subagent-skill-template.md
  ├── subagent-background-template.md
  ├── summary-report-template.md
  ├── verification-report-template.md
  ├── poc-template.py
  └── ...
state/                           # State schema
  └── audit-state-schema.md
evals/                           # Trigger evaluation test cases
  ├── evals.json
  └── trigger-evals.json
```

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Git
- Docker (for POC verification)
- Python 3.x (for POC execution)
- MCP servers: `codebase-memory`, `cve-search` (optional, for specialized mode)

## License

This project is a skill definition for Claude Code. Use at your own risk. The system is designed for authorized security testing and vulnerability research only.
