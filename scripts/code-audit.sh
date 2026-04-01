#!/bin/bash

# Code Audit System - 命令行审计入口
# 使用方式：在项目目录中运行 /skill code-audit 或 bash code-audit.sh

set -e

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
STATE_DIR="$WORKSPACE_DIR/code-audit-system/state"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
🔒 Code Audit System v${VERSION}

用法:
  $0 [选项] [项目路径]

选项:
  -h, --help          显示帮助信息
  -v, --version       显示版本号
  -q, --quick         快速审计 (仅静态分析)
  -d, --deep          深度审计 (包含调用链分析)
  -o, --output <dir>  指定报告输出目录
  -m, --model <name>  指定 Qwen 模型 (默认：qwen3.5-plus)
  -y, --yolo          自动确认所有提示

示例:
  $0                          # 审计当前目录
  $0 /path/to/project         # 审计指定项目
  $0 -d -m qwen3-coder-plus   # 深度审计，使用 coder 模型
  $0 -q -y                    # 快速审计，自动确认

EOF
}

# 检查 Qwen 是否可用
check_qwen() {
    if ! command -v qwen &> /dev/null; then
        error "Qwen CLI 未安装"
        echo ""
        echo "请运行以下命令安装:"
        echo "  npm install -g @qwen-code/qwen-code@latest"
        echo ""
        echo "然后运行认证:"
        echo "  qwen auth login"
        exit 1
    fi
    
    # 检查认证状态
    if ! qwen auth status &> /dev/null; then
        warning "Qwen 未认证，请运行：qwen auth login"
        exit 1
    fi
    
    success "Qwen CLI 已就绪"
}

# 初始化审计环境
init_audit_env() {
    local project_path="$1"
    local project_name=$(basename "$project_path")
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    # 创建审计目录结构
    mkdir -p "$WORKSPACE_DIR/code-audit-system/$project_name/source"
    mkdir -p "$WORKSPACE_DIR/code-audit-system/$project_name/reports"
    mkdir -p "$WORKSPACE_DIR/code-audit-system/$project_name/pocs"
    
    # 初始化状态文件
    if [ ! -f "$STATE_DIR/task-state.json" ]; then
        cat > "$STATE_DIR/task-state.json" << EOF
{
  "version": "3.1",
  "projects": [],
  "last_updated": "$(date -Iseconds)"
}
EOF
    fi
    
    info "审计环境已初始化"
}

# 克隆或复制项目源码
prepare_source() {
    local project_path="$1"
    local project_name=$(basename "$project_path")
    local source_dir="$WORKSPACE_DIR/code-audit-system/$project_name/source"
    
    if [[ "$project_path" =~ ^https?:// ]]; then
        # Git 仓库
        info "从 Git 仓库克隆：$project_path"
        git clone "$project_path" "$source_dir" 2>/dev/null || {
            error "克隆失败，请检查仓库地址或认证"
            exit 1
        }
    else
        # 本地目录
        info "复制本地项目：$project_path"
        cp -r "$project_path"/* "$source_dir/" 2>/dev/null || {
            error "复制失败，请检查路径"
            exit 1
        }
    fi
    
    success "源码准备完成"
}

# 执行代码审计
run_audit() {
    local project_name="$1"
    local audit_type="$2"  # quick 或 deep
    local model="$3"
    local yolo="$4"
    
    local source_dir="$WORKSPACE_DIR/code-audit-system/$project_name/source"
    local report_dir="$WORKSPACE_DIR/code-audit-system/$project_name/reports"
    local report_file="$report_dir/audit_report.md"
    
    info "开始代码审计..."
    info "项目：$project_name"
    info "类型：$audit_type"
    info "模型：$model"
    
    # 构建审计提示词
    local prompt="你是一名专业的网络安全专家，负责对以下项目进行代码安全审计。

审计要求：
1. 只报告可实际利用的漏洞（有入口 + 无阻断 + 可 POC）
2. 拒绝理论漏洞（无用户输入入口）
3. 拒绝潜在漏洞（需要特殊条件）
4. 每个漏洞必须有完整调用链追踪
5. 提供可执行的修复建议

审计重点：
- SQL 注入
- 远程代码执行 (RCE)
- 文件上传漏洞
- 认证/授权绕过
- XSS
- 路径遍历
- 命令注入
- 反序列化漏洞
- 敏感信息泄露

报告格式：
# 漏洞审计报告

## 项目信息
- 项目名称：$project_name
- 审计时间：$(date +%Y-%m-%d)
- 审计模型：$model

## 漏洞列表

### 漏洞 1: [漏洞名称]
- **类型**: [漏洞类型]
- **认证**: [需要/不需要]
- **位置**: \`文件路径\` line [行号]
- **触发过程**: [完整调用链描述]
- **CVSS**: [评分]
- **修复建议**: [具体修复方案]

请对 $source_dir 目录进行完整审计。"

    # 执行 Qwen 审计
    cd "$source_dir"
    
    if [ "$yolo" = "true" ]; then
        info "YOLO 模式：自动确认所有提示"
        qwen -m "$model" -y -p "$prompt" > "$report_file" 2>&1 &
        local pid=$!
    else
        qwen -m "$model" -p "$prompt" > "$report_file" 2>&1 &
        local pid=$!
    fi
    
    # 等待完成
    info "审计任务运行中 (PID: $pid)..."
    wait $pid
    
    if [ $? -eq 0 ]; then
        success "审计完成！报告：$report_file"
    else
        error "审计失败，请检查报告文件"
        exit 1
    fi
    
    cd - > /dev/null
}

# 创建 POC 脚本
create_pocs() {
    local project_name="$1"
    local model="$2"
    
    local report_file="$WORKSPACE_DIR/code-audit-system/$project_name/reports/audit_report.md"
    local poc_dir="$WORKSPACE_DIR/code-audit-system/$project_name/pocs"
    
    if [ ! -f "$report_file" ]; then
        error "审计报告不存在：$report_file"
        exit 1
    fi
    
    info "开始编写 POC 脚本..."
    
    local prompt="根据以下审计报告，为每个可利用的漏洞编写 Python POC 脚本。

要求：
1. 每个漏洞一个独立的 Python 脚本
2. 脚本必须可执行、可验证
3. 包含详细的注释和使用说明
4. 使用彩色输出显示结果
5. 遵循 POC 模板格式

审计报告内容：
$(cat "$report_file")

请将 POC 脚本保存到 $poc_dir 目录。"

    qwen -m "$model" -p "$prompt"
    
    success "POC 脚本创建完成"
}

# 主函数
main() {
    local audit_type="quick"
    local model="qwen3.5-plus"
    local yolo="false"
    local project_path="."
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                echo "Code Audit System v${VERSION}"
                exit 0
                ;;
            -q|--quick)
                audit_type="quick"
                shift
                ;;
            -d|--deep)
                audit_type="deep"
                shift
                ;;
            -m|--model)
                model="$2"
                shift 2
                ;;
            -y|--yolo)
                yolo="true"
                shift
                ;;
            -*)
                error "未知选项：$1"
                show_help
                exit 1
                ;;
            *)
                project_path="$1"
                shift
                ;;
        esac
    done
    
    echo ""
    echo "🔒 Code Audit System v${VERSION}"
    echo "================================"
    echo ""
    
    # 检查 Qwen
    check_qwen
    
    # 初始化环境
    init_audit_env "$project_path"
    
    # 准备源码
    prepare_source "$project_path"
    
    # 执行审计
    local project_name=$(basename "$project_path")
    run_audit "$project_name" "$audit_type" "$model" "$yolo"
    
    # 询问是否创建 POC
    if [ "$yolo" != "true" ]; then
        echo ""
        read -p "是否创建 POC 脚本？(y/n): " create_poc
        if [[ "$create_poc" =~ ^[Yy]$ ]]; then
            create_pocs "$project_name" "$model"
        fi
    else
        info "YOLO 模式：自动创建 POC 脚本"
        create_pocs "$project_name" "$model"
    fi
    
    echo ""
    success "审计流程完成！"
    echo ""
    echo "📁 项目目录：$WORKSPACE_DIR/code-audit-system/$(basename "$project_path")"
    echo "📄 审计报告：$WORKSPACE_DIR/code-audit-system/$(basename "$project_path")/reports/audit_report.md"
    echo "🐍 POC 脚本：$WORKSPACE_DIR/code-audit-system/$(basename "$project_path")/pocs/"
    echo ""
}

# 执行主函数
main "$@"
