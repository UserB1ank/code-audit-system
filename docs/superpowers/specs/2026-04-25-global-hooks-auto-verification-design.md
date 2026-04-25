# 全局 Hook 规则发现 + 自动二次验证 设计文档

**日期**: 2026-04-25
**状态**: 已确认

---

## 问题背景

当前子代理以 Source→Sink 数据流追踪为核心审计手段，存在两个盲区：

1. **全局安全机制遗漏** — Java Filter、Spring Security 配置、PHP 中间件等全局安全机制横切所有请求，但不出现在具体的 Source→Sink 代码流中。导致：
   - 误报：报告了一个被全局 Filter 阻断的"漏洞"
   - 漏报：未发现某条路径绕过了全局安全机制

2. **一轮审计覆盖不足** — 仅靠一轮审计无法保证所有危险 Sink 都被检查到，需要自动化二次验证补盲。

---

## 设计方案：新增两个独立阶段（方案 A）

### Phase 2.0b: 全局安全机制发现

**插入位置**: Phase 2.1 技术侦察之后、Phase 2.2 模块划分之前
**触发条件**: 始终执行（非可选）

#### 扫描目标

| 类别 | 扫描内容 | 典型文件/位置 |
|------|----------|--------------|
| 全局过滤器 | Servlet Filter、Spring HandlerInterceptor、PHP 中间件、Django Middleware、Express middleware | `web.xml`、`SecurityConfig`、`kernel.php`、`settings.py`、`app.js` |
| 认证/授权配置 | Spring Security 规则、Shiro 配置、路由级 auth guard、`.htaccess` | `SecurityConfig.java`、`shiro.ini`、路由配置文件 |
| 全局输入清理 | 全局 sanitize 函数、HTML 编码器、SQL 转义、CSRF 校验、WAF 规则 | Filter 实现、中间件、基类 Controller |
| 其他全局配置 | CORS 策略、全局异常处理、序列化白名单、文件上传限制 | `@ControllerAdvice`、`CORS config`、`application.yml` |

#### 输出产物

`workspace/02-global-security-map.md`，每个全局机制记录：

```
机制名称: [如 CsrfFilter]
类型: [过滤器/拦截器/中间件/配置]
作用: [CSRF Token 校验]
覆盖范围: [所有 POST/PUT/DELETE 请求]
排除路径: [/api/public/*, /health]
绕过条件: [无 / 仅 AJAX 请求头绕过]
代码位置: [CsrfFilter.java:25-45]
```

#### 下游消费

- 注入每个子代理的 `background.md`，增加"全局安全机制"章节
- 子代理在判断漏洞可利用性时，必须对照此地图验证是否被全局机制阻断
- 二次验证阶段以此地图为基准交叉检查

---

### Phase 2.5: 自动二次验证

**触发条件**: 所有子代理完成 Phase 2.4 报告后，主代理**立即自动启动**，不询问用户

#### 轨道 1：全局危险 Sink 扫描代理

**职责**: 脱离第一轮的 Source→Sink 思维，纯做 Sink 枚举 + 逐点检查

**工作方式**:
1. 根据目标语言读取 `references/<lang>-guide.md` 中的危险函数清单
2. 对整个 `source/` 执行 grep，列出**每一个**危险 Sink 调用点
3. 逐点检查：该调用点是否在第一轮报告中被覆盖？
   - 已覆盖 → 跳过
   - 未覆盖 → 追溯该 Sink 是否有用户可控输入可达（快速 Source→Sink 验证）
4. 输出：`workspace/03-sink-coverage-report.md`

#### 轨道 2：交叉验证代理

**职责**: 对照 `02-global-security-map.md` 审查第一轮报告

**工作方式**:
1. 读取所有子代理的 `report.md`
2. 读取 `02-global-security-map.md`
3. 对每个报告的漏洞：
   - 检查漏洞路径是否被全局机制阻断（剔除误报）
   - 记录置信度：✅ 确认可利用 / ⚠️ 可能被全局机制阻断 / ❌ 已被阻断
4. 对全局安全地图中的每个排除/绕过路径：
   - 检查是否有子代理审计了该路径（发现漏报）
   - 未覆盖的绕过路径 → 标记为高优先级待审计点
5. 输出：`workspace/04-cross-verification-report.md`

#### 合并与行动

| 结果 | 处理 |
|------|------|
| 轨道 1 发现未覆盖的 Sink | 自动调度补充子代理审计该 Sink 的 Source→Sink 路径 |
| 轨道 2 发现误报 | 从报告中剔除，记录原因 |
| 轨道 2 发现漏报 | 标记为高优先级，自动调度补充审计 |
| 轨道 1 + 轨道 2 均无新发现 | 流程继续到步骤 3（环境部署） |

---

## 文件变更清单

### 新增文件

| 文件 | 用途 |
|------|------|
| `references/global-security-discovery-guide.md` | 全局安全机制发现方法论——按语言/框架列出要扫描的配置文件、注解、类模式 |
| `templates/global-security-map-template.md` | `02-global-security-map.md` 的输出模板 |
| `templates/sink-coverage-report-template.md` | 轨道 1（Sink 覆盖报告）模板 |
| `templates/cross-verification-report-template.md` | 轨道 2（交叉验证报告）模板 |
| `templates/verification-subagent-skill-template.md` | 二次验证子代理的技能模板 |

### 修改文件

| 文件 | 变更内容 |
|------|----------|
| `SKILL.md` | 工作流概览增加 Phase 2.0b 和 Phase 2.5；步骤 2 中插入对应操作说明；状态机增加 `global_discovery` 和 `round2_verifying` 状态 |
| `templates/subagent-background-template.md` | 增加"全局安全机制"章节，由主代理填充 |
| `templates/subagent-skill-template.md` | 增加"全局 Hook 对照检查"强制步骤 |
| `references/php-guide.md` | 增加"全局安全机制识别"章节 |
| `references/java-guide.md` | 增加"全局安全机制识别"章节 |
| `state/audit-state-schema.md` | 增加 `global_security_map` 和 `round2_verification` 状态字段 |

---

## 状态机变更

```
原: init → cloning → auditing → poc_developing → verifying → reporting → completed
新: init → cloning → global_discovery → auditing → round2_verifying → poc_developing → verifying → reporting → completed
```

新增状态：
- `global_discovery` — 全局安全机制发现中
- `round2_verifying` — 二次验证中（含补充审计）
