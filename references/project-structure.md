# Project Structure Reference

## Directory Layout

```
~/code-audit-projects/<project-name>/
├── source/                 # Cloned source code from git
│   └── <repo contents>
├── pocs/                   # Proof-of-concept exploit scripts
│   ├── poc-001-sql-injection-login.py
│   ├── poc-002-rce-file-upload.py
│   └── poc-003-xss-search.py
├── reports/                # Vulnerability and summary reports
│   ├── vulnerability-001-sql-injection.md
│   ├── vulnerability-002-rce.md
│   ├── verification-report.md
│   └── summary-report.md
├── workspace/              # SubAgent workspaces
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   ├── agent-auth/
│   │   ├── skill.md
│   │   ├── work-background.md
│   │   ├── module-info.md
│   │   └── report.md
│   └── agent-api/
│       └── ...
├── docker/                 # Docker deployment configs
│   ├── Dockerfile
│   └── docker-compose.yml
└── metadata.json           # Project metadata
```

## metadata.json Schema

```json
{
  "project_name": "<name>",
  "git_url": "https://github.com/xxx/xxx.git",
  "clone_date": "2026-04-02T10:30:00Z",
  "commit_hash": "abc123...",
  "language": ["Python", "JavaScript"],
  "framework": ["Django", "React"],
  "app_type": "web-application",
  "modules": ["auth", "api", "frontend"],
  "vulnerabilities_found": 5,
  "pocs_written": 3,
  "verification_status": "pending"
}
```

## File Naming Conventions

### Vulnerability Reports
```
reports/vulnerability-<NNN>-<type>-<location>.md
Example: vulnerability-001-sql-injection-login.md
         vulnerability-002-rce-file-upload.md
```

### POC Scripts
```
pocs/poc-<NNN>-<type>-<location>.py
Example: poc-001-sql-injection-login.py
         poc-002-rce-file-upload.py
```

### SubAgent Workspaces
```
workspace/agent-<module-name>/
Example: workspace/agent-auth/
         workspace/agent-api/
         workspace/agent-frontend/
```

## Storage Requirements

1. **Source Code**: Always clone to `source/` - never modify original
2. **POCs**: All exploit scripts in `pocs/` with consistent naming
3. **Reports**: All reports in `reports/` with markdown format
4. **Workspaces**: Each SubAgent gets isolated workspace directory

## Cleanup

After audit completion, archive the project:
```bash
tar -czf <project-name>-audit-<date>.tar.gz ~/code-audit-projects/<project-name>/
```
