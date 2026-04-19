# Code Audit System - CVE 发现引擎

以 CVE 为导向的多 Agent 代码审计系统，协调子 Agent 发现可利用漏洞（RCE、SQLi、Auth Bypass 等）、编写武器化 POC、生成 CVE 就绪报告。

## 核心理念

**只报告可实际利用的漏洞，目标是提交 CVE，而非让代码变得更安全。**

- 必须有明确用户输入入口（Source）
- 必须有完整调用链（Source -> Sink）
- 无有效安全控制阻断
- 可编写可执行 POC
- 目标 CVSS >= 7.0

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                  主 Agent                         │
│  协调工作流程 · 管理子 Agent · 聚合报告           │
└──────────────────────┬──────────────────────────┘
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  子 Agent 1 │ │  子 Agent 2 │ │  子 Agent N │
│  模块 A     │ │  模块 B     │ │  模块 N     │
└─────────────┘ └─────────────┘ └─────────────┘
```

主 Agent 负责项目初始化、技术侦察、模块划分和子 Agent 调度；子 Agent 并行审计各代码模块，输出 CVE 级别漏洞报告。

## 工作流程

```
项目收集 → 技术侦察 → 模块划分 → 子 Agent 并行审计 → POC 编写 → (可选) Docker 部署验证 → CVE 提交报告
```

1. **项目收集** — 用户提供 git URL，克隆到标准目录结构
2. **技术侦察** — 识别语言、框架、攻击面、高风险区域
3. **模块划分** — 将代码库按逻辑边界拆分为独立审计模块
4. **子 Agent 审计** — 并行调度子 Agent 深度追踪 Source -> Sink 调用链
5. **POC 编写** — 为 CVE 级别漏洞编写武器化 Python 脚本
6. **环境验证**（可选）— Docker 沙箱中部署并验证 POC
7. **汇总报告** — 聚合所有发现，生成 CVE 提交包

## 项目结构

```
code-audit-system/
├── SKILL.md                          # 主 Skill 文件，完整工作流程
├── README.md
├── evals/
│   ├── evals.json                    # Skill 测试用例
│   └── trigger-evals.json            # 触发评估集
└── references/
    ├── project-structure.md          # 标准目录结构规范
    ├── module-detection.md           # 按项目类型的模块划分模板
    ├── java-guide.md                 # Java 漏洞审计指南
    ├── php-guide.md                  # PHP 漏洞审计指南
    ├── state/
    │   └── audit-state-schema.md     # 状态文件格式规范
    └── templates/
        ├── work-background-template.md
        ├── subagent/
        │   ├── subagent-skill-template.md
        │   ├── subagent-background-template.md
        │   ├── module-info-template.md
        │   └── execution-log-template.md
        └── reports/
            ├── vulnerability-report-template.md
            ├── summary-report-template.md
            ├── verification-report-template.md
            └── poc-template.py
```

### 审计项目标准结构

```
code-audit-projects/<project>/
├── source/               # 源代码（git clone 目标）
├── state/                # 审计状态追踪（支持断点续传）
├── workspace/            # 子 Agent 工作区
│   ├── 00-work-background.md
│   ├── 01-module-map.md
│   └── agent-<module>/
├── pocs/                 # POC 脚本
├── reports/              # CVE 报告
├── docker/               # Docker 环境（可选）
└── metadata.json         # 项目元数据
```

## 支持的项目类型

| 类型 | 指示文件 | 示例 |
|------|----------|------|
| Web 应用（前后端分离） | package.json + requirements.txt | React + Django |
| 单体 MVC 应用 | pom.xml / manage.py / Gemfile | Spring Boot, Django, Rails |
| 系统服务 / CLI | Cargo.toml / go.mod / CMakeLists.txt | Go daemon, Rust CLI |
| GUI 桌面应用 | Electron / Qt / .NET | Electron app |
| 移动应用 | build.gradle / .xcodeproj | Android, iOS |
| 微服务架构 | docker-compose.yml / k8s/ | Kubernetes 集群 |
| 库 / SDK | setup.py / pyproject.toml | Python package |

## 漏洞审计指南

内置 Java 和 PHP 两种语言的漏洞审计指南，涵盖：

| 漏洞类型 | CVSS | 目标 Sink |
|----------|------|-----------|
| SQL 注入 | 9.0+ | Statement.executeQuery(), mysqli_query() |
| 命令注入 / RCE | 9.8 | Runtime.exec(), system() |
| XXE | 8.0+ | DocumentBuilder.parse(), simplexml_load_string() |
| 反序列化 | 9.0+ | ObjectInputStream.readObject(), unserialize() |
| 路径穿越 | 7.5 | FileInputStream(), file_get_contents() |
| SSRF | 8.6-9.0 | HttpClient.send(), curl_exec() |
| SSTI | 9.0+ | Template.process(), Velocity.evaluate() |
| 认证绕过 | 4.0-9.8 | JWT none 算法, 弱密钥 |
| 文件上传 | 8.0-9.8 | move_uploaded_file() |
| JNDI 注入 | 9.0+ | InitialContext.lookup() |

每类漏洞均包含危险 API 列表、漏洞代码示例、安全写法对比和审计检查清单。

## 输出物

- **CVE 提交报告** — 包含 CVSS 评分、受影响版本、调用链、POC 引用
- **武器化 POC** — 自包含 Python 脚本，可配置目标，默认展示完整影响
- **独立漏洞报告** — 精确到文件行号的技术分析
- **POC 验证报告**（可选）— Docker 环境中的实际验证结果

## 关键规则

1. `git clone` 必须克隆到 `source/` 子目录
2. 状态文件必须在 `state/` 目录（支持断点续传）
3. 主 Agent 必须预先为每个子 Agent 创建背景文档
4. 每个子 Agent 必须有独立工作区
5. 仅报告 CVSS >= 7.0 的可利用漏洞
6. 1 个可利用漏洞 > 10 个理论漏洞

## 适用场景

- 提供 git 仓库 URL 进行 CVE 发现
- 需要武器化 POC 代码的安全研究
- CVE 就绪报告生成（提交至 MITRE / GitHub 安全公告 / 供应商 PSIRT）
- 开源项目安全审计
