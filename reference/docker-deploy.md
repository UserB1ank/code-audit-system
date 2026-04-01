# Docker 环境部署指南

## 概述

代码审计系统使用 Docker 隔离环境进行：
1. 目标项目部署
2. POC 沙箱执行

## 依赖技能

- **docker-essentials** (主要): Docker 容器管理
- **docker-sandbox**: 沙箱环境执行 POC

## ⚠️ 关键注意事项：Web 目录权限

### 常见问题

PHP 项目 (如 ThinkPHP、Laravel) 需要 Web 用户对特定目录有**读写权限**，否则会导致：
- ❌ 无法生成日志文件
- ❌ 无法写入缓存
- ❌ 无法上传文件
- ❌ 安装程序失败

### 必须设置权限的目录

| 目录 | 用途 | 权限要求 |
|------|------|---------|
| `.env` | 环境配置文件 | 可写 |
| `runtime/` | 运行时日志、缓存 | 可写 |
| `app/install/` | 安装程序数据 | 可写 |
| `public/uploads/` | 用户上传文件 | 可写 |

### 权限设置方法

#### 方法 1: 容器启动时自动设置 (推荐)

在 `docker-compose.yml` 中添加：

```yaml
services:
  web:
    build: .
    user: "33:33"  # www-data 用户 UID:GID
    command: >
      sh -c "chown -R 33:33 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads 2>/dev/null;
             chmod -R 775 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads 2>/dev/null;
             apache2-foreground"
```

#### 方法 2: Dockerfile 中设置

```dockerfile
# 创建必要目录
RUN mkdir -p /var/www/html/runtime/log \
    /var/www/html/runtime/temp \
    /var/www/html/runtime/cache \
    /var/www/html/public/uploads \
    && chown -R 33:33 /var/www/html/runtime \
    && chown -R 33:33 /var/www/html/public/uploads \
    && chmod -R 775 /var/www/html/runtime \
    && chmod -R 775 /var/www/html/public/uploads
```

#### 方法 3: 手动设置 (容器运行后)

```bash
docker-compose exec web chown -R 33:33 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads
docker-compose exec web chmod -R 775 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads
```

### 权限验证

```bash
# 测试写入权限
docker-compose exec -u www-data web touch /var/www/html/runtime/test.txt
docker-compose exec -u www-data web touch /var/www/html/.env
docker-compose exec -u www-data web touch /var/www/html/app/install/test.txt
docker-compose exec -u www-data web touch /var/www/html/public/uploads/test.txt

# 查看权限
docker-compose exec web ls -la /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads
```

预期输出：
```
drwxrwxr-x  www-data www-data  runtime/
drwxrwxr-x  www-data www-data  app/install/
drwxrwxr-x  www-data www-data  public/uploads/
-rwxrwxr-x  www-data www-data  .env
```

---

## 目录结构

```
<project>/docker/
├── Dockerfile              # 目标项目镜像
├── docker-compose.yml      # 编排配置
└── .env                    # 环境变量 (可选)
```

## Dockerfile 模板

### PHP 项目 (ThinkPHP/CMS)

```dockerfile
FROM php:8.1-apache

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libz-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 PHP 扩展
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install mysqli pdo pdo_mysql gd

# 启用 Apache 模块
RUN a2enmod rewrite

# 安装 Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# 设置工作目录
WORKDIR /var/www/html

# 复制项目代码
COPY . .

# 创建必要目录并设置权限 (UID 33 = www-data)
RUN mkdir -p /var/www/html/runtime/log \
    /var/www/html/runtime/temp \
    /var/www/html/runtime/cache \
    /var/www/html/public/uploads \
    && chown -R 33:33 /var/www/html/runtime \
    && chown -R 33:33 /var/www/html/public/uploads \
    && chmod -R 775 /var/www/html/runtime \
    && chmod -R 775 /var/www/html/public/uploads

# 配置 Apache 文档根目录 (根据项目调整)
RUN echo '<VirtualHost *:80>' > /etc/apache2/sites-available/000-default.conf \
    && echo '    DocumentRoot /var/www/html/public' >> /etc/apache2/sites-available/000-default.conf \
    && echo '    <Directory /var/www/html/public>' >> /etc/apache2/sites-available/000-default.conf \
    && echo '        Options -Indexes +FollowSymLinks' >> /etc/apache2/sites-available/000-default.conf \
    && echo '        AllowOverride All' >> /etc/apache2/sites-available/000-default.conf \
    && echo '        Require all granted' >> /etc/apache2/sites-available/000-default.conf \
    && echo '    </Directory>' >> /etc/apache2/sites-available/000-default.conf \
    && echo '</VirtualHost>' >> /etc/apache2/sites-available/000-default.conf

# 暴露端口
EXPOSE 80

CMD ["apache2-foreground"]
```

### Java 项目

```dockerfile
FROM openjdk:11-jre-slim

# 安装依赖
RUN apt-get update && apt-get install -y curl

# 复制 WAR 包
COPY target/*.war /app.war

# 暴露端口
EXPOSE 8080

CMD ["java", "-jar", "/app.war"]
```

### Node.js 项目

```dockerfile
FROM node:18-alpine

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm install --production

# 复制代码
COPY . .

# 暴露端口
EXPOSE 3000

CMD ["node", "server.js"]
```

## docker-compose.yml 模板

### 基础配置 (PHP + MySQL) - 含权限设置

```yaml
services:
  web:
    build: .
    ports:
      - "8084:80"
    volumes:
      - ../source:/var/www/html
    user: "33:33"  # 重要：以 www-data 用户运行
    command: >
      sh -c "chown -R 33:33 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads 2>/dev/null;
             chmod -R 775 /var/www/html/.env /var/www/html/runtime /var/www/html/app/install /var/www/html/public/uploads 2>/dev/null;
             apache2-foreground"
    depends_on:
      - db
    networks:
      - audit_net

  db:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: target_db
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
    networks:
      - audit_net

  adminer:
    image: adminer
    ports:
      - "8081:8080"
    depends_on:
      - db
    networks:
      - audit_net

volumes:
  db_data:

networks:
  audit_net:
    driver: bridge
```

### POC 执行沙箱

```yaml
services:
  poc-runner:
    image: python:3.10-slim
    volumes:
      - ./pocs:/pocs
      - ./reports:/reports
    working_dir: /pocs
    command: ["python", "001_sql_injection.py", "--target", "http://web:80"]
    networks:
      - audit_net
    depends_on:
      - web

  web:
    # ... 目标项目配置
```

## 部署流程

### 1. 检查项目

```bash
# 检查项目结构
ls -la <project>/source/

# 识别框架类型
cat <project>/source/composer.json  # PHP
cat <project>/source/package.json   # Node.js
```

### 2. 编写 Dockerfile

根据项目类型选择模板，保存到 `<project>/docker/Dockerfile`

**关键点**:
- ✅ 创建必要的 writable 目录
- ✅ 设置正确的 UID:GID (33:33 = www-data)
- ✅ 配置 Apache 文档根目录

### 3. 编写 docker-compose.yml

使用模板，保存到 `<project>/docker/docker-compose.yml`

**关键点**:
- ✅ 添加 `user: "33:33"`
- ✅ 添加启动时权限设置的 `command`
- ✅ 配置 volume 挂载

### 4. 构建并部署

```bash
cd <project>/docker

# 构建镜像
docker-compose build

# 启动容器
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f web
```

### 5. 验证部署

```bash
# 检查 Web 服务
curl http://localhost:8084

# 检查权限
docker-compose exec -u www-data web touch /var/www/html/runtime/test.txt && echo "权限正常"

# 检查数据库
mysql -h 127.0.0.1 -P 3306 -u root -proot123
```

## POC 执行

### 1. 准备沙箱

```bash
cd <project>/docker

# 启动沙箱执行 POC
docker-compose run poc-runner
```

### 2. 查看结果

```bash
# 查看 POC 输出
docker-compose logs poc-runner

# 查看生成的报告
cat <project>/reports/verify_report.md
```

## 清理环境

```bash
# 停止容器
docker-compose down

# 删除卷 (可选，会删除数据)
docker-compose down -v

# 删除镜像
docker-compose down --rmi all
```

## 常见问题

### Q: 403 Forbidden 错误？

A: 检查 Apache 文档根目录是否正确配置，确保指向 `public/` 目录。

### Q: 权限拒绝 (Permission denied)？

A: 确保在 docker-compose.yml 中添加了 `user: "33:33"` 和权限设置的 `command`。

### Q: 端口冲突？

A: 修改 docker-compose.yml 中的端口映射，如 `"8081:80"` 改为 `"8082:80"`

### Q: 数据库连接失败？

A: 确保容器在同一网络，使用服务名而非 localhost 连接（如 `db:3306`）。

### Q: 文件权限问题？

A: 在 Dockerfile 中设置正确的权限，并在 docker-compose.yml 中添加启动时权限设置命令。

### Q: POC Runner 镜像无法拉取？

A: 网络问题时可暂时注释 poc-runner 服务，直接在宿主机执行 POC 脚本。

## 安全提示

⚠️ **重要**: 所有 POC 执行必须在隔离的 Docker 网络中进行，禁止使用 host 网络模式。

```yaml
# ✅ 正确 - 隔离网络
networks:
  audit_net:
    driver: bridge

# ❌ 错误 - 使用宿主机网络
network_mode: host
```

⚠️ **权限注意**: 生产环境不应使用 775 权限，这里仅用于审计测试环境。
