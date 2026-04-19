# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **CVE-oriented multi-agent code audit system** implemented as a Claude Code skill (`SKILL.md`). It is not a traditional codebase with build/test/lint commands — it is a declarative skill definition that orchestrates subagents to discover exploitable vulnerabilities in git repositories, write weaponized POCs, and generate CVE-ready reports.

The system has no runtime, no package dependencies, and no executable code. It operates entirely through Claude's agent orchestration capabilities.

## Architecture

### Main Agent (Orchestrator)

The MainAgent drives a 6-step workflow defined in `SKILL.md`:

1. **Project Initialization** — Clone target repo into `code-audit-projects/<name>/source/`, create `metadata.json`, state files, and workspace
2. **CVE Discovery** — Technology reconnaissance, module partitioning, subagent dispatch, vulnerability reporting
3. **Environment Deployment** (optional) — Docker setup for POC verification
4. **POC Writing** — Weaponized Python exploit scripts
5. **Verification** (optional) — Test POCs against deployed environment
6. **Summary Report** — Aggregate into CVE submission package

### SubAgents (CVE Hunters)

Each module gets a dedicated subagent with its own workspace under `workspace/agent-<module>/`. Subagents follow a 4-phase audit process: reconnaissance, deep dive (Source→Sink tracing), exploitability assessment, and CVE-ready reporting.

### Key Design Constraints

- **Only report exploitable vulnerabilities** with complete Source→Sink call chains, no theoretical issues
- **CVE submission threshold**: CVSS >= 7.0
- `git clone` must target `source/` subdirectory, never the project root
- State files (`state/audit-state.json`, `state/task-history.jsonl`) enable crash recovery and checkpointing

## File Organization

| Directory | Purpose |
|-----------|---------|
| `SKILL.md` | Main skill definition — the entire audit workflow and rules |
| `references/` | Language-specific vulnerability guides (`php-guide.md`, `java-guide.md`) and project analysis references (`module-detection.md`, `project-structure.md`) |
| `templates/` | Output templates for reports, POCs, subagent configs, execution logs, and background docs |
| `state/` | State file schema (`audit-state-schema.md`) |
| `evals/` | Skill trigger evaluation test cases (`evals.json`, `trigger-evals.json`) |
| `scripts/`, `assets/` | Empty; reserved for future use |

## Key References Used During Audits

- `references/php-guide.md` — PHP vulnerability patterns (SQLi, command injection, file inclusion, deserialization, etc.) with Source→Sink examples
- `references/java-guide.md` — Java vulnerability patterns (SQLi, XXE, deserialization, JNDI injection, Spring-specific issues)
- `references/module-detection.md` — How to partition projects into modules by type (web app, monolith, system daemon, GUI, mobile, microservices, ETL, library)
- `state/audit-state-schema.md` — Full JSON schema for audit state tracking and checkpoint recovery

## Workflow State Machine

Project status: `init → cloning → auditing → poc_developing → verifying → reporting → completed`
Phase status: `pending → in_progress → completed` (or `failed`/`skipped`)
Subagent status: `pending → running → completed` (or `failed`/`timeout`)

## Language

The skill definition, templates, and references are primarily written in **Chinese** with English technical terms. Subagent outputs (reports, POCs) use English for CVE submission compatibility.
