# Module Detection Reference

This reference helps identify project types and partition codebases into modules for SubAgent assignment.

## How to Use

1. **Identify project type** by scanning root directory and key files
2. **Match to closest template** below
3. **Adapt based on actual structure** - projects often mix patterns
4. **Create module map** at `workspace/01-module-map.md`

---

## 1. Web Application (Frontend + Backend Separated)

**Technology Indicators**:
- Frontend: `package.json` with react/vue/angular, `src/` or `app/` containing components
- Backend: `requirements.txt` (Python), `pom.xml` (Java), `go.mod` (Go), `Cargo.toml` (Rust)
- API: OpenAPI/Swagger specs, REST controllers
- Database: MySQL, PostgreSQL, MongoDB configs

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| Frontend | `frontend/`, `web/`, `ui/` | UI, routing, state | XSS, CSRF, client-side logic |
| API Layer | `backend/api/`, `controllers/` | HTTP handlers, routing | Input validation, auth checks |
| Service Layer | `backend/service/`, `services/` | Business logic | Authorization, data flow |
| Data Layer | `backend/repository/`, `dao/`, `models/` | DB access | SQL injection, ORM misuse |
| Middleware | `backend/middleware/`, `middlewares/` | Auth, logging, CORS | Auth bypass, header injection |
| Config | `backend/config/`, `config/` | App configuration | Secret exposure, insecure defaults |
| Database | `database/`, `migrations/`, `db/` | Schema, seeds | Schema vulnerabilities |

---

## 2. Monolithic Web Application (MVC)

**Technology Indicators**:
- Spring Boot: `@SpringBootApplication`, `pom.xml` with spring-boot-starter
- Django: `manage.py`, `settings.py`, `urls.py`
- Rails: `Gemfile`, `config/routes.rb`, `app/controllers/`
- Templates: `.jsp`, `.ejs`, `.phtml`, `.erb`

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| Controllers | `controllers/`, `app/controllers/` | Request handling | Input validation, redirects |
| Services | `services/`, `app/services/` | Business logic | Logic flaws, authz |
| Models/Repositories | `models/`, `app/models/` | Data entities | Mass assignment, injection |
| Views | `views/`, `templates/`, `app/views/` | Server-rendered HTML | XSS in templates |
| Static | `public/`, `static/`, `assets/` | CSS, JS, images | File disclosure |
| Config | `config/` | Routes, env config | Debug exposure, secrets |
| Utils | `utils/`, `lib/`, `helpers/` | Shared utilities | Deserialization, path traversal |

---

## 3. System Application (Daemon/CLI)

**Technology Indicators**:
- Languages: C, C++, Go, Rust
- No GUI, runs as service
- Config files: `.toml`, `.yaml`, `.ini`
- Protocol: protobuf, thrift, gRPC

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| Entry Points | `cmd/`, `bin/`, `main/` | CLI commands, main() | Command injection, args parsing |
| Core Daemon | `internal/daemon/`, `daemon/` | Lifecycle management | Race conditions, signal handling |
| Server | `internal/server/`, `server/` | Network listeners | Network vulns, protocol bugs |
| Config Parser | `internal/config/`, `config/` | Config loading | Path traversal, insecure parsing |
| Plugins | `internal/plugins/`, `plugins/` | Dynamic extensions | Code injection, unsafe loading |
| API/Protocol | `api/`, `proto/` | Protocol definitions | Serialization bugs |
| Utils | `pkg/`, `common/` | Shared libraries | Memory safety (C/C++) |

---

## 4. GUI Desktop Application

**Technology Indicators**:
- Electron: `main.js`, `preload.js`, `package.json` with electron
- Qt: `.pro` files, `CMakeLists.txt` with Qt
- .NET WPF: `.csproj`, `App.xaml`, `MainWindow.xaml`
- GTK: `.glade` files, GTK imports

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| Main Process | `src/main/`, `main/` | App lifecycle (Electron main) | IPC, native module loading |
| Renderer | `src/renderer/`, `renderer/` | UI rendering | XSS, context isolation |
| Components | `src/components/`, `components/` | Reusable UI | Event handling |
| Services | `src/services/`, `services/` | Backend logic | Local storage, IPC |
| Resources | `assets/`, `resources/` | Icons, themes | Resource exhaustion |
| Native | `native/`, `bridge/` | Native bindings | Memory corruption |

---

## 5. Mobile Application

**Technology Indicators**:
- Android: `build.gradle`, `AndroidManifest.xml`, `app/src/main/`
- iOS: `.xcodeproj`, `Podfile`, `Info.plist`
- Cross-platform: `flutter.yaml`, `react-native.config.js`

**Module Partition (Android Example)**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| UI Layer | `app/src/main/java/*/ui/` | Activities, Fragments | Intent injection, deep links |
| Data Layer | `app/src/main/java/*/data/` | Repositories, Room DAO | SQL injection, insecure storage |
| Domain Layer | `app/src/main/java/*/domain/` | UseCases, business logic | Logic flaws |
| DI Module | `app/src/main/java/*/di/` | Dependency injection | Component exposure |
| Resources | `app/src/main/res/` | Layouts, strings | Hardcoded secrets |
| Network | `app/src/main/java/*/network/` | API clients | SSL pinning, cert handling |

---

## 6. Microservices Architecture

**Technology Indicators**:
- Multiple service directories under `services/`
- docker-compose.yml, Kubernetes manifests
- gRPC/protobuf, REST APIs
- Service mesh configs (Istio, Linkerd)

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| User Service | `services/user-service/` | User management | Auth, data exposure |
| Order Service | `services/order-service/` | Order processing | Business logic, injection |
| Payment Service | `services/payment-service/` | Payment handling | Crypto, PCI compliance |
| API Gateway | `gateway/`, `api-gateway/` | Request routing | Auth bypass, rate limiting |
| Shared Libs | `libs/`, `shared/` | Common utilities | Shared vulns across services |
| Deploy Config | `deploy/`, `k8s/`, `docker/` | K8s YAML, Dockerfiles | Container escapes, secrets |

---

## 7. Data Pipeline / ETL

**Technology Indicators**:
- Python/Scala with pyspark, spark, flink
- Airflow: `dags/` directory
- Jupyter notebooks: `notebooks/`
- Database connectors: SQLAlchemy, JDBC

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| Extract | `extract/`, `ingestion/` | Data source connectors | Credential handling, injection |
| Transform | `transform/`, `processing/` | Data cleaning, transformation | Code injection via data |
| Load | `load/`, `writers/` | Data output writers | SQL injection, file writes |
| Jobs | `jobs/`, `workflows/` | Job definitions | Workflow logic |
| DAGs | `dags/` | Airflow DAGs | Task injection |
| Config | `config/` | Connection strings | Secret management |
| Utils | `utils/`, `common/` | Helper functions | Shared vulnerabilities |

---

## 8. Library / SDK

**Technology Indicators**:
- Python: `setup.py`, `pyproject.toml`
- NPM: `package.json` with `main` field
- Java: `.jar` publishing, Maven Central
- Examples: `examples/`, `sample/`

**Module Partition**:

| Module | Path Pattern | Responsibility | Audit Focus |
|--------|--------------|----------------|-------------|
| Core | `src/core/`, `src/main/` | Main functionality | Input validation |
| API | `src/api/`, `public/` | Public interface | Interface safety |
| Extras | `src/extras/`, `optional/` | Optional features | Feature-specific vulns |
| Examples | `examples/`, `samples/` | Usage demos | Insecure examples |
| Tests | `tests/`, `test/` | Unit/integration tests | Test data exposure |
| Benchmarks | `benchmarks/`, `perf/` | Performance tests | DoS via resource exhaustion |

---

## Mixed Project Types

Projects often combine multiple patterns. Common combinations:

| Combination | Example | Approach |
|-------------|---------|----------|
| Web + CLI | Django app with `manage.py` | Treat as MVC, add CLI module |
| Microservice + Data | User service with ETL jobs | Split by service, then by data modules |
| Desktop + Web | Electron app with backend | Separate main/renderer, audit backend separately |
| Mobile + SDK | Android app using custom SDK | Audit app and SDK as separate modules |

---

## Quick Identification Checklist

Scan these files to identify project type:

| File | Indicates |
|------|-----------|
| `package.json` | Node.js, Electron, React, Vue |
| `requirements.txt` or `setup.py` | Python |
| `pom.xml` or `build.gradle` | Java, Android |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Gemfile` | Ruby, Rails |
| `composer.json` | PHP |
| `mix.exs` | Elixir |
| `pubspec.yaml` | Flutter/Dart |
| `CMakeLists.txt` | C/C++ |
| `*.xcodeproj` | iOS/macOS |
| `AndroidManifest.xml` | Android |
| `docker-compose.yml` | Multi-service |
| `Dockerfile` | Containerized app |

---

## Next Steps After Partitioning

1. Create `workspace/01-module-map.md` with file assignments
2. For each module, create SubAgent workspace
3. Copy relevant section of this reference to each SubAgent's `work-background.md`
4. Dispatch SubAgents with module-specific instructions
