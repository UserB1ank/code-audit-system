# 漏洞审计报告模板

```markdown
# 漏洞审计报告

## 项目信息

| 项目 | 值 |
|------|-----|
| 项目名称 | [项目名] |
| 项目地址 | [GitHub/Gitee URL] |
| 审计时间 | YYYY-MM-DD HH:MM |
| 审计工具 | Qwen + code-audit skill |
| 审计范围 | 全量代码审计 |

---

## 漏洞汇总

| 编号 | 类型 | 严重程度 | 认证 | 位置 | 状态 |
|------|------|----------|------|------|------|
| 001 | SQL Injection | 🔴 Critical | 否 | `src/user.php` L30-35 | 待验证 |
| 002 | RCE | 🔴 Critical | 是 | `admin/upload.php` L45-60 | 待验证 |
| 003 | XSS | 🟡 Medium | 否 | `public/index.php` L120 | 待验证 |

**统计:**
- 🔴 Critical: X 个
- 🟠 High: X 个
- 🟡 Medium: X 个
- 🟢 Low: X 个
- **总计**: X 个

---

## 漏洞详情

### 001 - SQL 注入

#### 基本信息

- **漏洞类型**: SQL Injection
- **严重程度**: 🔴 Critical
- **CVSS 评分**: 9.8
- **认证要求**: 不需要
- **影响范围**: 所有用户

#### 漏洞位置

```
文件：src/user.php
行号：30-35
函数：login()
```

#### 代码片段

```php
// src/user.php line 30-35
public function login($username, $password) {
    $sql = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";
    $result = $this->db->query($sql);
    // ...
}
```

#### 触发过程

1. 用户输入用户名和密码提交到 `login()` 函数
2. 函数直接接收用户输入，**未进行任何过滤或转义**
3. 用户输入直接拼接到 SQL 语句中
4. 攻击者可以构造恶意输入如 `' OR '1'='1` 绕过认证
5. 最终导致 SQL 注入漏洞，可获取数据库所有数据

#### 验证步骤

```bash
# 使用 POC 脚本验证
python pocs/001_sql_injection.py

# 或手动验证
curl -X POST "http://target/login" \
  -d "username=admin' OR '1'='1&password=anything"
```

#### 修复建议

1. **使用参数化查询** (推荐)

```php
// 修复后
public function login($username, $password) {
    $stmt = $this->db->prepare("SELECT * FROM users WHERE username = ? AND password = ?");
    $stmt->execute([$username, $password]);
    $result = $stmt->fetch();
    // ...
}
```

2. **输入验证**: 对用户名和密码进行严格的格式验证
3. **密码加密**: 使用 bcrypt 或 Argon2 加密密码

#### 参考链接

- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)

---

### 002 - 远程代码执行 (RCE)

#### 基本信息

- **漏洞类型**: Remote Code Execution
- **严重程度**: 🔴 Critical
- **CVSS 评分**: 9.1
- **认证要求**: 需要 (管理员)
- **影响范围**: 管理员用户

#### 漏洞位置

```
文件：admin/upload.php
行号：45-60
函数：uploadFile()
```

#### 触发过程

1. 管理员访问文件上传功能
2. `uploadFile()` 函数仅检查文件扩展名，**未检查文件内容**
3. 攻击者可以上传伪造扩展名的 PHP 文件
4. 文件被保存到 Web 可访问目录
5. 访问上传的文件即可执行任意代码

#### 修复建议

1. **白名单验证**: 仅允许特定扩展名
2. **内容检查**: 使用 `finfo_file()` 检查真实 MIME 类型
3. **重命名文件**: 使用随机文件名
4. **隔离存储**: 将上传文件存放在 Web 根目录外

#### 参考链接

- [OWASP File Upload](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [CWE-434: Unrestricted Upload](https://cwe.mitre.org/data/definitions/434.html)

---

## 附录

### 审计工具版本

- Qwen: qwen3-coder-plus
- code-audit skill: v3.0.0
- 审计日期：YYYY-MM-DD

### 免责声明

本报告仅供安全研究和修复参考，不得用于非法用途。
```

---

# 漏洞验证报告模板

```markdown
# 漏洞验证报告

## 项目信息

| 项目 | 值 |
|------|-----|
| 项目名称 | [项目名] |
| 验证时间 | YYYY-MM-DD HH:MM |
| 验证环境 | Docker 沙箱 |

---

## 验证结果汇总

| 编号 | 类型 | 严重程度 | POC 路径 | 验证状态 | 结果 |
|------|------|----------|---------|----------|------|
| 001 | SQL Injection | Critical | `pocs/001_sql_injection.py` | ✅ 成功 | 获取数据库版本 |
| 002 | RCE | Critical | `pocs/002_rce.py` | ✅ 成功 | 执行 whoami 成功 |
| 003 | XSS | Medium | `pocs/003_xss.py` | ❌ 失败 | WAF 拦截 |

**统计:**
- ✅ 成功：X 个
- ❌ 失败：X 个
- **成功率**: XX%

---

## 验证详情

### 001 - SQL 注入验证

#### POC 信息

- **POC 路径**: `pocs/001_sql_injection.py`
- **执行时间**: 2026-03-09 10:30:45
- **执行环境**: Docker (Ubuntu 22.04, Python 3.10)

#### 执行命令

```bash
python pocs/001_sql_injection.py --target http://localhost:8080
```

#### 执行输出

```
[+] 目标：http://localhost:8080
[+] 检测 SQL 注入...
[+] 发现注入点：/login (POST)
[+] 测试 payload: ' OR '1'='1
[+] 成功绕过认证！
[+] 获取数据库版本：MySQL 5.7.32
[+] 获取当前用户：root@localhost
[+] 验证成功 ✅
```

#### 验证结论

✅ **漏洞确认存在**

- 成功绕过登录认证
- 成功获取数据库版本信息
- 可进一步获取敏感数据

---

### 002 - RCE 验证

#### POC 信息

- **POC 路径**: `pocs/002_rce.py`
- **执行时间**: 2026-03-09 10:32:15

#### 执行命令

```bash
python pocs/002_rce.py --target http://localhost:8080 --cmd "whoami"
```

#### 执行输出

```
[+] 目标：http://localhost:8080
[+] 上传恶意文件...
[+] 文件路径：/uploads/shell_abc123.php
[+] 执行命令：whoami
[+] 输出：www-data
[+] 验证成功 ✅
```

#### 验证结论

✅ **漏洞确认存在**

- 成功上传 WebShell
- 成功执行系统命令
- 权限：www-data

---

## 验证环境

### Docker 配置

```yaml
version: '3.8'
services:
  target:
    build: .
    ports:
      - "8080:80"
    networks:
      - audit_net
  
  attacker:
    image: python:3.10-slim
    volumes:
      - ./pocs:/pocs
    networks:
      - audit_net
```

### 环境信息

- Docker 版本：24.0.0
- Python 版本：3.10.12
- 网络模式：隔离网络

---

## 安全提示

⚠️ 所有验证均在 Docker 沙箱中进行，请勿在生产环境执行 POC。
```
