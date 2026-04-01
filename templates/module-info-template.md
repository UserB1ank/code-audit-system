# Module Information - [Module Name]

## Module Overview

**Module Name:** [name]
**Assigned Agent:** SubAgent-[name]
**Workspace:** `workspace/agent-[name]/`

---

## Responsibilities

[Describe what this module is responsible for in the application]

Example:
- Handle user authentication and authorization
- Process HTTP API requests
- Manage database connections
- Render user interface components

---

## Files in This Module

| File | Lines | Purpose | Priority |
|------|-------|---------|----------|
| `path/to/file1.py` | 150 | Login handler | High |
| `path/to/file2.py` | 89 | Session management | High |
| `path/to/file3.py` | 45 | Utility functions | Medium |

---

## Entry Points

Functions/methods that accept external input:

| Function | Location | Input Type |
|----------|----------|------------|
| `login_handler()` | `file1.py:15` | HTTP POST body |
| `search()` | `file2.py:30` | Query parameter |
| `upload_file()` | `file3.py:10` | File upload |

---

## Data Flow

```
[Input Source]
    ↓
[Entry Point Function]
    ↓
[Processing Functions]
    ↓
[Sink Function]
```

### Specific Data Flows for This Module

1. **Authentication Flow:**
   ```
   POST /login
       ↓
   login_handler(request)
       ↓
   validate_credentials(user, pass)
       ↓
   create_session(user_id)
       ↓
   Set-Cookie header
   ```

2. **[Flow Name]:**
   ```
   [Describe flow]
   ```

---

## Security Sinks

Functions that perform sensitive operations:

| Sink | Location | Operation |
|------|----------|-----------|
| `db.execute()` | `db.py:45` | SQL queries |
| `os.system()` | `utils.py:20` | System commands |
| `render_template()` | `views.py:30` | HTML output |

---

## Known Security Controls

| Control | Implementation | Location |
|---------|----------------|----------|
| Input sanitization | `sanitize_input()` | `utils.py:5-15` |
| Authentication check | `@require_auth` decorator | `auth.py:10` |
| CSRF token | `csrf_protect()` middleware | `middleware.py:25` |

---

## Vulnerability Focus Areas

Based on module analysis, focus audit efforts on:

1. **[Vulnerability Type 1]**
   - Why: [reason]
   - Files: [file list]

2. **[Vulnerability Type 2]**
   - Why: [reason]
   - Files: [file list]

---

## Inter-Module Dependencies

| Dependent Module | Relationship | Data Shared |
|------------------|--------------|-------------|
| [Module A] | Calls this module | User credentials |
| [Module B] | Called by this module | Query results |

---

## Test Coverage

| File | Tests Exist | Coverage |
|------|-------------|----------|
| `file1.py` | Yes/No | N/A |
| `file2.py` | Yes/No | N/A |

---

## Notes for Auditor

- [Special consideration 1]
- [Special consideration 2]
- [Areas requiring extra scrutiny]

---

## Deliverables

1. Complete static analysis of all files listed above
2. Document all vulnerabilities found using `templates/vulnerability-report-template.md`
3. Save reports to `workspace/agent-[name]/`
4. Notify MainAgent of Critical findings immediately
