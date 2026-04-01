# Work Background - [Project Name]

## Project Overview

**Repository:** [Git URL]
**Analysis Date:** [Date]
**Analyzed By:** MainAgent

---

## Technology Stack

### Programming Languages

| Language | Version | Files |
|----------|---------|-------|
| [e.g., Python] | [e.g., 3.9] | [count] |
| [e.g., JavaScript] | [e.g., ES2020] | [count] |

### Frameworks and Libraries

| Framework/Library | Version | Purpose |
|-------------------|---------|---------|
| [e.g., Django] | [e.g., 4.2] | Web framework |
| [e.g., React] | [e.g., 18.2] | Frontend UI |

### Database

| Database | Version | Usage |
|----------|---------|-------|
| [e.g., PostgreSQL] | [e.g., 15] | Primary data store |
| [e.g., Redis] | [e.g., 7] | Cache/session |

### External Services

| Service | Purpose |
|---------|---------|
| [e.g., AWS S3] | File storage |
| [e.g., Stripe] | Payment processing |

---

## Application Type

**Primary Classification:** [Web Application / System Service / GUI App / Mobile App / Other]

**Architecture:** [Monolith / Microservices / Serverless / Hybrid]

**Deployment:** [Docker / VM / Bare Metal / Cloud Native]

---

## Key Components

### Entry Points

| Component | Location | Description |
|-----------|----------|-------------|
| HTTP Server | `server.py:main()` | Main web server |
| API Routes | `api/routes.py` | REST API endpoints |
| CLI Commands | `cmd/main.go` | Command-line interface |

### Attack Surface Areas

1. **HTTP endpoints** - [count] routes accepting user input
2. **File uploads** - [locations]
3. **Authentication** - [login/register/password reset endpoints]
4. **Database** - [query patterns]
5. **External integrations** - [APIs called]

---

## Security-Relevant Patterns

### Authentication Method
[JWT / Session-based / OAuth / API Keys / None]

### Authorization Pattern
[RBAC / ABAC / ACL / None detected]

### Input Handling
[Sanitization library used / Manual sanitization / None detected]

### Cryptography
[Libraries and algorithms in use]

---

## Module Partition Summary

| Module | Files | Responsibility | Assigned To |
|--------|-------|----------------|-------------|
| [Module 1] | [count] | [Description] | SubAgent-1 |
| [Module 2] | [count] | [Description] | SubAgent-2 |
| [Module 3] | [count] | [Description] | SubAgent-3 |

---

## Notes for SubAgents

### Module-Specific Concerns

**For API Module:**
- Watch for: SQL injection, auth bypass, IDOR
- Key files: `api/*.py`, `handlers/*.go`

**For Frontend Module:**
- Watch for: XSS, CSRF, client-side logic flaws
- Key files: `src/**/*.jsx`, `components/**/*.vue`

**For Auth Module:**
- Watch for: Weak password hashing, session fixation
- Key files: `auth/*.py`, `middleware/auth.*`

---

## Files for Detailed Analysis

### High Priority (Direct External Input)
1. `[file_path]` - Handles [input type]
2. `[file_path]` - Manages [sensitive operation]

### Medium Priority (Internal Processing)
1. `[file_path]` - Processes [data type]
2. `[file_path]` - Implements [business logic]

### Low Priority (Utility/Support)
1. `[file_path]` - Provides [utility function]

---

## Next Steps

1. Each SubAgent should read their module-specific `module-info.md`
2. Follow the vulnerability checklist in your assigned `skill.md`
3. Report findings to `workspace/agent-<module>/report.md`
4. Notify MainAgent of Critical findings immediately
