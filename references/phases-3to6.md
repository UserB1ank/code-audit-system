# Phase 3-6: 环境部署、POC 编写、验证与报告

> 本文档包含步骤 3-6 的详细操作说明：环境部署、武器化 POC 编写、漏洞验证和 CVE 提交报告。从 SKILL.md 中提取。

---

## 步骤 3: 环境部署 (可选 - 询问用户)

继续前，询问用户:
> "是否要在 Docker 环境中部署目标应用程序以进行漏洞验证? 这样可以在隔离环境中测试 POC。"

如果用户确认:

1. **检查现有 Docker 配置** - 在源代码仓库中查找 Dockerfile、docker-compose.yml
2. **创建 Docker 环境** (如果不存在):
   - 分析应用依赖 (包文件、构建工具、运行时需求)
   - 编写适当的 `Dockerfile`
   - 创建包含服务依赖的 `docker-compose.yml` (MySQL、PostgreSQL、Neo4j 等)

3. **编写 Docker 文件**:
   - 对于典型 Web 应用，创建多阶段 Dockerfile (构建和运行阶段)
   - 使用 `docker-compose.yml` 定义应用服务加数据库/依赖服务
   - 将 Docker 配置存储在项目的 `docker/` 目录

4. **Dockerfile 模板示例**:
   ```dockerfile
   # Build stage
   FROM maven:3.9-eclipse-temurin-21 AS builder
   WORKDIR /app
   COPY pom.xml .
   RUN mvn dependency:go-offline
   COPY src ./src
   RUN mvn package -DskipTests

   # Runtime stage
   FROM eclipse-temurin:21-jre
   WORKDIR /app
   COPY --from=builder /app/target/*.jar app.jar
   EXPOSE 8080
   ENTRYPOINT ["java", "-jar", "app.jar"]
   ```

5. **docker-compose.yml 模板示例**:
   ```yaml
   version: '3.8'
   services:
     app:
       build: .
       ports:
         - "8080:8080"
       environment:
         - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/appdb
         - SPRING_DATASOURCE_USERNAME=appuser
         - SPRING_DATASOURCE_PASSWORD=apppass
       depends_on:
         db:
           condition: service_healthy
     db:
       image: postgres:16
       environment:
         POSTGRES_DB: appdb
         POSTGRES_USER: appuser
         POSTGRES_PASSWORD: apppass
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U appuser"]
         interval: 5s
         timeout: 5s
         retries: 5
   ```

6. **启动环境**:
   ```bash
   docker-compose up -d
   ```

**注意**: 如果目标应用有特殊需求 (如特定中间件、缓存层或复杂网络)，需相应调整 Docker 配置。

---

## 步骤 4: 武器化 POC 编写

调度子代理为 CVE 提交编写 **武器化** 的概念验证利用:

1. **阅读步骤 2 的漏洞报告** (仅 CVE 级别)
2. **创建 POC 目录**: `<project-root>/pocs/`
3. **为每个 CVE 级别漏洞** 创建 Python 脚本:
   - `poc-001-rce-auth-bypass.py`
   - `poc-002-sqli-admin-takeover.py`
   - `poc-003-path-traversal-rce.py`

**POC 要求 (CVE 提交标准)**:
- 自包含的 Python 脚本 (除 requests 外无外部依赖)
- 清晰的使用说明和示例命令
- 可配置的目标 URL/主机/端口
- **默认武器化** (演示完整影响)
- 安全执行 (无永久损害，但证明利用)
- **利用前/后证据** (如 `whoami` 输出、创建的文件、提取的数据)
- 注释中的 CVSS 评分依据

**POC 结构**:
```python
#!/usr/bin/env python3
"""
CVE-XXXX-XXXXX: [漏洞名称]
目标: [产品名] [受影响版本]
发现者: [你的名字]
CVSS: [评分] [向量]

用法: python3 poc.py -t http://target:port

概念验证:
- 利用前: [正常状态]
- 利用中: [攻击动作]
- 利用后: [被攻陷状态]
"""
```

**阅读**: `templates/poc-template.py` 获取 POC 结构。

**CVE 提交包**:
为每个 CVE 级别漏洞准备:
1. POC 脚本 (武器化)
2. 视频演示 (可选但推荐)
3. 技术报告 (影响、受影响版本、修复建议)
4. CVSS v3.1 评分

---

## 步骤 5: 漏洞验证 (可选 - 询问用户)

询问用户:
> "是否要在部署的环境中验证 POC? 每验证一个漏洞将生成一份独立验证报告，最终汇总为 CVE 提交总报告。"

如果用户确认:

1. **部署目标** (未在步骤 3 中完成)
2. **逐个漏洞进行验证** — 对每个 CVE 级别漏洞:

   a. **运行 POC** 于部署的 Docker/本地环境
   b. **记录结果**: 成功/失败、输出/证据、利用耗时

   c. **立即编写单漏洞验证报告** (小报告):
      - 路径: `reports/vulnerability-<id>-verification.md`
      - 格式: 参考 `templates/per-vulnerability-verification-report-template.md`
      - 内容必须包含: 漏洞标题、严重性评估、受影响组件、影响、技术复现步骤、漏洞根因、展示的影响、环境信息、补救建议
      - 若验证失败，报告中需包含失败分析和可能原因

   d. **更新审计状态**:
      ```json
      {
        "vulnerabilities": [{
          "id": "VULN-XXX",
          "verification_report": "reports/vulnerability-XXX-verification.md",
          "verification_status": "verified|failed|skipped",
          "verification_date": "2026-04-22T10:00:00Z"
        }]
      }
      ```

3. **(可选) 生成验证汇总报告** `reports/verification-report.md` — 汇总索引，详细内容指向各单漏洞验证报告

**关键规则**:
- **每验证一个漏洞必须立即写一份小报告**，禁止等全部验证完成后再统一写
- 小报告是 CVE 提交总报告的核心素材，必须详实、可复现
- 使用中文撰写，保留技术术语英文

---

## 步骤 6: CVE 提交报告

主代理将所有发现汇总为 **CVE 就绪提交包**:

1. **收集所有报告**: 子代理的独立漏洞报告 (仅 CVE 级别)、武器化 POC 脚本、POC 验证结果

2. **生成 CVE 提交总报告** `reports/cve-submission-report.md`:

总报告汇总所有已验证的单漏洞报告，格式如下：

```markdown
# CVE Submission Report — [产品名]

## Project Overview
- **Product**: [产品名称]
- **Repository**: <git-url>
- **Vendor**: [厂商名称]
- **Audit Date**: <date>
- **Commit**: <commit-hash>
- **Auditor**: [你的名称/代号]

## Executive Summary
- **CVE-Worthy Vulnerabilities**: <count> (CVSS ≥ 7.0)
- **Critical (CVSS 9.0-10.0)**: <count>
- **High (CVSS 7.0-8.9)**: <count>
- **Total with Complete Exploit Chains**: <count>
- **POC-Ready**: <count>

## CVE Candidates

| ID | Type | CVSS | CWE | Location | POC | Status |
|----|------|------|-----|----------|-----|--------|
| CVE-XXXX-XXXXX | [漏洞类型] | [评分] | CWE-XXX | `file.py:行号` | Yes | Ready |

---

## Detailed CVE Reports

### CVE-XXXX-XXXXX: [漏洞名称]

**Severity**: [严重级别] (CVSS [评分])
**Vector**: [CVSS向量字符串]
**CWE**: CWE-XXX ([CWE名称])
**Affected Versions**: [版本范围]

**Location**: `[文件路径:行号范围]`

**Root Cause**: [根本缺陷的详细说明，具体指出缺少什么验证]

**Call Chain**:
```
[1] Source: [函数]() 位于 [文件:行号]
    ↓ [数据流描述]
[2] Process: [函数]() 位于 [文件:行号]
    ↓ [数据流描述]
[3] Sink: [函数]() 位于 [文件:行号]
    ↓ [最终结果]
```

**Impact**: [攻击者可达成的具体目标]

**POC**:
```bash
[可执行的 POC 命令或脚本路径]
```

**Verification**: ✅ 成功 (详见 `reports/vulnerability-XXX-verification.md`)

---

## Maximum Impact Exploit Chain

1. [步骤1]: [利用某个漏洞进行侦察/初始访问]
2. [步骤2]: [利用某个漏洞提升权限/窃取凭证]
3. [步骤3]: [利用某个漏洞实现 RCE/持久化]
4. [步骤4]: [利用某个漏洞横向移动/数据窃取]

**Total time to full compromise**: <时间> with default configuration.

## Submission Targets

| CNA | URL | Priority |
|-----|-----|----------|
| MITRE | https://cveform.mitre.org/ | Primary |
| GitHub Security Advisories | https://github.com/[vendor]/[repo]/security/advisories | High |
| Vendor PSIRT | [vendor-specific] | Medium |

## Submission Checklist

For each CVE candidate:
- [ ] Technical writeup complete (引用单漏洞验证报告)
- [ ] POC weaponized and tested
- [ ] CVSS v3.1 scoring calculated
- [ ] Affected versions confirmed
- [ ] Vendor notification (如协调披露)
- [ ] Video demonstration (optional)

## Appendix
- Individual verification reports: `reports/vulnerability-*-verification.md`
- Weaponized POCs: `pocs/`
- Background: `workspace/00-work-background.md`
- Module map: `workspace/01-module-map.md`
```

**总报告生成规则**:
- 总报告中的每个漏洞详细描述必须引用对应的单漏洞验证报告
- 总报告侧重于**汇总和提交就绪状态**，技术细节以单漏洞验证报告为准
- 必须包含 **Maximum Impact Exploit Chain** 章节，展示漏洞组合利用的最大影响
- 使用中文撰写，保留技术术语英文

3. **CVE 提交渠道**:
   - **MITRE**: 主要 CVE CNA
   - **GitHub Security Advisories**: 开源项目
   - **厂商 PSIRT**: 协调披露
   - **NVD**: CVE 分配后

4. **存储结构化数据**: 漏洞元数据、POC 元数据、验证结果
