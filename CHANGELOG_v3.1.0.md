# Code Audit System 更新日志 - v3.1.0

## 📅 更新日期
2026-03-31

---

## ✨ 新增功能

### 1. 命令行直接审计入口

**新增文件**: `scripts/code-audit.sh`

现在可以在项目目录中直接使用 `/skill code-audit` 命令触发代码审计，无需通过飞书 Bot。

**使用示例**:
```bash
# 基础审计
/skill code-audit

# 深度审计（包含调用链分析）
/skill code-audit -d

# 指定 Qwen 模型
/skill code-audit -m qwen3-coder-plus

# YOLO 模式（自动确认）
/skill code-audit -y

# 审计指定项目
/skill code-audit /path/to/project

# 审计 Git 仓库
/skill code-audit https://github.com/OWASP/juice-shop.git
```

### 2. 支持的命令选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-h, --help` | 显示帮助信息 | - |
| `-v, --version` | 显示版本号 | - |
| `-q, --quick` | 快速审计（静态分析） | 是 |
| `-d, --deep` | 深度审计（调用链分析） | 否 |
| `-m, --model` | 指定 Qwen 模型 | qwen3.5-plus |
| `-y, --yolo` | 自动确认所有提示 | 否 |
| `-o, --output` | 指定报告输出目录 | 默认工作区 |

### 3. 审计流程自动化

命令行模式自动执行以下流程：

1. ✅ 检查 Qwen CLI 安装和认证状态
2. ✅ 初始化审计环境（创建目录结构）
3. ✅ 克隆 Git 仓库或复制本地项目
4. ✅ 调用 Qwen 进行代码审计
5. ✅ 生成审计报告 (`reports/audit_report.md`)
6. ✅ (可选) 创建 POC 脚本 (`pocs/*.py`)
7. ✅ 输出完整报告路径

---

## 📝 文档更新

### 1. SKILL.md 更新

- 添加命令行快速开始指南
- 添加命令行脚本说明表格
- 区分命令行模式和飞书 Bot 模式的核心功能
- 添加两种模式的工作流程图
- 添加命令行使用示例
- 更新版本号至 3.1.0

### 2. 新增 scripts/README.md

完整的命令行工具使用文档，包含：
- 前置要求和安装指南
- 详细的使用方法和示例
- 命令选项说明
- 输出结构说明
- 审计报告格式示例
- POC 脚本示例
- 任务追踪命令
- 故障排除指南

### 3. 更新 _meta.json

- 版本号：3.0.0 → 3.1.0
- 更新说明：`feat: Add CLI entry /skill code-audit for direct project audit`

---

## 🔄 两种调用方式对比

### 命令行模式（新增）

**适用场景**:
- 快速审计单个项目
- 本地开发环境
- 不需要 Docker 环境部署
- 不需要漏洞验证

**优势**:
- 简单直接，一条命令启动
- 无需飞书 Bot 配置
- 支持多种 Qwen 模型选择
- YOLO 模式完全自动化

**限制**:
- 无 Docker 环境部署
- 无漏洞验证环节
- 无飞书通知推送

### 飞书 Bot 模式（原有）

**适用场景**:
- 企业级审计流程
- 需要完整审计 + 验证流程
- 需要 Docker 隔离环境
- 需要团队协作和通知

**优势**:
- 完整的审计 → POC → 验证流程
- Docker 隔离环境部署
- 飞书通知和报告推送
- 任务状态追踪和断点续传

**限制**:
- 需要飞书 Bot 配置
- 流程相对复杂
- 需要用户确认环节

---

## 🎯 使用建议

### 快速审计（推荐命令行模式）

```bash
# 发现漏洞 → 生成报告
/skill code-audit -q /path/to/project
```

### 深度审计（推荐命令行模式）

```bash
# 完整调用链分析 → 生成详细报告
/skill code-audit -d -m qwen3-coder-plus /path/to/project
```

### 企业级审计（推荐飞书 Bot 模式）

```bash
# 飞书命令
/audit add https://github.com/target/project.git
# 自动执行：审计 → 部署 → POC → 验证 → 报告
```

---

## 📦 文件变更清单

### 新增文件
- `scripts/code-audit.sh` - 命令行审计入口脚本（7091 字节）
- `scripts/README.md` - 命令行工具使用文档（3723 字节）

### 修改文件
- `SKILL.md` - 添加命令行支持说明
- `_meta.json` - 版本更新至 3.1.0

---

## 🔧 技术实现

### Qwen 集成

脚本通过 Qwen Code CLI 调用 Qwen LLM：

```bash
qwen -m <model> -p "<prompt>" [-y]
```

**审计提示词包含**:
- 只报告可实际利用的漏洞
- 拒绝理论漏洞和潜在漏洞
- 完整调用链追踪
- 可执行的修复建议
- CVSS 评分

### 目录结构

审计完成后生成：

```
~/.openclaw/workspace-cybersecurity_expert/code-audit-system/<project>/
├── source/          # 源码
├── reports/         # 审计报告
├── pocs/            # POC 脚本
└── state/           # 任务状态（全局）
```

### 状态追踪

审计任务自动记录到：
- `state/task-state.json` - 当前状态快照
- `state/task-history.jsonl` - 事件历史

---

## ⚠️ 注意事项

### 前置要求

1. **Qwen Code CLI 必须安装**
   ```bash
   npm install -g @qwen-code/qwen-code@latest
   ```

2. **Qwen 必须认证**
   ```bash
   qwen auth login
   # 或
   export DASHSCOPE_API_KEY="sk-xxx"
   ```

### 安全提示

1. 仅对授权项目进行审计
2. POC 脚本应在 Docker 沙箱中执行
3. 不要泄露审计报告和 POC 给未授权方

---

## 🚀 下一步计划

- [ ] 添加审计报告自动生成 CVE 提交草稿
- [ ] 支持多项目并行审计
- [ ] 添加审计结果对比功能
- [ ] 集成 DeepAudit 系统

---

**版本**: 3.1.0  
**作者**: SecAudit  
**更新日期**: 2026-03-31
