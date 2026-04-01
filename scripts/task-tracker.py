#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务状态追踪器 - Task Tracker for Code Audit System

功能:
- 记录任务执行历史
- 查询当前任务状态
- 生成执行统计报告
- 支持断点续传

使用:
    python task-tracker.py status      # 查看当前状态
    python task-tracker.py history     # 查看历史记录
    python task-tracker.py stats       # 生成统计报告
    python task-tracker.py resume      # 恢复未完成的任务
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 配置
STATE_DIR = Path(__file__).parent.parent / "state"
STATE_FILE = STATE_DIR / "task-state.json"
HISTORY_FILE = STATE_DIR / "task-history.jsonl"

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def load_state():
    """加载当前状态"""
    if not STATE_FILE.exists():
        return None
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_history(limit=20):
    """加载历史记录"""
    if not HISTORY_FILE.exists():
        return []
    
    history = []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                history.append(json.loads(line))
    
    return history[-limit:]

def show_status():
    """显示当前状态"""
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}代码审计系统 - 任务状态{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    state = load_state()
    if not state:
        print(f"{Colors.YELLOW}暂无状态信息{Colors.END}")
        return
    
    # 活跃项目
    active = state.get('active_projects', [])
    print(f"{Colors.BLUE}活跃项目：{len(active)}{Colors.END}")
    for proj in active:
        status_icon = "✅" if proj['status'] == 'completed' else "🔄"
        print(f"  {status_icon} #{proj['project_id']} {proj['name']} - {proj['status']}")
        if 'vulnerabilities' in proj:
            vuln = proj['vulnerabilities']
            print(f"      漏洞：{vuln.get('total', 0)} (C:{vuln.get('critical',0)} H:{vuln.get('high',0)} M:{vuln.get('medium',0)} L:{vuln.get('low',0)})")
    
    # 子 Agent 池
    print(f"\n{Colors.BLUE}子 Agent 池{Colors.END}")
    pool = state.get('subagent_pool', {})
    print(f"  可用：{len(pool.get('available', []))}")
    print(f"  活跃：{len(pool.get('active', []))}")
    
    # 最近执行
    recent = pool.get('recent', [])
    if recent:
        print(f"\n{Colors.BLUE}最近执行 ({len(recent)} 个){Colors.END}")
        for task in recent[-5:]:
            icon = "✅" if task['status'] == 'completed' else "❌"
            duration = task.get('duration_seconds', 0)
            print(f"  {icon} {task['agent']}: {task['task']} ({duration}s)")
    
    # 当前任务
    current = state.get('current_task')
    if current:
        print(f"\n{Colors.YELLOW}当前任务：{current.get('task_id', 'N/A')}{Colors.END}")
    else:
        print(f"\n{Colors.GREEN}当前无执行中任务{Colors.END}")
    
    # 最后完成
    last = state.get('last_completed_task')
    if last:
        print(f"\n{Colors.GREEN}最后完成：{last['task_id']} ({last['completed_at']}){Colors.END}")
        if 'summary' in last:
            s = last['summary']
            print(f"  漏洞：{s.get('vulnerabilities_found', 0)} | POC: {s.get('pocs_created', 0)} | 验证：{s.get('vulnerabilities_verified', 0)}")

def show_history(limit=20):
    """显示历史记录"""
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}任务历史记录 (最近 {limit} 条){Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    history = load_history(limit)
    
    for event in reversed(history):
        ts = event.get('timestamp', 'Unknown')
        event_type = event.get('event', 'unknown')
        
        # 事件图标
        icons = {
            'project_added': '📁',
            'task_started': '🚀',
            'task_completed': '✅',
            'task_failed': '❌',
            'environment_deployed': '🐳',
            'project_completed': '🎉'
        }
        icon = icons.get(event_type, '📌')
        
        # 格式化输出
        task_id = event.get('task_id', event.get('project_id', ''))
        agent = event.get('agent', '')
        duration = event.get('duration_seconds', 0)
        
        line = f"{icon} [{ts}] {event_type}"
        if task_id:
            line += f" - {task_id}"
        if agent:
            line += f" ({agent})"
        if duration:
            line += f" [{duration}s]"
        
        # 结果信息
        if 'result' in event:
            result = event['result']
            if 'vulnerabilities' in result:
                line += f" → {result['vulnerabilities']} 个漏洞"
            if 'pocs_created' in result:
                line += f" → {result['pocs_created']} 个 POC"
        
        print(line)

def show_stats():
    """生成统计报告"""
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}执行统计报告{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    history = load_history(limit=1000)
    
    # 统计事件类型
    event_counts = {}
    total_duration = 0
    tasks_completed = 0
    tasks_failed = 0
    
    for event in history:
        event_type = event.get('event', 'unknown')
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        if event_type == 'task_completed':
            tasks_completed += 1
            total_duration += event.get('duration_seconds', 0)
        elif event_type == 'task_failed':
            tasks_failed += 1
    
    # 项目统计
    state = load_state()
    total_vulns = 0
    total_pocs = 0
    
    for proj in state.get('active_projects', []):
        if 'vulnerabilities' in proj:
            total_vulns += proj['vulnerabilities'].get('total', 0)
        total_pocs += len(proj.get('pocs', []))
    
    print(f"{Colors.BLUE}项目统计{Colors.END}")
    print(f"  总项目数：{len(state.get('active_projects', []))}")
    print(f"  总漏洞数：{total_vulns}")
    print(f"  总 POC 数：{total_pocs}")
    
    print(f"\n{Colors.BLUE}任务执行{Colors.END}")
    print(f"  完成任务：{tasks_completed}")
    print(f"  失败任务：{tasks_failed}")
    print(f"  成功率：{tasks_completed/(tasks_completed+tasks_failed)*100:.1f}% (如有数据)")
    print(f"  总耗时：{total_duration/60:.1f} 分钟")
    
    print(f"\n{Colors.BLUE}事件分布{Colors.END}")
    for event_type, count in sorted(event_counts.items(), key=lambda x: -x[1]):
        print(f"  {event_type}: {count}")

def resume_task():
    """恢复未完成的任务"""
    print(f"{Colors.YELLOW}检查未完成的任务...{Colors.END}\n")
    
    state = load_state()
    if not state:
        print(f"{Colors.GREEN}无需要恢复的任务{Colors.END}")
        return
    
    # 查找运行中的任务
    for proj in state.get('active_projects', []):
        if proj['status'] == 'running':
            print(f"{Colors.YELLOW}发现运行中项目：#{proj['project_id']} {proj['name']}{Colors.END}")
            print(f"  状态：{proj['status']}")
            print(f"  创建时间：{proj['created_at']}")
            
            # 可以添加恢复逻辑
            print(f"\n{Colors.CYAN}提示：可以手动恢复此项目的执行{Colors.END}")
    
    print(f"\n{Colors.GREEN}检查完成{Colors.END}")

def print_help():
    """打印帮助信息"""
    print(f"""
{Colors.CYAN}代码审计系统 - 任务追踪器{Colors.END}

用法：python task-tracker.py <命令>

命令:
  status    查看当前任务状态
  history   查看最近历史记录 (默认 20 条)
  stats     生成统计报告
  resume    恢复未完成的任务
  help      显示此帮助信息

示例:
  python task-tracker.py status
  python task-tracker.py history 50
  python task-tracker.py stats
""")

def main():
    import sys
    
    if len(sys.argv) < 2:
        show_status()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_status()
    elif command == 'history':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_history(limit)
    elif command == 'stats':
        show_stats()
    elif command == 'resume':
        resume_task()
    elif command == 'help' or command == '--help':
        print_help()
    else:
        print(f"{Colors.RED}未知命令：{command}{Colors.END}")
        print_help()

if __name__ == "__main__":
    main()
