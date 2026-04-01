---
name: code-audit-system
description: Multi-agent code audit system for finding security vulnerabilities. Use when user provides a git repository URL for security auditing, code review for vulnerabilities, or wants to generate POCs for found vulnerabilities. This skill orchestrates subagents to analyze codebases, identify security issues (SQL injection, RCE, XSS, etc.), write exploit proofs-of-concept, and generate comprehensive vulnerability reports. ALWAYS use this skill when the user mentions code auditing, security analysis, vulnerability scanning, or provides a git URL for security review.
---

# Code Audit System - Multi-Agent Security Analysis

This skill orchestrates a multi-agent system to perform comprehensive security audits on codebases. It identifies vulnerabilities, writes proof-of-concept exploits, and generates detailed reports.

## When to Use This Skill

- User provides a git repository URL for security analysis
- User requests code auditing for vulnerabilities
- User wants to find security issues like SQL injection, RCE, XSS, etc.
- User needs POC (proof-of-concept) code for identified vulnerabilities
- User wants comprehensive vulnerability reports with exploitation details

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Agent                                │
│  - Orchestrates workflow                                         │
│  - Manages subagent workspaces                                   │
│  - Coordinates module detection                                  │
│  - Aggregates reports                                            │
│  - Interfaces with user                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  SubAgent 1   │   │   SubAgent 2    │   │  SubAgent N   │
│  Module A     │   │   Module B      │   │  Module N     │
│  Vulnerability│   │   Vulnerability │   │  Vulnerability│
│  Scanner      │   │   Scanner       │   │  Scanner      │
└───────────────┘   └─────────────────┘   └───────────────┘
```

## Workflow Overview

1. **Project Collection** - User provides git URLs
2. **Vulnerability Discovery** - SubAgents audit code modules
3. **Environment Deployment** (optional) - Docker setup
4. **POC Writing** - SubAgents write exploit scripts
5. **Verification** (optional) - Test POCs against deployed environment
6. **Summary Report** - MainAgent aggregates all findings

## Step-by-Step Instructions

### Step 1: Project Collection

When the user provides git repository URLs:

1. Create a project workspace directory: `~/code-audit-projects/<project-name>/`
2. Clone each repository:
   ```bash
   git clone <git-url> ~/code-audit-projects/<project-name>/source/
   ```
3. Create project structure:
   ```
   <project-name>/
   ├── source/          # Cloned source code
   ├── pocs/            # Proof-of-concept scripts
   ├── reports/         # Vulnerability reports
   └── workspace/       # SubAgent workspaces
   ```

**Read**: `references/project-structure.md` for detailed storage requirements.

### Step 2: Vulnerability Discovery (Main Process)

This is the core auditing phase. The MainAgent coordinates multiple SubAgents.

#### Phase 2.1: Technology Discovery

First, analyze the project to understand its technical background:

1. **Identify programming languages** - Scan file extensions, package files
2. **Detect frameworks and components** - Check package.json, requirements.txt, pom.xml, etc.
3. **Determine application type** - Web app, system service, GUI, mobile, etc.
4. **Map dependencies** - External libraries, databases, services

Create a **Work Background** document at `workspace/00-work-background.md` containing:
- Technology stack summary
- Application type classification
- Key components and frameworks
- Entry points and attack surface areas

**Use**: `references/module-detection.md` for module structure templates by project type.

#### Phase 2.2: Module Partitioning

Based on the technology discovery, partition the codebase into logical modules:

1. Identify module boundaries from directory structure
2. Map files to each module
3. Identify inter-module dependencies
4. Create module dependency graph

Store module mapping at `workspace/01-module-map.md`.

#### Phase 2.3: SubAgent Dispatch

For each module, create a dedicated SubAgent workspace:

```
workspace/
├── agent-<module-name>/
│   ├── skill.md           # Module-specific audit skill
│   ├── work-background.md # Technology context
│   ├── module-info.md     # Files, responsibilities
│   └── report.md          # Output: vulnerability findings
```

**Dispatch Strategy**:
- If modules have NO dependencies on each other → dispatch in parallel using thread pool
- If modules have dependencies → dispatch in dependency order

**Read**: `templates/subagent-skill-template.md` for creating SubAgent skills.

#### Phase 2.4: SubAgent Vulnerability Report

Each SubAgent must produce a report covering:

| Field | Description |
|-------|-------------|
| **Vulnerability Type** | SQL Injection, RCE, XSS, CSRF, SSRF, Path Traversal, etc. |
| **Authentication Required** | Yes/No/Partial |
| **Location** | File path and line numbers (e.g., `auth/login.py:45-52`) |
| **Trigger Description** | Call chain: function A → function B → vulnerability |
| **Severity** | Critical/High/Medium/Low |
| **CVSS Score** (optional) | Base score 0.0-10.0 |
| **Evidence** | Code snippets showing the vulnerability |

**Use**: `templates/vulnerability-report-template.md` for report format.

### Step 3: Environment Deployment (Optional - Ask User)

Before proceeding, ask the user:
> "Do you want to deploy the target application in a Docker environment for vulnerability verification? This allows testing POCs in an isolated environment."

If user confirms:

1. **Check for existing Docker config** - Look for Dockerfile, docker-compose.yml
2. **Create Docker environment** if none exists:
   - Analyze application dependencies
   - Write appropriate Dockerfile
   - Create docker-compose.yml with service dependencies (MySQL, Neo4j, etc.)

3. **Deploy using skills**:
   - Use `docker-essentials` skill for container setup
   - Use `docker-sandbox` skill for isolated testing environment

4. **Start the environment**:
   ```bash
   docker-compose up -d
   ```

**Store**: Docker configs at `workspace/docker/`

### Step 4: POC Writing

Dispatch SubAgents to write proof-of-concept exploits:

1. **Read vulnerability reports** from Step 2
2. **Create POC directory**: `<project-root>/pocs/`
3. **For each vulnerability**, create a Python script:
   - `poc-001-sql-injection-login.py`
   - `poc-002-rce-file-upload.py`
   - `poc-003-xss-search.py`

**POC Requirements**:
- Self-contained Python script
- Clear usage instructions in comments
- Configurable target URL/host
- Safe by default (doesn't cause damage)
- Demonstrates exploit clearly

**Read**: `templates/poc-template.py` for POC structure.

### Step 5: Vulnerability Verification (Optional - Ask User)

Ask the user:
> "Do you want to verify the POCs against the deployed environment? This will test if each exploit works and produce a verification report."

If user confirms:

1. **Deploy target** (not done in Step 3)
2. **Run each POC** in the docker-sandbox environment
3. **Record results**:
   - Success/Failure
   - Output/evidence
   - Time to exploit

4. **Create verification report**: `reports/verification-report.md`

Verification report extends vulnerability report with:
- Verification status: "成功" (Success) / "失败" (Failure)
- POC path: Full path to POC script
- Execution output: Terminal output from POC run
- Evidence: Screenshots, response data, etc.

### Step 6: Summary Report

MainAgent aggregates all findings into a comprehensive summary:

1. **Collect all reports**:
   - Individual vulnerability reports from SubAgents
   - POC verification results (if verified)

2. **Generate summary** at `reports/summary-report.md`:

```markdown
# Code Audit Summary Report

## Project Overview
- Repository: <git-url>
- Audit Date: <date>
- Total Modules Analyzed: <count>

## Executive Summary
- Total Vulnerabilities: <count>
- Critical: <count>
- High: <count>
- Medium: <count>
- Low: <count>

## Vulnerability Breakdown
| Type | Count | Verified |
|------|-------|----------|
| SQL Injection | 3 | 2/3 |
| RCE | 1 | 1/1 |
| XSS | 5 | 3/5 |

## Critical Findings
[List with severity and status]

## Recommendations
[Priority-ordered remediation steps]

## Appendix
- Full reports: reports/vulnerability-*.md
- POC scripts: pocs/
- Verification: reports/verification-report.md
```

3. **Store call graphs in Neo4j** (if implemented):
   - Function call chains leading to vulnerabilities
   - Data flow from input to sink

4. **Store structured data in MySQL** (if implemented):
   - Vulnerability metadata
   - POC metadata
   - Verification results

## Data Storage

### MySQL Schema (Structured Data)

Tables needed:
- `vulnerabilities` - Core vulnerability records
- `pocs` - POC script metadata
- `verifications` - Verification results
- `projects` - Project metadata

### Neo4j Schema (Relationship Data)

Model call chains as:
```
(Node:Function {name: "userInput", output: "string"})
  -[:CALLS]->
(Node:Function {name: "sanitize", output: "string"})
  -[:CALLS]->
(Node:Function {name: "executeQuery", output: "result"})
```

Each entity has:
- Properties for input parameters
- Output as property or edge label
- Source location (file:line)

## SubAgent Workspace Creation

For each SubAgent, create a dedicated workspace with:

1. **skill.md** - Module-specific audit instructions
2. **work-background.md** - Technology context
3. **module-info.md** - File list, responsibilities, interfaces
4. **report.md** - Output template

Use the `superpowers:dispatching-parallel-agents` skill when modules are independent.

## Error Handling

- **Clone failures**: Report to user, skip repository
- **SubAgent timeout**: Retry once, then mark as incomplete
- **Docker failures**: Fall back to static analysis only
- **POC execution errors**: Log output, mark verification as failed

## Output Delivery

Present to user:
1. Summary report (inline or as file)
2. Link to full reports directory
3. List of POC scripts created
4. (Optional) Verification results

---

## Related Templates and References

- `templates/vulnerability-report-template.md` - Report format
- `templates/poc-template.py` - POC script structure
- `templates/subagent-skill-template.md` - SubAgent skill template
- `references/module-detection.md` - Module detection by project type
- `references/project-structure.md` - Project storage structure
