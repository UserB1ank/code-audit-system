# Python 漏洞指南

Python 应用程序中常见的安全漏洞类型，包含对应的危险函数、审计模式和实际案例。

## 如何使用

审计 Python 代码时查阅本指南。将发现的漏洞与这些模式进行匹配，追踪 Source → Sink 链。

## 审计总体流程

1. **信息收集与代码理解** — 阅读项目文档、README、API 文档；识别主要入口点（`main.py`、`app.py`、`views.py`、路由定义等）；理解数据流（用户输入 → 处理函数 → 输出响应）；列出所有第三方依赖及版本（`requirements.txt`、`Pipfile`、`setup.py` 等）。
2. **威胁建模** — 确定攻击面：HTTP 参数、上传文件、命令行参数、环境变量、数据库查询、外部 API 调用。标出敏感功能：认证、授权、密码重置、支付、文件操作、命令执行、序列化/反序列化。
3. **人工代码审查** — 按漏洞类型逐类检查代码模式；重点关注用户可控数据流入危险函数的地方；跟踪关键变量从输入到使用结束的全过程。
4. **动态验证（可选）** — 手动构造恶意输入，观察行为。
5. **输出报告** — 记录漏洞位置、代码片段、危害、利用方法、修复建议。

---

## 1. SQL 注入

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是

### 危险函数/模式

| 函数/模式 | 风险 | 说明 |
|-----------|------|------|
| `cursor.execute(sql + var)` | 🔴 严重 | 字符串拼接 SQL |
| `cursor.execute(f"SELECT ... {var}")` | 🔴 严重 | f-string 拼接 SQL |
| `cursor.execute("SELECT ... %s" % var)` | 🔴 严重 | % 格式化拼接 |
| `Model.objects.raw(sql)` | 🔴 严重 | ORM raw SQL |
| `Model.objects.extra(where=...)` | 🟡 中等 | ORM extra 子句 |
| `cursor.execute(sql, (param,))` | 🟢 安全 | 参数化查询 |

**常见模块**：`sqlite3`、`MySQLdb`、`psycopg2`、`pymysql`、Django ORM (`raw()`、`extra()`)

### 漏洞代码示例

```python
# 漏洞：字符串拼接
name = request.GET.get('name')
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")

# 漏洞：f-string
user_id = request.args.get('id')
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# 漏洞：% 格式化
query = "SELECT * FROM users WHERE name = '%s'" % name
cursor.execute(query)

# 漏洞：Django raw SQL
User.objects.raw("SELECT * FROM users WHERE name = '%s'" % name)

# 安全：参数化查询
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))

# 安全：Django ORM
User.objects.filter(name=name)
```

### 审计检查清单

- [ ] 搜索 `execute(`、`raw(`、`extra(`
- [ ] 检查 SQL 字符串是否包含 `+`、`%`、`f"..."` 拼接
- [ ] 追踪变量来源（`request.GET`、`request.POST`、`request.args`、`json.loads(request.body)`）
- [ ] 确认变量是否经过参数化处理（`%s` 占位 + 参数元组）

### 真实 CVE 案例：研究员如何发现它

**CVE-2019-14234 (Django SQL 注入)**
- **发现思路**: 研究员不是 grep `execute(`，而是先问"Django ORM 的哪些 API 接受原始字符串？"，然后翻文档找到 `JSONField` 的 `key_transform` 在构造 SQL 时直接拼接了键名。
- **关键洞察**: 漏洞不在 `execute()`，而在 ORM 内部的 `__` 查询语法（`filter(data__key=val)`），键名 `key` 未经转义就进入了 SQL。
- **审计启示**: 不要只看显式 SQL 调用，**ORM 的动态查询构造器**（`filter()`、`annotate()`、`extra()`）同样可能拼接用户输入。

---

## 2. 命令注入

**严重程度**: 严重 (CVSS 9.8) | **可利用**: 是（远程代码执行）

### 危险函数/模式

| 函数 | 风险 | 说明 |
|------|------|------|
| `os.system(cmd)` | 🔴 严重 | 直接执行 shell 命令 |
| `os.popen(cmd)` | 🔴 严重 | shell 命令 + 读取输出 |
| `subprocess.call(cmd, shell=True)` | 🔴 严重 | shell=True 允许 shell 元字符 |
| `subprocess.Popen(cmd, shell=True)` | 🔴 严重 | 同上 |
| `subprocess.check_output(cmd, shell=True)` | 🔴 严重 | 同上 |
| `eval(expr)` | 🔴 严重 | 执行任意 Python 表达式 |
| `exec(code)` | 🔴 严重 | 执行任意 Python 代码 |
| `__import__(mod)` | 🔴 严重 | 动态导入任意模块 |

**常见模块**：`os`、`subprocess`、`sys`

### 漏洞代码示例

```python
# 漏洞：用户输入直接进入 shell 命令
host = request.GET.get('host')
os.system("ping -c 4 " + host)

# 漏洞：subprocess shell=True
filename = request.POST.get('file')
subprocess.call("cat " + filename, shell=True)

# 漏洞：eval 执行用户表达式
expr = request.args.get('calc')
result = eval(expr)

# 漏洞：exec 执行用户代码
code = request.data.decode()
exec(code)

# 安全：列表参数（不经过 shell）
subprocess.call(["ping", "-c", "4", host])

# 安全：shlex.quote 转义
import shlex
os.system("ping -c 4 " + shlex.quote(host))
```

### 审计检查清单

- [ ] 搜索 `os.system(`、`os.popen(`、`subprocess.call(`、`subprocess.Popen(`、`subprocess.check_output(`
- [ ] 检查 `shell=True` 参数
- [ ] 搜索 `eval(`、`exec(`、`__import__(`、`compile(`
- [ ] 追踪用户输入是否到达这些函数
- [ ] 检查是否使用 `shlex.quote()` 或列表参数形式

### 真实 CVE 案例：研究员如何发现它

**CVE-2021-41091 (Moby/Docker 命令注入)**
- **发现思路**: 研究员不是搜索 `subprocess`，而是先问"Docker 在哪里调用外部工具？"，找到 `runc` 调用链，发现容器路径中的特殊字符（换行符）会被传入 shell 命令，导致宿主机命令注入。
- **关键洞察**: 漏洞在**路径参数**而非"命令参数"，研究员通过追踪"文件系统路径如何变成 shell 参数"发现了注入点。
- **审计启示**: 命令注入不只在 `cmd` 参数里，**文件名、路径、环境变量**传入 shell 时同样危险。搜索所有 `shell=True` + 包含路径/文件名变量的调用。

---

## 3. 路径遍历（Path Traversal）

**严重程度**: 高 (CVSS 7.5-8.0) | **可利用**: 是

### 危险函数/模式

| 函数/模式 | 风险 | 说明 |
|-----------|------|------|
| `open(user_path)` | 🔴 严重 | 用户控制文件路径 |
| `os.path.join(base, user_input)` | 🟡 中等 | `..` 可绕过基目录 |
| `shutil.copy(src, dst)` | 🔴 严重 | 任意文件复制 |
| `shutil.move(src, dst)` | 🔴 严重 | 任意文件移动 |
| `os.listdir(user_dir)` | 🟡 中等 | 目录泄露 |

**常见模块**：`open`、`os.path`、`pathlib`、`shutil`

### 漏洞代码示例

```python
# 漏洞：直接拼接用户文件名
filename = request.GET.get('file')
with open("/var/uploads/" + filename, 'rb') as f:
    return f.read()

# 漏洞：os.path.join 无法阻止绝对路径
user_path = request.args.get('path')
full_path = os.path.join("/var/www/files", user_path)
# 如果 user_path 以 / 开头，join 会忽略 base 目录
# user_path = "/etc/passwd" → full_path = "/etc/passwd"

# 安全：路径规范化 + 前缀校验
import os
base = os.path.realpath("/var/uploads/")
filepath = os.path.realpath(os.path.join(base, filename))
if not filepath.startswith(base + os.sep):
    raise ValueError("path traversal detected")
with open(filepath, 'rb') as f:
    return f.read()
```

### 审计检查清单

- [ ] 搜索 `open(`、`os.listdir(`、`shutil.copy(`、`shutil.move(`
- [ ] 检查路径参数是否包含用户输入
- [ ] 测试 `../`、绝对路径（`/` 开头）、URL 编码绕过
- [ ] 验证路径规范化（`os.path.realpath`）+ 前缀校验

---

## 4. 反序列化漏洞

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是（RCE）

### 危险函数/模式

| 函数 | 风险 | 说明 |
|------|------|------|
| `pickle.loads(data)` | 🔴 严重 | 任意代码执行 |
| `pickle.load(f)` | 🔴 严重 | 从文件反序列化 |
| `cPickle.loads(data)` | 🔴 严重 | 同 pickle |
| `dill.loads(data)` | 🔴 严重 | 更强大的 pickle 变体 |
| `yaml.load(data)` | 🔴 严重 | 默认允许任意 Python 对象 |
| `marshal.loads(data)` | 🔴 严重 | 代码对象反序列化 |
| `yaml.safe_load(data)` | 🟢 安全 | 仅加载基本类型 |

**常见模块**：`pickle`、`cPickle`、`dill`、`yaml`、`marshal`

### 漏洞代码示例

```python
# 漏洞：pickle 反序列化用户输入
import pickle
data = request.cookies.get('session')
session = pickle.loads(base64.b64decode(data))

# 漏洞：yaml.load 未使用 safe_load
import yaml
config = yaml.load(request.data)  # 默认 Loader 允许任意对象

# 漏洞：从文件反序列化
with open(user_file, 'rb') as f:
    obj = pickle.load(f)

# 安全：yaml.safe_load
config = yaml.safe_load(request.data)

# 安全：使用 JSON 代替 pickle
import json
session = json.loads(request.cookies.get('session'))
```

### 审计检查清单

- [ ] 搜索 `pickle.loads(`、`pickle.load(`、`cPickle`、`dill`、`marshal.loads(`
- [ ] 搜索 `yaml.load(`，检查是否使用了 `safe_load` 或 `Loader=yaml.SafeLoader`
- [ ] 追踪反序列化数据来源（cookie、POST body、消息队列、文件）
- [ ] 评估是否可替换为 JSON 等安全格式

---

## 5. SSTI（服务端模板注入）

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是（常导致 RCE）

### 危险函数/模式

| 函数/模式 | 风险 | 说明 |
|-----------|------|------|
| `render_template_string(user_input)` | 🔴 严重 | Flask 直接渲染用户输入 |
| `Template(user_input).render()` | 🔴 严重 | Jinja2 直接渲染字符串 |
| `Template(user_input)` (Mako) | 🔴 严重 | Mako 模板注入 |
| `render_template('file.html', **ctx)` | 🟢 安全 | 从模板文件渲染 |

**常见模块**：`Jinja2`（Flask）、`Mako`、`Tornado`、`Django templates`

### 漏洞代码示例

```python
# 漏洞：Flask 拼接用户输入到模板
from flask import render_template_string
name = request.args.get('name')
return render_template_string("Hello " + name)

# 漏洞：Jinja2 直接渲染用户输入
from jinja2 import Template
user_input = request.form.get('content')
return Template(user_input).render()

# 利用载荷（Jinja2）：
# {{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
# {{ ''.__class__.__mro__[1].__subclasses__() }}

# 安全：参数化模板渲染
return render_template('greet.html', name=name)
```

### 审计检查清单

- [ ] 搜索 `render_template_string(`、`Template(`
- [ ] 检查模板字符串是否包含用户可控变量
- [ ] 验证是否使用 `render_template`（模板文件）代替 `render_template_string`（字符串拼接）
- [ ] 检查 Jinja2 sandbox 模式（`SandboxedEnvironment`）

---

## 6. XXE（XML 外部实体注入）

**严重程度**: 高 (CVSS 8.0+) | **可利用**: 是

### 危险函数/模式

| 函数/模式 | 风险 | 说明 |
|-----------|------|------|
| `xml.etree.ElementTree.parse()` | 🟡 中等 | 标准库，默认不解析外部实体 |
| `xml.etree.ElementTree.fromstring()` | 🟡 中等 | 同上 |
| `lxml.etree.parse()` | 🟡 中等 | 默认可能允许 |
| `lxml.etree.fromstring()` | 🟡 中等 | 同上 |
| `defusedxml` | 🟢 安全 | 专门防御 XXE 的替代库 |

**常见模块**：`xml.etree.ElementTree`、`lxml`、`xml.dom.minidom`

### 漏洞代码示例

```python
# 漏洞：lxml 未禁用外部实体
from lxml import etree
xml_data = request.data
root = etree.fromstring(xml_data)  # 可能解析外部实体

# 安全：lxml 禁用实体解析
from lxml import etree
parser = etree.XMLParser(resolve_entities=False)
root = etree.fromstring(xml_data, parser)

# 安全：使用 defusedxml
import defusedxml.ElementTree as ET
root = ET.fromstring(xml_data)
```

### 审计检查清单

- [ ] 搜索 `etree.parse(`、`etree.fromstring(`、`xml.dom`、`minidom`
- [ ] 若使用 lxml，检查是否设置 `resolve_entities=False`
- [ ] 建议使用 `defusedxml` 替代标准库 XML 解析
- [ ] 检查 SOAP / XML-RPC 端点

---

## 7. SSRF（服务端请求伪造）

**严重程度**: 高 (CVSS 8.6-9.0) | **可利用**: 是

### 危险函数/模式

| 函数 | 风险 | 说明 |
|------|------|------|
| `requests.get(user_url)` | 🔴 严重 | 用户控制请求 URL |
| `urllib.request.urlopen(user_url)` | 🔴 严重 | 用户控制 URL |
| `http.client.HTTPConnection(host)` | 🔴 严重 | 原始 HTTP 连接 |
| `aiohttp.ClientSession().get(user_url)` | 🔴 严重 | 异步请求 |

### 漏洞代码示例

```python
# 漏洞：用户提供的 URL 直接请求
import requests
url = request.GET.get('url')
resp = requests.get(url)
return resp.text

# 漏洞：urllib
import urllib.request
url = request.args.get('url')
data = urllib.request.urlopen(url).read()

# 攻击目标：http://169.254.169.254/ (AWS 元数据)
# 攻击目标：http://localhost:6379/ (Redis)
# 攻击目标：file:///etc/passwd

# 安全：URL 白名单 + 域名校验
from urllib.parse import urlparse
ALLOWED_DOMAINS = {'api.example.com', 'cdn.example.com'}
parsed = urlparse(url)
if parsed.hostname not in ALLOWED_DOMAINS:
    raise ValueError("blocked domain")
```

### 审计检查清单

- [ ] 搜索 `requests.get(`、`requests.post(`、`urlopen(`、`HTTPConnection(`
- [ ] 追踪 URL 参数来源
- [ ] 检查是否有白名单/域名校验
- [ ] 测试内网 IP（`127.0.0.1`、`169.254.169.254`、`10.x.x.x`）和协议（`file://`）

---

## 8. 开放重定向

**严重程度**: 中 (CVSS 5.4-6.1) | **可利用**: 是

### 危险函数/模式

| 函数 | 风险 | 说明 |
|------|------|------|
| `flask.redirect(user_url)` | 🟡 中等 | 用户控制重定向目标 |
| `HttpResponseRedirect(user_url)` | 🟡 中等 | Django 同上 |

### 漏洞代码示例

```python
# 漏洞：Flask 重定向未校验
from flask import redirect, request
return redirect(request.args.get('next'))

# 漏洞：Django
from django.http import HttpResponseRedirect
return HttpResponseRedirect(request.GET.get('next'))

# 安全：白名单校验
from urllib.parse import urlparse
next_url = request.args.get('next', '/')
parsed = urlparse(next_url)
if parsed.hostname and parsed.hostname not in ALLOWED_HOSTS:
    next_url = '/'
return redirect(next_url)
```

### 审计检查清单

- [ ] 搜索 `redirect(`、`HttpResponseRedirect(`
- [ ] 检查重定向参数是否来自用户输入
- [ ] 验证是否有白名单或域名校验

---

## 9. 敏感信息泄露

**严重程度**: 中-高 (CVSS 5.0-7.5) | **可利用**: 视场景

### 危险模式

| 模式 | 风险 | 说明 |
|------|------|------|
| `DEBUG = True` 生产环境 | 🔴 严重 | 泄露完整栈轨迹和代码 |
| `print(password)` | 🔴 严重 | 密码输出到日志 |
| `logger.debug(api_key)` | 🟡 中等 | 敏感字段记入日志 |
| `traceback.print_exc()` | 🟡 中等 | 向用户暴露栈轨迹 |
| `except: pass` | 🟡 中等 | 静默吞掉错误，可能隐藏攻击 |
| 硬编码 `SECRET_KEY = "..."` | 🔴 严重 | 密钥泄露到源码仓库 |

### 漏洞代码示例

```python
# 漏洞：生产环境 DEBUG 模式
# settings.py
DEBUG = True

# 漏洞：硬编码密钥
SECRET_KEY = "my-super-secret-key-12345"
API_KEY = "sk-abc123def456"

# 漏洞：日志记录敏感数据
import logging
logging.debug(f"User login: password={password}")

# 漏洞：异常暴露栈轨迹
@app.errorhandler(Exception)
def handle_error(e):
    return str(e), 500  # 向用户暴露错误详情

# 安全：密钥从环境变量读取
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
```

### 审计检查清单

- [ ] 搜索 `DEBUG = True`、`SECRET_KEY = "`、`API_KEY = "`、`PASSWORD = "`
- [ ] 检查 `print(`、`logger.debug(` 是否输出敏感信息
- [ ] 搜索 `traceback.print_exc(`、`sys.exc_info(`
- [ ] 检查 `except: pass` 或 `except Exception: pass` 模式
- [ ] 验证错误处理是否向用户暴露内部信息

---

## 10. 弱加密与硬编码密钥

**严重程度**: 高 (CVSS 7.0-9.0) | **可利用**: 是

### 危险函数/模式

| 函数/模式 | 风险 | 说明 |
|-----------|------|------|
| `hashlib.md5(password)` | 🔴 严重 | MD5 不安全 |
| `hashlib.sha1(password)` | 🔴 严重 | SHA1 不安全 |
| `random.random()` 用于安全场景 | 🔴 严重 | 可预测 |
| `hmac.compare_digest()` | 🟢 安全 | 常量时间比较 |
| `a == b`（密码/令牌比较） | 🟡 中等 | 时间攻击 |

**常见模块**：`hashlib`、`cryptography`、`jwt`、`hmac`

### 漏洞代码示例

```python
# 漏洞：MD5/SHA1 用于密码
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# 漏洞：random 用于生成令牌
import random
token = str(random.randint(100000, 999999))

# 漏洞：== 比较密码（时间攻击）
if request.args.get('token') == SECRET_TOKEN:
    return "authorized"

# 安全：bcrypt 哈希密码
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 安全：secrets 生成令牌
import secrets
token = secrets.token_hex(32)

# 安全：常量时间比较
import hmac
if hmac.compare_digest(request.args.get('token'), SECRET_TOKEN):
    return "authorized"
```

### 审计检查清单

- [ ] 搜索 `hashlib.md5(`、`hashlib.sha1(`
- [ ] 搜索 `random.random()`、`random.randint()`（安全场景应使用 `secrets` 模块）
- [ ] 检查密码/令牌比较是否使用 `hmac.compare_digest()`
- [ ] 搜索硬编码密钥 `SECRET_KEY = "`、`API_KEY = "`

---

## 11. 权限绕过与逻辑漏洞

**严重程度**: 视场景 (CVSS 4.0-9.8) | **可利用**: 是

### 危险模式

| 模式 | 风险 | 说明 |
|------|------|------|
| 缺少 `@login_required` 装饰器 | 🔴 严重 | 未认证访问 |
| 仅验证身份未验证权限 | 🔴 严重 | 水平越权 |
| 对象 ID 未关联当前用户 | 🔴 严重 | IDOR |
| 管理路由无权限检查 | 🔴 严重 | 垂直越权 |

### 漏洞代码示例

```python
# 漏洞：水平越权（IDOR）
@app.route('/api/user/<user_id>/profile')
def get_profile(user_id):
    # 未验证 user_id 是否属于当前登录用户
    user = User.query.get(user_id)
    return jsonify(user.to_dict())

# 漏洞：管理接口无权限检查
@app.route('/admin/config', methods=['POST'])
def update_config():
    # 缺少角色检查
    Config.update(request.json)
    return "ok"

# 安全：验证资源归属
@app.route('/api/user/<user_id>/profile')
@login_required
def get_profile(user_id):
    if int(user_id) != current_user.id:
        abort(403)
    user = User.query.get(user_id)
    return jsonify(user.to_dict())

# 安全：角色检查
@app.route('/admin/config', methods=['POST'])
@login_required
@admin_required
def update_config():
    Config.update(request.json)
    return "ok"
```

### 审计检查清单

- [ ] 阅读所有 `@app.route` 或 URL 模式，确认敏感函数有权限检查
- [ ] 检查对象 ID 是否与当前用户关联验证
- [ ] 对比权限检查装饰器之间的差异
- [ ] 检查密码重置流程（token 有效期、用户枚举）
- [ ] 检查支付/积分操作（重复使用、负数金额）
- [ ] 检查文件上传（类型检查是否仅依赖扩展名、大小限制）

---

## 12. 文件上传漏洞

**严重程度**: 高-严重 (CVSS 8.0-9.8) | **可利用**: 常导致 RCE

### 危险模式

| 模式 | 风险 | 说明 |
|------|------|------|
| 直接使用用户提供的文件名 | 🔴 严重 | 路径遍历/覆盖 |
| 仅检查扩展名 | 🟡 中等 | 可伪造 |
| 仅检查 MIME type | 🟡 中等 | 客户端可控 |
| 上传到 web 可访问目录 | 🔴 严重 | 直接执行 |
| 无大小限制 | 🟡 中等 | 存储耗尽 |

### 漏洞代码示例

```python
# 漏洞：直接保存用户文件名
@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['file']
    f.save('/var/www/uploads/' + f.filename)  # 文件名可控

# 漏洞：仅检查扩展名
ext = f.filename.split('.')[-1]
if ext in ['jpg', 'png']:
    f.save('/var/www/uploads/' + f.filename)

# 安全：随机文件名 + 白名单 + 内容校验
import secrets
from pathlib import Path

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_SIZE = 5 * 1024 * 1024  # 5MB

ext = Path(f.filename).suffix.lower().lstrip('.')
if ext not in ALLOWED_EXTENSIONS:
    abort(400)
f.seek(0, 2)
size = f.tell()
f.seek(0)
if size > MAX_SIZE:
    abort(400)
new_name = secrets.token_hex(16) + '.' + ext
f.save('/var/www/uploads/' + new_name)
```

### 审计检查清单

- [ ] 搜索 `f.save(`、`save(`、`file.save(`
- [ ] 检查文件名是否来自用户且未过滤
- [ ] 验证扩展名白名单 + 内容校验
- [ ] 检查上传目录是否 web 可直接访问
- [ ] 检查文件大小限制

---

## 快速参考：Source → Sink 模式

| Source | 中间处理 | Sink | 漏洞类型 |
|--------|----------|------|----------|
| `request.GET.get('id')` | 字符串拼接 | `cursor.execute()` | SQL 注入 |
| `request.args.get('cmd')` | 无 | `os.system()` | 命令注入 |
| `request.GET.get('file')` | 路径拼接 | `open()` | 路径遍历 |
| `request.cookies.get('data')` | `base64.b64decode` | `pickle.loads()` | 反序列化 RCE |
| `request.args.get('name')` | 拼接字符串 | `render_template_string()` | SSTI |
| `request.data` | 无 | `yaml.load()` | 反序列化 |
| `request.GET.get('url')` | 无 | `requests.get()` | SSRF |
| `request.args.get('next')` | 无 | `redirect()` | 开放重定向 |

---

## 危险函数速查清单

```
# 命令执行
os.system, os.popen, subprocess.call, subprocess.Popen, subprocess.check_output, eval, exec, __import__, compile

# 反序列化
pickle.loads, pickle.load, cPickle.loads, dill.loads, yaml.load, marshal.loads

# 文件操作
open, os.listdir, shutil.copy, shutil.move, os.remove, os.rename

# 模板注入
render_template_string, Template(

# 网络请求
requests.get, requests.post, urllib.request.urlopen, http.client.HTTPConnection

# XML 解析
xml.etree.ElementTree.parse, xml.etree.ElementTree.fromstring, lxml.etree.parse

# 重定向
redirect, HttpResponseRedirect

# SQL
execute(, raw(, extra(
```

---

## 13. 逻辑类漏洞（无需 Source→Sink）

### 13.1 认证绕过

**严重程度**: 严重 (CVSS 8.0+) | **可利用**: 是

**常见模式**:
```python
# ❌ 装饰器缺失：敏感视图忘记加 @login_required
def admin_delete_user(request, user_id): ...

# ❌ JWT alg:none 绕过
header = base64.decode(token.split('.')[0])
# 如果 alg 字段未强制校验，攻击者可伪造 alg:none

# ❌ 条件逻辑缺陷
if user.role == 'admin' or debug_mode:  # debug_mode 可被外部控制？
    grant_access()
```

**审计检查清单**:
- [ ] 搜索所有路由/视图，确认每个敏感操作前有鉴权装饰器
- [ ] 搜索 JWT 验证代码，确认 `algorithms` 参数被强制指定（不接受 `none`）
- [ ] 检查条件分支中是否有可被外部控制的"后门"变量

**真实 CVE 案例**:
- **CVE-2022-29217 (PyJWT 认证绕过)**: 研究员发现 PyJWT 在某些版本中，若调用方未指定 `algorithms` 参数，攻击者可在 JWT header 中指定 `alg:none` 绕过签名验证。发现思路：审查"默认行为"——库在参数缺失时做了什么？

---

### 13.2 越权 / IDOR

**严重程度**: 高 (CVSS 7.0+) | **可利用**: 是

**常见模式**:
```python
# ❌ 只校验登录，未校验所有权
@login_required
def get_document(request, doc_id):
    doc = Document.objects.get(id=doc_id)  # 未检查 doc.owner == request.user
    return JsonResponse(doc.data)

# ❌ 可预测 ID
doc_id = request.GET.get('id')  # 如果 ID 是自增整数，可枚举
```

**审计检查清单**:
- [ ] 搜索所有 `.get(id=...)` / `.filter(id=...)` 调用，确认有 `owner=request.user` 或等效校验
- [ ] 检查资源 ID 是否可预测（自增整数 vs UUID）
- [ ] 检查批量操作接口是否逐条校验权限

---

### 13.3 竞态条件 / TOCTOU

**严重程度**: 高 (CVSS 7.0+) | **可利用**: 是（需并发请求）

**常见模式**:
```python
# ❌ TOCTOU：check 和 use 之间有窗口
if user.balance >= amount:      # check
    time.sleep(0)               # 窗口（即使无 sleep，并发也可利用）
    user.balance -= amount      # use（未加锁）
    user.save()

# ❌ 文件 TOCTOU
if os.path.exists(path):        # check
    with open(path) as f:       # use（path 可能已被替换为符号链接）
        data = f.read()
```

**审计检查清单**:
- [ ] 搜索"先查询余额/库存再扣减"的模式，确认使用数据库事务或 `select_for_update()`
- [ ] 搜索 `os.path.exists()` + `open()` 组合，检查是否有符号链接攻击风险
- [ ] 检查文件上传：临时文件名是否可预测？

---

### 13.4 加密误用

**严重程度**: 高 (CVSS 7.0+) | **可利用**: 是

**常见模式**:
```python
# ❌ 密码用 MD5/SHA1 存储（无盐）
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# ❌ 可预测随机数用于安全场景
import random
token = random.randint(100000, 999999)  # 应用 secrets 模块

# ❌ ECB 模式（相同明文产生相同密文）
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_ECB)

# ❌ 硬编码密钥
SECRET_KEY = "hardcoded_secret_123"
```

**审计检查清单**:
- [ ] 搜索 `hashlib.md5`、`hashlib.sha1` 用于密码存储
- [ ] 搜索 `random.` 用于令牌/验证码生成（应用 `secrets.`）
- [ ] 搜索 `AES.MODE_ECB`
- [ ] 搜索硬编码字符串赋值给 `SECRET`、`KEY`、`PASSWORD`、`TOKEN` 变量

---

## 审计小技巧

- **字符串拼接热点**：用编辑器高亮 `+`、`%`、`f"{}"` 附近的字符串，关注 SQL 和命令上下文。
- **注释线索**：留意 `# TODO`、`# FIXME`、`# HACK`，往往隐藏不安全写法。
- **测试代码**：检查 `tests/` 目录中是否有硬编码凭据或危险的 mock。
- **通配符导入**：如果 `from x import *`，去 `x.py` 查看实际定义。
- **异常安全**：`except: pass` 会隐藏错误，可能允许攻击者绕过检查。
- **时间攻击**：密码/令牌比较是否使用 `==` 还是 `hmac.compare_digest`（后者更安全）。
- **依赖风险**：手动检查 `requirements.txt`，对高影响包（Django、Flask、requests）回忆或查阅常见历史漏洞模式。
