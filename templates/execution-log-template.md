# SubAgent 执行日志格式规范

## 📋 日志文件位置

```
workspace/agent-<module-name>/execution.log
```

---

## 📝 日志格式

### 标准日志条目

```
[时间戳] [阶段] [动作] 详细信息
```

**示例**:
```
[2026-04-02 12:00:01] [Phase 1] [START] 开始代码地图绘制
[2026-04-02 12:00:05] [Phase 1] [FILE] 扫描文件：DocumentServiceImpl.java (1200 行)
[2026-04-02 12:00:10] [Phase 1] [SOURCE] 发现入口点：DocumentRestService.getDocumentsByQuery() @79
[2026-04-02 12:00:15] [Phase 1] [SINK] 发现危险点：QueryImpl.createQuery() @991
[2026-04-02 12:00:20] [Phase 1] [END] 代码地图绘制完成，发现 3 个 Source, 5 个 Sink
```

---

## 🎯 日志内容要求

### Phase 1: 代码地图绘制

```
[时间戳] [Phase 1] [START] 开始代码地图绘制
[时间戳] [Phase 1] [FILE] 扫描文件：<文件名> (<行数>行)
[时间戳] [Phase 1] [SOURCE] 发现入口点：<方法名> @<行号>
[时间戳] [Phase 1] [SINK] 发现危险点：<方法名> @<行号>
[时间戳] [Phase 1] [END] 代码地图绘制完成，发现 X 个 Source, Y 个 Sink
```

### Phase 2: 数据流追踪

```
[时间戳] [Phase 2] [START] 开始数据流追踪
[时间戳] [Phase 2] [CHAIN] 追踪路径：<Source> → <Process> → <Sink>
[时间戳] [Phase 2] [VALIDATE] 检查验证：<函数名> - 验证类型 - 有效性 (✅/❌)
[时间戳] [Phase 2] [BYPASS] 绕过分析：<控制措施> - 绕过方法 - 可利用性 (高/中/低)
[时间戳] [Phase 2] [END] 完成 X 条调用链追踪
```

### Phase 3: 安全控制分析

```
[时间戳] [Phase 3] [START] 开始安全控制分析
[时间戳] [Phase 3] [CONTROL] 全局策略：<策略名称> - 作用 - 有效性
[时间戳] [Phase 3] [CONTROL] 局部验证：<函数名> - 验证类型 - 有效性
[时间戳] [Phase 3] [BYPASS] 绕过可能：<控制措施> → <绕过方法> (可行性：高/中/低)
[时间戳] [Phase 3] [END] 安全控制分析完成
```

### Phase 4: CVE 发现与报告

```
[时间戳] [Phase 4] [START] 开始 CVE 发现
[时间戳] [Phase 4] [VULN] 发现漏洞：<漏洞类型> - <位置> - CVSS 评分
[时间戳] [Phase 4] [CHECK] CVE 判定：可利用 (✅/❌) POC 可行 (✅/❌) CVSS≥7.0 (✅/❌)
[时间戳] [Phase 4] [FILTER] 过滤漏洞：<漏洞类型> - 原因 (理论/被阻断/CVSS 低)
[时间戳] [Phase 4] [REPORT] 生成报告：report.md
[时间戳] [Phase 4] [END] CVE 发现完成，发现 X 个高危漏洞
```

---

## 📊 完整日志示例

```log
================================================================================
SubAgent 执行日志
================================================================================
任务：ECMS CVE Hunter - Core Services 模块
模块：core/services/
开始时间：2026-04-02 12:00:00
================================================================================

[2026-04-02 12:00:01] [Phase 1] [START] 开始代码地图绘制

[2026-04-02 12:00:05] [Phase 1] [FILE] 扫描文件：DocumentServiceImpl.java (1200 行)
[2026-04-02 12:00:06] [Phase 1] [FILE] 扫描文件：DocumentRestService.java (500 行)
[2026-04-02 12:00:07] [Phase 1] [FILE] 扫描文件：AttachmentsRestService.java (300 行)
[2026-04-02 12:00:08] [Phase 1] [FILE] 扫描文件：LinkManagerImpl.java (450 行)

[2026-04-02 12:00:10] [Phase 1] [SOURCE] 发现入口点：DocumentRestService.getDocumentsByQuery() @79
  - 参数：@QueryParam("query") String query
  - 类型：HTTP 查询参数
  - 可信度：❌ 不可信

[2026-04-02 12:00:12] [Phase 1] [SOURCE] 发现入口点：AttachmentsRestService.getAttachments() @120
  - 参数：@QueryParam("nodeId") String nodeId
  - 类型：HTTP 查询参数
  - 可信度：❌ 不可信

[2026-04-02 12:00:15] [Phase 1] [SINK] 发现危险点：QueryImpl.createQuery() @991
  - 方法：queryManager.createQuery(query, Query.SQL)
  - 危险类型：JCR SQL 查询
  - 风险等级：🔴 高

[2026-04-02 12:00:17] [Phase 1] [SINK] 发现危险点：session.getItem(path) @220
  - 方法：session.getItem(userPath)
  - 危险类型：JCR 路径访问
  - 风险等级：🔴 高

[2026-04-02 12:00:20] [Phase 1] [END] 代码地图绘制完成，发现 5 个 Source, 8 个 Sink

--------------------------------------------------------------------------------

[2026-04-02 12:00:21] [Phase 2] [START] 开始数据流追踪

[2026-04-02 12:00:25] [Phase 2] [CHAIN] 追踪路径：DocumentRestService → DocumentServiceImpl → QueryImpl
  Source: DocumentRestService.getDocumentsByQuery(query) @79
    ↓
  Process: DocumentServiceImpl.getDocumentsByQuery(query) @984
    ↓ 验证：无 (仅检查 null)
  Process: queryManager.createQuery(query, Query.SQL) @991
    ↓ 危险：直接拼接用户输入
  Sink: QueryImpl.execute() @1015
    ↓
  Impact: JCR SQL 注入 → 绕过访问控制

[2026-04-02 12:00:30] [Phase 2] [VALIDATE] 检查验证：getDocumentsByQuery - null 检查 - 有效性 ❌
  - 仅检查 query != null
  - 未验证 query 内容
  - 可注入恶意 SQL

[2026-04-02 12:00:35] [Phase 2] [BYPASS] 绕过分析：ACL 权限检查 - 使用系统会话绕过 - 可利用性 高
  - 现有控制：WCMCoreUtils.getUserSessionProvider()
  - 绕过方法：getSystemSessionProvider()
  - 影响：完全绕过 ACL

[2026-04-02 12:00:40] [Phase 2] [END] 完成 5 条调用链追踪

--------------------------------------------------------------------------------

[2026-04-02 12:00:41] [Phase 3] [START] 开始安全控制分析

[2026-04-02 12:00:45] [Phase 3] [CONTROL] 全局策略：@RolesAllowed("users") - 基本认证 - 有效性 ⚠️ 部分
  - 要求用户认证
  - 无输入验证
  - 认证后完全开放

[2026-04-02 12:00:50] [Phase 3] [CONTROL] 局部验证：null 检查 - 有效性 ❌ 不足
  - 位置：DocumentServiceImpl.getDocumentsByQuery() @986
  - 仅检查：if (query == null) return error
  - 缺失：内容验证、长度限制、白名单

[2026-04-02 12:00:55] [Phase 3] [BYPASS] 绕过可能：@RolesAllowed → 发送合法认证请求 (可行性：高)
  - 任意认证用户可访问
  - 无权限级别检查

[2026-04-02 12:01:00] [Phase 3] [END] 安全控制分析完成

--------------------------------------------------------------------------------

[2026-04-02 12:01:01] [Phase 4] [START] 开始 CVE 发现

[2026-04-02 12:01:10] [Phase 4] [VULN] 发现漏洞：JCR SQL 注入 - DocumentServiceImpl.java:991 - CVSS 9.8
  - 位置：core/services/src/main/java/.../DocumentServiceImpl.java:991
  - 类型：JCR SQL Injection
  - 调用链：REST API → Service → QueryManager → Execute
  - 影响：绕过访问控制、窃取所有文档

[2026-04-02 12:01:15] [Phase 4] [CHECK] CVE 判定：
  - 可利用：✅ 是 (有明确 Source 和 Sink)
  - POC 可行：✅ 是 (可构造恶意查询)
  - CVSS≥7.0: ✅ 是 (9.8 Critical)
  - 判定：✅ CVE 就绪

[2026-04-02 12:01:20] [Phase 4] [VULN] 发现漏洞：认证绕过 - AttachmentsRestService.java:220 - CVSS 7.5
  - 位置：core/services/src/main/java/.../AttachmentsRestService.java:220
  - 类型：Authentication Bypass
  - 问题：缺少@RolesAllowed 注解
  - 影响：未授权访问附件元数据

[2026-04-02 12:01:25] [Phase 4] [CHECK] CVE 判定：
  - 可利用：✅ 是
  - POC 可行：✅ 是
  - CVSS≥7.0: ✅ 是 (7.5 High)
  - 判定：✅ CVE 就绪

[2026-04-02 12:01:30] [Phase 4] [FILTER] 过滤漏洞：信息泄露 - LinkManagerImpl.java:450 - 原因：CVSS 低 (5.3)
  - 问题：错误日志泄露路径信息
  - 影响：有限信息泄露
  - 判定：❌ 不报告 (CVSS < 7.0)

[2026-04-02 12:01:35] [Phase 4] [REPORT] 生成报告：report.md
  - 文件：/workspace/agent-services/report.md
  - 内容：2 个 CVE 就绪漏洞
  - 状态：完成

[2026-04-02 12:01:40] [Phase 4] [END] CVE 发现完成，发现 2 个高危漏洞

================================================================================
执行总结
================================================================================
开始时间：2026-04-02 12:00:00
结束时间：2026-04-02 12:01:40
总耗时：1 分 40 秒

扫描文件：4 个
发现 Source: 5 个
发现 Sink: 8 个
追踪调用链：5 条
发现漏洞：3 个
CVE 就绪：2 个 (CVSS ≥ 7.0)
过滤漏洞：1 个 (CVSS < 7.0)

输出文件:
- report.md (CVE 报告)
- execution.log (本日志)
================================================================================
```

---

## 🔧 日志记录最佳实践

### 1. 及时记录

每个关键动作后立即记录，不要等到最后：
```java
// ✅ 好：立即记录
log("[Phase 1] [FILE] 扫描文件：" + fileName);
scanFile(fileName);

// ❌ 差：延迟记录
scanFile(fileName);
scanFile(fileName2);
scanFile(fileName3);
log("扫描完成");  // 丢失了细节
```

### 2. 结构化格式

使用统一的 `[阶段] [动作] 详细信息` 格式：
```
✅ [Phase 2] [CHAIN] 追踪路径：A → B → C
❌ Phase 2: 追踪路径 A 到 B 到 C (格式不统一)
```

### 3. 包含关键信息

每个日志条目应包含：
- **时间戳**: 便于计算耗时
- **阶段**: 识别审计进度
- **动作类型**: 快速筛选日志
- **详细信息**: 文件名、行号、方法名等

### 4. 使用 emoji 标记重要性

```
🔴 高危漏洞
🟡 中等漏洞
🟢 低危/建议
✅ 验证通过
❌ 验证失败/过滤
⚠️ 警告/注意
```

---

## 📊 日志分析用途

### 1. 审计过程追溯

```bash
# 查看某个阶段的所有动作
grep "\[Phase 2\]" workspace/agent-services/execution.log
```

### 2. 调试子 Agent 问题

```bash
# 查看失败/过滤的漏洞
grep "\[FILTER\]" workspace/agent-*/execution.log
```

### 3. 优化审计策略

```bash
# 统计各阶段耗时
grep "\[START\]\|\[END\]" workspace/agent-*/execution.log
```

### 4. 知识积累

```bash
# 汇总所有发现的漏洞类型
grep "\[VULN\] 发现漏洞" workspace/agent-*/execution.log
```

---

## 📁 日志文件管理

### 文件命名

```
workspace/agent-<module-name>/execution.log
```

### 日志轮转 (可选)

如果日志过大 (>10MB)，可考虑轮转：
```
execution.log       # 当前日志
execution.log.1     # 上一轮日志
execution.log.2     # 上上轮日志
```

### 日志压缩 (审计完成后)

```bash
# 压缩旧日志
gzip workspace/agent-*/execution.log
# 结果：execution.log.gz
```

---

**所有子 Agent 必须将执行日志保存到 `workspace/agent-<module>/execution.log`** 🔒
