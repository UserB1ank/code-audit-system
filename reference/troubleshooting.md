# 代码审计系统故障排除指南

## 常见问题速查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 403 Forbidden | Apache 文档根目录错误 | 配置 DocumentRoot 到 public/ |
| Permission denied | Web 用户无写权限 | 设置 user: "33:33" + chown/chmod |
| 数据库连接失败 | 网络配置错误 | 使用服务名连接 (db:3306) |
| POC 无法执行 | 镜像拉取失败 | 宿主机直接执行或检查网络 |

---

## 问题 1: 403 Forbidden

### 症状

```bash
curl http://localhost:8084
# 返回 403 Forbidden
```

### 原因

Apache 文档根目录配置错误，默认指向 `/var/www/html` 但项目入口在 `public/` 子目录。

### 解决方案

在 Dockerfile 中添加 Apache 配置：

```dockerfile
RUN echo '<VirtualHost *:80>' > /etc/apache2/sites-available/000-default.conf \
    && echo '    DocumentRoot /var/www/html/public' >> /etc/apache2/sites-available/000-default.conf \
    && echo '    <Directory /var/www/html/public>' >> /etc/apache2/sites-available/000-default.conf \
    && echo '        Options -Indexes +FollowSymLinks' >> /etc/apache2/sites-available/000-default.conf \
    && echo '        AllowOverride All' >> /etc/apache2/sites-available/000-default.conf \
    && echo '        Require all granted' >> /etc/apache2/sites-available/000-default.conf \
    && echo '    </Directory>' >> /etc/apache2/sites-available/000-default.conf \
    && echo '</VirtualHost>' >> /etc/apache2/sites-available/000-default.conf
```

### 验证

```bash
docker-compose restart web
curl http://localhost:8084/install.php  # 应显示安装页面
```

---

## 问题 2: Permission denied (权限拒绝)

### 症状

```bash
# Web 页面报错
"Unable to write to runtime directory"
"Permission denied: /var/www/html/runtime/log"

# 或手动测试失败
docker-compose exec -u www-data web touch /var/www/html/runtime/test.txt
# touch: cannot touch: Permission denied
```

### 原因

1. **Volume 挂载问题**: 宿主机目录挂载到容器后，文件所有者是宿主机用户 (UID 1000)，不是容器内的 www-data (UID 33)
2. **Dockerfile 权限设置在 Volume 挂载后无效**: 因为 Volume 内容会覆盖容器内的目录

### 解决方案

#### 方案 A: docker-compose.yml 中设置 (推荐)

```yaml
services:
  web:
    build: .
    user: "33:33"  # 以 www-data 用户运行
    command: >
      sh -c "chown -R 33:33 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads 2>/dev/null;
             chmod -R 775 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads 2>/dev/null;
             apache2-foreground"
```

#### 方案 B: 手动设置 (临时)

```bash
# 容器运行后手动设置
docker-compose exec web chown -R 33:33 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads
docker-compose exec web chmod -R 775 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads
```

### 验证

```bash
# 测试所有目录的写入权限
docker-compose exec -u www-data web touch /var/www/html/.env
docker-compose exec -u www-data web touch /var/www/html/runtime/test.txt
docker-compose exec -u www-data web touch /var/www/html/app/install/test.txt
docker-compose exec -u www-data web touch /var/www/html/public/uploads/test.txt

# 查看权限
docker-compose exec web ls -la /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads
```

预期输出：
```
-rwxrwxr-x  www-data www-data  .env
drwxrwxr-x  www-data www-data  runtime/
drwxrwxr-x  www-data www-data  app/install/
drwxrwxr-x  www-data www-data  public/uploads/
```

---

## 问题 3: 数据库连接失败

### 症状

```
SQLSTATE[HY000] [2002] Connection refused
```

### 原因

1. 数据库容器未启动
2. 连接地址错误 (使用 localhost 而非服务名)
3. 网络配置问题

### 解决方案

1. **检查容器状态**:
```bash
docker-compose ps
```

2. **使用正确的连接地址**:
```php
// ✅ 正确 - 使用 Docker 服务名
$host = 'db';  // 或 docker-db-1

// ❌ 错误 - localhost 在容器内指当前容器
$host = 'localhost';
```

3. **确保在同一网络**:
```yaml
services:
  web:
    networks:
      - hkcms_net
  db:
    networks:
      - hkcms_net
```

### 验证

```bash
# 从 Web 容器 ping 数据库
docker-compose exec web ping -c 3 db

# 测试 MySQL 连接
docker-compose exec web mysql -h db -P 3306 -u hkcms -p
```

---

## 问题 4: POC Runner 镜像无法拉取

### 症状

```
failed to resolve reference "docker.io/library/python:3.10-slim"
dial tcp: lookup registry-1.docker.io: no such host
```

### 原因

网络问题导致无法访问 Docker Hub。

### 解决方案

#### 方案 A: 宿主机直接执行 POC (推荐)

```bash
cd <project>/pocs

# 直接运行 POC 脚本
python 001_sql_injection_basedao.py --target http://localhost:8084 --check
```

#### 方案 B: 使用国内镜像源

```bash
# 配置 Docker 使用国内镜像加速器
# /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.cn-hangzhou.aliyuncs.com"
  ]
}
```

#### 方案 C: 暂时注释 POC Runner

```yaml
# docker-compose.yml
# poc-runner:
#   image: python:3.10-slim
#   ...
```

---

## 问题 5: 容器启动后立即退出

### 症状

```bash
docker-compose ps
# web 容器状态为 Exit 1
```

### 原因

1. Apache 配置错误
2. 端口被占用
3. 权限问题导致无法启动

### 解决方案

```bash
# 查看日志
docker-compose logs web

# 常见错误及解决:
# - "Address already in use": 修改 ports 映射
# - "Permission denied": 检查权限设置
# - "Invalid command": 检查 Apache 配置
```

---

## 问题 6: 项目克隆失败

### 症状

```
fatal: unable to access 'https://gitee.com/xxx/xxx.git': Could not resolve host
```

### 原因

网络连接问题或 Git 仓库地址错误。

### 解决方案

1. **检查网络**:
```bash
ping gitee.com
ping github.com
```

2. **验证仓库地址**:
```bash
# 在浏览器中打开仓库地址确认存在
```

3. **使用替代协议**:
```bash
# HTTPS 失败时尝试 SSH (需配置 SSH key)
git clone git@gitee.com:xxx/xxx.git
```

---

## 诊断命令集合

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看容器日志
docker-compose logs -f web
docker-compose logs -f db

# 3. 进入容器调试
docker-compose exec web bash
docker-compose exec db bash

# 4. 测试网络连接
docker-compose exec web ping -c 3 db
docker-compose exec web curl -I http://localhost:80

# 5. 检查权限
docker-compose exec web ls -la /var/www/html/
docker-compose exec web id

# 6. 测试数据库连接
docker-compose exec web mysql -h db -u hkcms -p -e "SELECT 1"

# 7. 重启服务
docker-compose restart web
docker-compose down && docker-compose up -d

# 8. 重建镜像
docker-compose build --no-cache web
```

---

## HkCms 特定问题

### 安装页面空白

**原因**: PHP 错误或权限问题

**解决**:
```bash
# 查看 PHP 错误日志
docker-compose exec web tail -f /var/www/html/runtime/log/error.log

# 检查权限
docker-compose exec web ls -la /var/www/html/runtime/
```

### 安装完成后 500 错误

**原因**: .env 配置文件权限问题

**解决**:
```bash
docker-compose exec web chown 33:33 /var/www/html/.env
docker-compose exec web chmod 664 /var/www/html/.env
```

---

## 获取帮助

如遇到未列出的问题，请提供：

1. `docker-compose ps` 输出
2. `docker-compose logs web` 最后 50 行
3. 问题复现步骤
4. 相关错误信息
