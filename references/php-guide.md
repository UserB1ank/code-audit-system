# PHP 漏洞指南

PHP 应用程序中常见的漏洞类型，包含对应的危险函数和实际案例。

## 如何使用

审计 PHP 代码时查阅本指南。将发现的漏洞与这些模式进行匹配，追踪 Source → Sink 链。

---

## 1. SQL 注入

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是

### 危险函数/模式

| 函数 | 模式 | 风险 |
|------|------|------|
| `mysqli_query()` | SQL 字符串拼接 | 🔴 严重 |
| `mysqli::query()` | `$conn->query("SELECT * FROM users WHERE id=$id")` | 🔴 严重 |
| `PDO::query()` | `PDO::query("SELECT * FROM users WHERE name='$name'")` | 🔴 严重 |
| `mysql_query()` | 传统字符串拼接 | 🔴 严重 |
| `SELECT ... WHERE id=` | 直接插入无预处理语句 | 🔴 严重 |

### 漏洞代码示例

```php
// 漏洞：直接拼接
$id = $_GET['id'];
$result = mysqli_query($conn, "SELECT * FROM users WHERE id=$id");

// 漏洞：PDO 字符串拼接
$name = $_POST['name'];
$stmt = $pdo->query("SELECT * FROM users WHERE name='$name'");

// 安全：预处理语句
$stmt = $pdo->prepare("SELECT * FROM users WHERE id=?");
$stmt->execute([$id]);
```

### 审计检查清单

- [ ] 搜索 `mysqli_query`, `mysql_query`, `PDO::query`, `pg_query`
- [ ] 追踪变量来源 (GET/POST/REQUEST/COOKIE)
- [ ] 确定用户输入是否在无预处理情况下到达 SQL
- [ ] 检查 WAF/过滤器绕过可能性

---

## 2. 命令注入

**严重程度**: 严重 (CVSS 9.8) | **可利用**: 是 (远程代码执行)

### 危险函数

| 函数 | 风险 | 示例 |
|------|------|------|
| `exec()` | 捕获输出 | `exec("ls $dir", $output)` |
| `shell_exec()` | 完整输出 | `shell_exec("cat $filename")` |
| `system()` | 回显输出 | `system("ping $host")` |
| `passthru()` | 原始输出 | `passthru("ls $path")` |
| `proc_open()` | 复杂管道 | `proc_open("cmd", ..., $pipes)` |
| `popen()` | 单向操作 | `popen("rm $file", "w")` |
| `` ` `` (反引号) | shell_exec 快捷方式 | `` $output = `ls $dir` `` |
| `pcntl_exec()` | 进程执行 | `pcntl_exec("/bin/sh", $args)` |

### 漏洞代码示例

```php
// 漏洞：用户输入进入 shell 命令
$file = $_GET['file'];
system("cat $file");

// 漏洞：带管道的命令链
$host = $_POST['host'];
system("ping -c 4 $host && ls /tmp");

// 漏洞：反引号操作符
$dir = $_REQUEST['dir'];
$files = `ls $dir`;

// 安全：escapeshellarg 过滤
system('ls ' . escapeshellarg($dir));
```

### 审计检查清单

- [ ] 搜索 `exec|shell_exec|system|passthru|proc_open|popen`
- [ ] 检查反引号操作符使用
- [ ] 验证 `escapeshellarg()` / `escapeshellcmd()` 使用
- [ ] 追踪用户输入到 shell 命令

---

## 3. 文件包含 / LFI / RFI

**严重程度**: 高 (CVSS 8.0+) | **可利用**: 是 (常通过日志污染或 PHP 伪协议 RCE)

### 危险函数

| 函数 | 风险 | 示例 |
|------|------|------|
| `include` | 执行包含文件 | `include $file` |
| `require` | 失败时致命错误 | `require $module` |
| `include_once` | 仅包含一次 | `include_once $view` |
| `require_once` | 仅请求一次 | `require_once $config` |

### 漏洞代码示例

```php
// 漏洞：直接文件包含
$page = $_GET['page'];
include("pages/$page.php");

// 漏洞：路径穿越
$file = $_GET['file'];
include("/var/www/templates/" . $file);

// LFI 到 RCE：利用 PHP 伪协议
// ?file=php://filter/convert.base64-encode/resource=config.php
// ?file=data://text/plain,<?php system($_GET['cmd']);?>
```

### 审计检查清单

- [ ] 搜索 `include|require|include_once|require_once`
- [ ] 确定用户可控制的路径
- [ ] 检查路径穿越 (`../`, 空字节注入)
- [ ] 测试 PHP 伪协议利用

---

## 4. 跨站脚本 (XSS)

**严重程度**: 中-高 (CVSS 6.1-8.2) | **可利用**: 是

### 危险函数/模式

| 函数/上下文 | 风险 | 示例 |
|------------|------|------|
| `echo` 裸输出 | 🔴 存储型 XSS | `echo $_GET['comment']` |
| `print` | 🔴 反射型 XSS | `print $_POST['name']` |
| `printf` 无 `%s` | 🔴 格式化字符串 | `printf($_GET['msg'])` |
| `heredoc`/`nowdoc` | 🔴 动态 HTML | `<<<HTML\n$user_input\nHTML;` |
| `.=` 拼接 | 🔴 构建 HTML | `$html .= $_GET['content']` |
| `innerHTML` (JS) | 🔴 DOM XSS | `element.innerHTML = userInput` |

### 漏洞代码示例

```php
// 漏洞：反射型 XSS
echo "Welcome " . $_GET['name'];

// 漏洞：数据库输出的存储型 XSS
echo $row['comment'];

// 漏洞：JavaScript 上下文
echo '<script>var user="' . $_GET['name'] . '";</script>';

// 安全：htmlspecialchars
echo htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');
```

### 审计检查清单

- [ ] 搜索带用户输入的 `echo|print|printf`
- [ ] 追踪数据流：DB → echo, GET/POST → echo
- [ ] 检查 JS 文件中的 `innerHTML` 赋值
- [ ] 验证输出编码函数

---

## 5. PHP 对象注入 / 反序列化

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是 (RCE, 文件操作)

### 危险函数

| 函数 | 风险 | 示例 |
|------|------|------|
| `unserialize()` | 🔴 严重 | `unserialize($_COOKIE['data'])` |
| `json_decode()` | 低（无魔术方法） | `json_decode($user_json)` |

### 可利用的魔术方法

```php
class Exploit {
    public $cmd;

    function __wakeup() {
        system($this->cmd);  // 对象反序列化时 RCE
    }
}
```

### 漏洞代码示例

```php
// 漏洞：反序列化用户输入
$data = $_COOKIE['session'];
$obj = unserialize($data);

// 漏洞：Base64 编码的载荷
$data = base64_decode($_GET['payload']);
unserialize($data);

// 安全：使用 JSON 代替 serialize
$obj = json_decode($_GET['data']);
```

### 审计检查清单

- [ ] 搜索 `unserialize()`
- [ ] 追踪对象来源 (COOKIE, GET, POST, DB)
- [ ] 查找 `__wakeup()`, `__destruct()`, `__toString()` 魔术方法
- [ ] 检查代码库中的 POP 链 gadgets

---

## 6. 路径穿越 / 本地文件包含

**严重程度**: 高 (CVSS 7.5-8.0) | **可利用**: 是 (文件读取/泄露)

### 危险函数

| 函数 | 风险 | 示例 |
|------|------|------|
| `file_get_contents()` | 读取文件内容 | `file_get_contents($path)` |
| `fopen()` | 文件句柄 | `fopen($filename, 'r')` |
| `readfile()` | 直接输出 | `readfile($filepath)` |
| `file()` | 行数组 | `file($path)` |
| `include` | 执行+读取 | `include $file` |

### 漏洞代码示例

```php
// 漏洞：路径穿越
$file = $_GET['file'];
readfile("/var/www/uploads/" . $file);

// 漏洞：空字节注入（旧版 PHP）
$file = $_GET['file'] . ".txt";
readfile("/data/" . $file . ".txt");
// 攻击：file=config.txt\x00 → 绕过扩展名

// 漏洞：编码的穿越
$path = $_GET['path'];
readfile("/var/www/" . urldecode($path));
```

### 审计检查清单

- [ ] 搜索 `file_get_contents|fopen|readfile|file|include`
- [ ] 确定用户可控制的路径
- [ ] 检查路径规范化问题
- [ ] 测试 `../` 模式和 URL 编码

---

## 7. 服务器端请求伪造 (SSRF)

**严重程度**: 高 (CVSS 8.6-9.0) | **可利用**: 是 (内网访问)

### 危险函数

| 函数 | 风险 | 示例 |
|------|------|------|
| `file_get_contents()` | 含 `php://` 或 `http://` | `file_get_contents($_GET['url'])` |
| `curl_exec()` | 用户 URL | `curl_exec($ch)` |
| `fsockopen()` | 原始套接字 | `fsockopen($host, $port)` |
| `stream_socket_client()` | 流客户端 | `stream_socket_client("tcp://$host")` |

### 漏洞代码示例

```php
// 漏洞：用户提供的 URL
$url = $_GET['url'];
echo file_get_contents($url);

// 漏洞：Curl SSRF
$ch = curl_init($_POST['webhook_url']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_exec($ch);

// 攻击目标：http://169.254.169.254/ (AWS 元数据)
// 攻击目标：http://localhost:6379/ (Redis)
// 攻击目标：file:///etc/passwd
```

### 审计检查清单

- [ ] 搜索 `file_get_contents|curl_exec|fsockopen`
- [ ] 追踪 URL 参数
- [ ] 检查白名单实现
- [ ] 测试内网 IP 段 (127.0.0.1, 169.254.169.254, 10.x.x.x)

---

## 8. 认证 / 会话漏洞

**严重程度**: 视情况 (CVSS 4.0-9.8) | **可利用**: 是

### 常见漏洞模式

| 问题 | 漏洞代码 | 风险 |
|------|----------|------|
| 弱哈希 | `md5($password)` | 🔴 彩虹表 |
| 无盐 | `sha1($pass)` | 🔴 预计算哈希 |
| 会话固定 | `session_id($_GET['sID'])` | 🟡 劫持 |
| URL 中的会话 | URL 中 `sid=<session>` | 🟡 日志暴露 |
| 可预测令牌 | `mt_rand()` 生成令牌 | 🔴 账户接管 |

### 漏洞代码示例

```php
// 漏洞：MD5 密码哈希
$hash = md5($_POST['password']);

// 漏洞：会话固定
session_start();
session_id($_GET['session_id']);

// 漏洞：弱令牌生成
$token = md5(mt_rand());

// 安全：bcrypt 密码哈希
$hash = password_hash($_POST['password'], PASSWORD_BCRYPT);

// 安全：random_bytes 生成令牌
$token = bin2hex(random_bytes(32));
```

### 审计检查清单

- [ ] 搜索 `password_hash|md5|sha1|crypt`
- [ ] 检查 `session_id()` 使用
- [ ] 验证令牌生成方法
- [ ] 追踪会话处理

---

## 9. 文件上传漏洞

**严重程度**: 高-严重 (CVSS 8.0-9.8) | **可利用**: 常导致 RCE

### 漏洞模式

| 问题 | 漏洞代码 | 风险 |
|------|----------|------|
| 无扩展名检查 | 直接移动上传文件 | 🔴 通过 .php RCE |
| MIME 嗅探 | `$type = $_FILES['f']['type']` | 🔴 绕过 |
| 覆盖 | 上传到可预测路径 | 🔴 配置覆盖 |
| 路径穿越 | 直接使用 `$_FILES['f']['name']` | 🔴 覆盖 |

### 漏洞代码示例

```php
// 漏洞：直接移动无验证
move_uploaded_file($_FILES['upload']['tmp_name'],
    "/var/www/uploads/" . $_FILES['upload']['name']);

// 漏洞：检查上传类型
if ($_FILES['f']['type'] == 'image/jpeg') { ... }

// 漏洞：客户端提供的文件名
$name = $_POST['filename'];
file_put_contents("/uploads/$name", $data);

// 安全：生成随机文件名
$ext = pathinfo($_FILES['f']['name'], PATHINFO_EXTENSION);
$filename = bin2hex(random_bytes(16)) . ".$ext";
```

### 审计检查清单

- [ ] 搜索 `move_uploaded_file|copy|file_put_contents`
- [ ] 验证扩展名验证
- [ ] 检查 MIME 类型验证
- [ ] 追踪文件名处理

---

## 10. XXE (XML 外部实体)

**严重程度**: 高 (CVSS 8.0+) | **可利用**: 是 (文件读取, SSRF)

### 危险函数

| 函数 | 风险 | 示例 |
|------|------|------|
| `simplexml_load_string()` | 含 XML 内容 | `simplexml_load_string($_GET['xml'])` |
| `DOMDocument->loadXML()` | 无 LIBXML_NOENT | `DOMDocument->loadXML($userXml)` |
| `SimpleXMLElement` | 直接解析 | `new SimpleXMLElement($xml)` |

### 漏洞代码示例

```php
// 漏洞：XXE
$xml = $_GET['xml'];
$dom = new DOMDocument();
$dom->loadXML($xml);

// 安全：禁用实体加载
$dom->loadXML($xml, LIBXML_NOENT); // NOENT 启用实体 - 有漏洞!
$dom->loadXML($xml); // 正确：无标志
libxml_disable_entity_loader(true);

// 安全：使用 JSON
$data = json_decode($_GET['data']);
```

### 审计检查清单

- [ ] 搜索 `loadXML|simplexml_load_string|SimpleXMLElement`
- [ ] 检查 `LIBXML_NOENT` 标志（危险）
- [ ] 验证 `libxml_disable_entity_loader(true)` 使用
- [ ] 推荐尽量使用 JSON 代替 XML

---

## 快速参考：Source → Sink 模式

| Source | 中间处理 | Sink | 漏洞类型 |
|--------|----------|------|----------|
| `$_GET['param']` | 字符串拼接 | `mysqli_query()` | SQL 注入 |
| `$_GET['cmd']` | 无 | `system()` | 命令注入 |
| `$_GET['file']` | 路径拼接 | `include()` | 文件包含/RCE |
| `$_POST['html']` | Echo | `echo` | XSS |
| `$_COOKIE['data']` | 无 | `unserialize()` | PHP 对象注入 |
| `$_GET['url']` | 无 | `file_get_contents()` | SSRF |
| `$_GET['path']` | 路径拼接 | `readfile()` | 路径穿越 |

---

## 相关参考

- **Skill**: `SKILL.md` (主审计工作流程)
- **Templates**: `templates/vulnerability-report-template.md`
