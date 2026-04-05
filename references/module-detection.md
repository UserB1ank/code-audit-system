# 模块检测参考文档

本参考帮助识别项目类型并将代码库划分为模块，以便分配给子 Agent 进行审计。

## 如何使用

1. 通过扫描根目录和关键文件**识别项目类型**
2. **匹配**最接近的模板
3. **根据实际结构调整** - 项目通常混合多种模式
4. 在 `workspace/01-module-map.md` **创建模块映射**

---

## 1. Web 应用（前后端分离）

**技术指示器**：
- 前端：`package.json` 含 react/vue/angular，`src/` 或 `app/` 含组件
- 后端：`requirements.txt`（Python）、`pom.xml`（Java）、`go.mod`（Go）、`Cargo.toml`（Rust）
- API：OpenAPI/Swagger 规范、REST 控制器
- 数据库：MySQL、PostgreSQL、MongoDB 配置

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| 前端 | `frontend/`、`web/`、`ui/` | UI、路由、状态 | XSS、CSRF、客户端逻辑 |
| API 层 | `backend/api/`、`controllers/` | HTTP 处理器、路由 | 输入验证、认证检查 |
| 服务层 | `backend/service/`、`services/` | 业务逻辑 | 授权、数据流 |
| 数据层 | `backend/repository/`、`dao/`、`models/` | 数据库访问 | SQL 注入、ORM 误用 |
| 中间件 | `backend/middleware/`、`middlewares/` | 认证、日志、CORS | 认证绕过、头注入 |
| 配置 | `backend/config/`、`config/` | 应用配置 | 秘密暴露、不安全默认值 |
| 数据库 | `database/`、`migrations/`、`db/` | 模式、种子 | 模式漏洞 |

---

## 2. 单体 Web 应用（MVC）

**技术指示器**：
- Spring Boot：`@SpringBootApplication`、`pom.xml` 含 spring-boot-starter
- Django：`manage.py`、`settings.py`、`urls.py`
- Rails：`Gemfile`、`config/routes.rb`、`app/controllers/`
- 模板：`.jsp`、`.ejs`、`.phtml`、`.erb`

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| 控制器 | `controllers/`、`app/controllers/` | 请求处理 | 输入验证、重定向 |
| 服务 | `services/`、`app/services/` | 业务逻辑 | 逻辑缺陷、授权 |
| 模型/仓库 | `models/`、`app/models/` | 数据实体 | 批量赋值、注入 |
| 视图 | `views/`、`templates/`、`app/views/` | 服务端渲染 HTML | 模板中的 XSS |
| 静态文件 | `public/`、`static/`、`assets/` | CSS、JS、图片 | 文件泄露 |
| 配置 | `config/` | 路由、环境配置 | 调试暴露、秘密 |
| 工具 | `utils/`、`lib/`、`helpers/` | 共享工具 | 反序列化、路径遍历 |

---

## 3. 系统应用（守护进程/CLI）

**技术指示器**：
- 语言：C、C++、Go、Rust
- 无 GUI，作为服务运行
- 配置文件：`.toml`、`.yaml`、`.ini`
- 协议：protobuf、thrift、gRPC

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| 入口点 | `cmd/`、`bin/`、`main/` | CLI 命令、main() | 命令注入、参数解析 |
| 核心守护进程 | `internal/daemon/`、`daemon/` | 生命周期管理 | 竞态条件、信号处理 |
| 服务器 | `internal/server/`、`server/` | 网络监听 | 网络漏洞、协议 bug |
| 配置解析器 | `internal/config/`、`config/` | 配置加载 | 路径遍历、不安全解析 |
| 插件 | `internal/plugins/`、`plugins/` | 动态扩展 | 代码注入、不安全加载 |
| API/协议 | `api/`、`proto/` | 协议定义 | 序列化漏洞 |
| 工具 | `pkg/`、`common/` | 共享库 | 内存安全（C/C++）|

---

## 4. GUI 桌面应用

**技术指示器**：
- Electron：`main.js`、`preload.js`、`package.json` 含 electron
- Qt：`.pro` 文件、`CMakeLists.txt` 含 Qt
- .NET WPF：`.csproj`、`App.xaml`、`MainWindow.xaml`
- GTK：`.glade` 文件、GTK 导入

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| 主进程 | `src/main/`、`main/` | 应用生命周期（Electron main）| IPC、原生模块加载 |
| 渲染器 | `src/renderer/`、`renderer/` | UI 渲染 | XSS、上下文隔离 |
| 组件 | `src/components/`、`components/` | 可复用 UI | 事件处理 |
| 服务 | `src/services/`、`services/` | 后端逻辑 | 本地存储、IPC |
| 资源 | `assets/`、`resources/` | 图标、主题 | 资源耗尽 |
| 原生绑定 | `native/`、`bridge/` | 原生绑定 | 内存损坏 |

---

## 5. 移动应用

**技术指示器**：
- Android：`build.gradle`、`AndroidManifest.xml`、`app/src/main/`
- iOS：`.xcodeproj`、`Podfile`、`Info.plist`
- 跨平台：`flutter.yaml`、`react-native.config.js`

**模块划分（Android 示例）**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| UI 层 | `app/src/main/java/*/ui/` | Activities、Fragments | Intent 注入、深链接 |
| 数据层 | `app/src/main/java/*/data/` | Repositories、Room DAO | SQL 注入、不安全存储 |
| 领域层 | `app/src/main/java/*/domain/` | UseCases、业务逻辑 | 逻辑缺陷 |
| DI 模块 | `app/src/main/java/*/di/` | 依赖注入 | 组件暴露 |
| 资源 | `app/src/main/res/` | 布局、字符串 | 硬编码秘密 |
| 网络 | `app/src/main/java/*/network/` | API 客户端 | SSL pinning、证书处理 |

---

## 6. 微服务架构

**技术指示器**：
- 多个服务目录在 `services/` 下
- docker-compose.yml、Kubernetes 清单
- gRPC/protobuf、REST API
- 服务网格配置（Istio、Linkerd）

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| 用户服务 | `services/user-service/` | 用户管理 | 认证、数据暴露 |
| 订单服务 | `services/order-service/` | 订单处理 | 业务逻辑、注入 |
| 支付服务 | `services/payment-service/` | 支付处理 | 加密、PCI 合规 |
| API 网关 | `gateway/`、`api-gateway/` | 请求路由 | 认证绕过、限速 |
| 共享库 | `libs/`、`shared/` | 共享工具 | 跨服务共享漏洞 |
| 部署配置 | `deploy/`、`k8s/`、`docker/` | K8s YAML、Dockerfile | 容器逃逸、秘密 |

---

## 7. 数据管道 / ETL

**技术指示器**：
- Python/Scala 加 pyspark、spark、flink
- Airflow：`dags/` 目录
- Jupyter notebooks：`notebooks/`
- 数据库连接器：SQLAlchemy、JDBC

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| Extract | `extract/`、`ingestion/` | 数据源连接器 | 凭证处理、注入 |
| Transform | `transform/`、`processing/` | 数据清洗、转换 | 通过数据的代码注入 |
| Load | `load/`、`writers/` | 数据输出写入 | SQL 注入、文件写入 |
| Jobs | `jobs/`、`workflows/` | 作业定义 | 工作流逻辑 |
| DAGs | `dags/` | Airflow DAG | 任务注入 |
| 配置 | `config/` | 连接字符串 | 秘密管理 |
| 工具 | `utils/`、`common/` | 辅助函数 | 共享漏洞 |

---

## 8. 库 / SDK

**技术指示器**：
- Python：`setup.py`、`pyproject.toml`
- NPM：`package.json` 含 `main` 字段
- Java：`.jar` 发布、Maven Central
- 示例：`examples/`、`sample/`

**模块划分**：

| 模块 | 路径模式 | 职责 | 审计重点 |
|------|----------|------|----------|
| 核心 | `src/core/`、`src/main/` | 主要功能 | 输入验证 |
| API | `src/api/`、`public/` | 公共接口 | 接口安全 |
| 额外功能 | `src/extras/`、`optional/` | 可选功能 | 功能特定漏洞 |
| 示例 | `examples/`、`samples/` | 使用演示 | 不安全示例 |
| 测试 | `tests/`、`test/` | 单元/集成测试 | 测试数据暴露 |
| 基准测试 | `benchmarks/`、`perf/` | 性能测试 | 通过资源耗尽的 DoS |

---

## 混合项目类型

项目通常组合多种模式。常见组合：

| 组合 | 示例 | 方法 |
|------|------|------|
| Web + CLI | 带 `manage.py` 的 Django 应用 | 视为 MVC，添加 CLI 模块 |
| 微服务 + 数据 | 带 ETL 作业的用户服务 | 按服务拆分，再按数据模块 |
| 桌面 + Web | 带后端的 Electron 应用 | 分开主进程/渲染器，分别审计后端 |
| 移动 + SDK | 使用自定义 SDK 的 Android 应用 | 将应用和 SDK 作为独立模块审计 |

---

## 快速识别检查清单

扫描这些文件以识别项目类型：

| 文件 | 指示 |
|------|------|
| `package.json` | Node.js、Electron、React、Vue |
| `requirements.txt` 或 `setup.py` | Python |
| `pom.xml` 或 `build.gradle` | Java、Android |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Gemfile` | Ruby、Rails |
| `composer.json` | PHP |
| `mix.exs` | Elixir |
| `pubspec.yaml` | Flutter/Dart |
| `CMakeLists.txt` | C/C++ |
| `*.xcodeproj` | iOS/macOS |
| `AndroidManifest.xml` | Android |
| `docker-compose.yml` | 多服务 |
| `Dockerfile` | 容器化应用 |

---

## 划分后的下一步

1. 创建 `workspace/01-module-map.md` 包含文件分配
2. 为每个模块创建子 Agent 工作区
3. 将本参考的相关部分复制到每个子 Agent 的 `background.md`
4. 使用模块特定指令调度子 Agent
