# Java 代码审计参考

本参考用于审计 Java Web 应用，识别漏洞和攻击面。

## 技术识别

**文件指示器**：
- `pom.xml` - Maven 依赖管理
- `build.gradle` - Gradle 依赖管理
- `src/main/java/` - Java 源代码
- `src/main/resources/` - 配置文件
- `WEB-INF/web.xml` - Java Web 配置
- `application.properties` / `application.yml` - Spring Boot 配置

**常见框架**：
- Spring Boot - `src/main/java/`, `application.yml`
- Struts2 - `struts.xml`, `*-action.xml`
- Shiro - `shiro.ini`, `ShiroFilter`
- javax.servlet - 原生 Servlet/JSP
- MyBatis - `*Mapper.xml`, `@Select`, `@Insert`

---

## 高风险区域

### 1. Spring Boot 安全漏洞

**危险注解/模式**：
```java
// 危险：任意文件读取
@RequestMapping("/read")
public String readFile(@RequestParam String path) {
    return new String(Files.readAllBytes(Paths.get(path)));
}

// 危险：SpEL 注入
@PostMapping("/eval")
public String eval(@RequestParam String input) {
    return parser.parseExpression(input).getValue().toString();
}

// 危险：SQL 拼接
@Query("SELECT * FROM User WHERE name = '" + name + "'")
```

**审计重点**：
- 搜索 `Files.readAllBytes()`, `FileInputStream` 处理用户输入
- 搜索 `parser.parseExpression()` 或 `SpEL` 解析用户输入
- 搜索 `@Query` 注解中的字符串拼接
- 检查 `@RequestParam`, `@RequestBody` 用户输入入口

### 2. SQL 注入

**危险模式**：
```java
// MyBatis 动态 SQL 拼接（高危）
@Select("SELECT * FROM user WHERE id = ${id}")
// 攻击: id=1 OR 1=1 返回所有用户

// JDBC 字符串拼接（极高危）
String sql = "SELECT * FROM users WHERE id = " + userId;
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(sql);

// PreparedStatement（安全）
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);
```

**审计重点**：
- 搜索 `${` 在 MyBatis mapper 中（使用 `#{}` 安全）
- 搜索 `Statement` 而非 `PreparedStatement`
- 搜索 `createStatement()`, `executeQuery()` 带字符串拼接
- 检查 MyBatis XML mapper 的 `<if test="...">` 拼接

### 3. 命令注入

**危险函数**：
```java
Runtime.getRuntime().exec(command);           // 极高危
ProcessBuilder pb = new ProcessBuilder(cmd);  // 极高危
```

**审计重点**：
- 搜索 `Runtime.getRuntime().exec()`
- 搜索 `new ProcessBuilder()`
- 检查用户输入是否经过 `command.split()` 或验证
- 搜索 `Groovy` 脚本执行（`GroovyShell.evaluate()`）

### 4. 路径遍历 / 文件操作

**危险模式**：
```java
// 危险：用户输入进入文件路径
Path path = Paths.get(baseDir, userInput);
Files.readAllBytes(path);

// 危险：SSRF
URL url = new URL(userInputUrl);
HttpURLConnection conn = (HttpURLConnection) url.openConnection();
```

**审计重点**：
- 搜索 `Paths.get()`, `File()` 接受用户输入
- 搜索 `Files.readAllBytes()`, `FileInputStream`
- 搜索 `new URL()` 打开网络连接
- 检查 `Path` 是否经过 `normalize()`, `toRealPath()` 验证

### 5. 反序列化

**危险场景**：
```java
// 危险：Java 原生反序列化
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();

// 危险：XMLDecoder
XMLDecoder decoder = new XMLDecoder(inputStream);
Object obj = decoder.readObject();

// 危险：XStream
XStream xstream = new XStream();
xstream.fromXML(inputStream);

// 危险：Jackson YAML
ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
Object obj = mapper.readValue(inputStream, Object.class);
```

**审计重点**：
- 搜索 `ObjectInputStream`, `readObject()`
- 搜索 `XMLDecoder`, `readObject()`
- 搜索 `XStream.fromXML()`
- 搜索 `ObjectMapper` 处理 YAML/JSON
- 检查是否使用 `ObjectMapperConfig` 启用类型限制

### 6. SpEL 注入

**危险模式**：
```java
// 危险：SpEL 解析用户输入
SpelExpressionParser parser = new SpelExpressionParser();
Expression exp = parser.parseExpression(userInput);
exp.getValue();

// 危险：TemplateEngine (Thymeleaf)
templateEngine.process(userTemplate, context);

// 危险：OGNL
Object obj = ognl.getValue(userExpression, root);
```

**审计重点**：
- 搜索 `SpelExpressionParser`, `parseExpression()`
- 搜索 `Ognl.getValue()`, `Ognl.setValue()`
- 检查模板引擎是否禁用原始文字表达式

### 7. SSRF（服务端请求伪造）

**危险模式**：
```java
// 危险：用户控制 URL
URL url = new URL(userInput);
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder().uri(url).build();
```

**审计重点**：
- 搜索 `HttpClient`, `HttpRequest` 构建用户指定的 URI
- 检查是否验证 URI scheme (http/https), host, port
- 检查是否解析重定向后的 URL
- 搜索 `RestTemplate`, `WebClient` 使用用户输入构建 URL

### 8. 认证与会话

**危险模式**：
```java
// 危险：JWT 不验证签名
Algorithm algorithm = Algorithm.none(); // 极高危

// 危险：弱密钥
Key key = new SecretKeySpec("123456".getBytes(), "AES");

// 危险：会话固定
HttpSession session = request.getSession();
session.setAttribute("user", userInput); // 未重新生成 session ID
```

**审计重点**：
- 搜索 `Algorithm.none()` JWT 配置
- 检查 JWT secret key 强度
- 检查 session 管理是否调用 `session.invalidate()` 重新创建
- 检查是否使用 `HttpOnly`, `Secure` cookie 标志

### 9. XXE（XML 外部实体）

**危险模式**：
```java
// 危险：DocumentBuilder 启用 DTD
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true); // 安全

DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(inputStream);

// SAXParser 同样危险
SAXParserFactory spf = SAXParserFactory.newInstance();
```

**审计重点**：
- 搜索 `DocumentBuilder`, `SAXParser`, `XMLStreamReader`
- 检查是否设置 `DISALLOW_DOCTYPE_DECL` 或 `XMLConstants.ACCESS_EXTERNAL_DTD`
- 搜索 `TransformerFactory` 处理用户上传的 XML/XSL

---

## 模块划分建议

**Spring Boot 项目**：

| 模块 | 路径 | 审计重点 |
|------|------|----------|
| Controller | `src/main/java/.../controller/` | 认证、授权、输入验证 |
| Service | `src/main/java/.../service/` | 业务逻辑、事务 |
| Repository | `src/main/java/.../repository/` | SQL 注入、ORM |
| Config | `src/main/java/.../config/` | 安全配置、CORS |
| Filter | `src/main/java/.../filter/` | 认证过滤器、CSRF |
| Entity | `src/main/java/.../entity/` | 批量赋值、序列化 |
| Mapper | `resources/mapper/` | MyBatis XML SQL |
| 资源 | `src/main/resources/` | 配置泄露 |

**Shiro 项目**：

| 模块 | 路径 | 审计重点 |
|------|------|----------|
| Filter | `shiroFilter` 配置 | 认证绕过 (CVE-2020-1957) |
| Realm | `*Realm.java` | 凭证验证逻辑 |
| Session | Session 管理 | 会话固定 |
| 加密 | 加密配置 | 弱加密算法 |

**Struts2 项目**：

| 模块 | 路径 | 审计重点 |
|------|------|----------|
| Action | `*Action.java`, `*-action.xml` | 参数绑定、OGNL 注入 |
| Interceptor | `interceptor/` | 认证、验证 |
| Result | `result/` | 路径遍历 |

---

## 漏洞利用链示例

### SQL注入 → 数据泄露

```
用户输入 → @Query拼接 → JDBC执行 → 数据库泄露
```

```java
// 漏洞代码
@Query("SELECT * FROM User WHERE name = '" + name + "'")
// 攻击: name=' OR '1'='1
// 结果: SELECT * FROM User WHERE name='' OR '1'='1'
```

### 反序列化 → RCE

```
用户输入 → ObjectInputStream.readObject() → RCE
```

```java
// 漏洞代码
ObjectInputStream ois = new ObjectInputStream(inputStream);
ois.readObject();
// 攻击: 使用 ysoserial 生成恶意序列化对象
```

### SpEL注入 → RCE

```
用户输入 → SpelExpressionParser.parseExpression() → RCE
```

```java
// 漏洞代码
SpelExpressionParser parser = new SpelExpressionParser();
parser.parseExpression(userInput);
// 攻击: T(java.lang.Runtime).getRuntime().exec('calc')
```

### SSRF → 内网探测

```
用户输入 → new URL() → openConnection() → 内网探测
```

```java
// 漏洞代码
URL url = new URL(userInputUrl);
HttpURLConnection conn = (HttpURLConnection) url.openConnection();
// 攻击: userInputUrl=http://169.254.169.254/metadata
// 读取云服务元数据
```

---

## CVE 常见模式

| 类型 | Java 相关 CVE | 说明 |
|------|-------------|------|
| RCE | CVE-2022-22965 (Spring4Shell) | Spring Framework RCE |
| Auth Bypass | CVE-2020-1957 (Shiro) | 绕过认证 |
| SQLi | CVE-2020-29651 (MyBatis) | 动态 SQL 注入 |
| XXE | CVE-2021-21341 (Jackson) | JSON/XXE |
| Deser | CVE-2017-17485 (Jackson) | 反序列化 RCE |
| SSRF | CVE-2020-5408 (Spring Cloud) | 服务端请求伪造 |

---

## 下一步

1. 在 `workspace/00-work-background.md` 记录 Java 版本、框架、关键依赖
2. 在 `workspace/01-module-map.md` 划分模块
3. 为每个模块创建子 Agent 工作区，使用本参考作为审计指南
4. 发现漏洞后，追踪 Source → Sink 完整调用链
5. 特别关注 `pom.xml`/`build.gradle` 中的漏洞依赖版本
