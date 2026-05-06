# 运维机制：自动提醒、错误处理与输出交付

> 本文档包含审计系统的运维机制：自动提醒、错误处理和输出交付。从 SKILL.md 中提取。

---

## Auto-Reminder Mechanism (自动提醒机制)

**触发条件**: 审计完成后，用户未指示下一步操作

### Reminder Schedule

| 时间点 | 行为 |
|--------|------|
| 完成时 | 显示审计结果 + 下一步建议选项 |
| +1 小时 | 询问是否需要继续 (POC 开发/CVE 提交) |
| +2 小时 | 再次提醒 + 强调 Critical 漏洞风险 |
| +3 小时 | 最后提醒 + 建议暂停/归档项目 |

### Reminder Message Template

```markdown
**审计完成时间**: {completion_time}
**发现漏洞**: {total_vulns} 个 (Critical: {critical_count})

待执行操作:
1. 生成综合 CVE 提交报告
2. 开发 Top 5 POC 验证脚本
3. 联系官方
4. 提交 CVE 编号 (MITRE/CNVD)

需要我执行哪项操作？
```

### Implementation

**主 Agent 职责**:
1. 审计完成后记录完成时间到 `state/audit-state.json`
2. 设置提醒标记 `reminder_pending: true`
3. 每次用户消息到达时检查是否超过 1 小时
4. 如超时而用户无新指令，发送提醒消息

**状态追踪**:
```json
{
  "reminder": {
    "enabled": true,
    "interval_hours": 1,
    "max_reminders": 3,
    "sent_count": 0,
    "last_reminder": null,
    "next_reminder": "2026-04-05T14:00:00+08:00"
  }
}
```

**取消条件**:
- 用户明确指示下一步操作
- 用户要求停止/暂停
- 达到最大提醒次数 (3 次)

---

## 错误处理

- **克隆失败**: 报告给用户，跳过该仓库
- **子 Agent 超时**: 重试一次，然后标记为未完成 (专注其他模块)
- **Docker 失败**: 回退到静态分析 + POC (无验证)
- **POC 执行错误**: 记录输出，标记验证为失败 (仍在提交中包含 POC)
- **CVE 被拒**: 分析原因并调整发现策略

---

## 输出交付

向用户展示:

1. **CVE 提交报告** (主要交付物)
   - 仅包含 CVE 级别漏洞
   - 武器化 POC
   - CVSS 评分
   - 提交就绪格式

2. **独立漏洞报告** (详细技术分析)

3. **武器化 POC 脚本** (可用于演示)

4. **(可选) 验证结果** (如使用 Docker 环境)

5. **CVE 提交指南**:
   - 推荐的 CNA 提交渠道
   - 协调披露时间线
   - 厂商联系模板
