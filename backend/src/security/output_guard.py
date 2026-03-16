"""Output Guard - 输出内容审查

This module scans AI-generated and user-generated content before displaying
to users, redacting sensitive information and detecting potential leaks.

Security Layer: Output Validation
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RedactionResult:
    """审查结果"""
    original: str
    redacted: str
    redacted_count: int
    redaction_types: List[str]


class OutputGuard:
    """
    输出内容审查器

    功能:
    1. 敏感信息脱敏 (API Keys, 密码，手机号等)
    2. 检测潜在信息泄露
    3. 审查 AI 生成内容
    """

    # 敏感信息模式 (pattern, replacement, type_name)
    SENSITIVE_PATTERNS = [
        # API Keys 和 Tokens
        (
            r'\b(sk_|pk_|api[_-]?key|token_)[a-zA-Z0-9_-]{20,}\b',
            '[API_KEY_REDACTED]',
            'api_key'
        ),
        (
            r'\b[a-fA-F0-9]{32,}\b',
            '[HEX_TOKEN_REDACTED]',
            'hex_token'
        ),

        # 密码类
        (
            r'(?i)(password|passwd|pwd|secret)\s*[:=]\s*["\']?[^\s"\']{4,}',
            r'\1=[PASSWORD_REDACTED]',
            'password'
        ),

        # 手机号 (中国)
        (
            r'\b1[3-9]\d{9}\b',
            '[PHONE_REDACTED]',
            'phone'
        ),

        # 邮箱
        (
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            'email'
        ),

        # IP 地址
        (
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            '[IP_REDACTED]',
            'ip_address'
        ),

        # 身份证号
        (
            r'\b\d{17}[\dXx]|\b\d{15}\b',
            '[ID_CARD_REDACTED]',
            'id_card'
        ),

        # 银行卡号
        (
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            '[CARD_NUMBER_REDACTED]',
            'card_number'
        ),

        # JWT Token
        (
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            '[JWT_REDACTED]',
            'jwt'
        ),

        # 数据库连接字符串
        (
            r'(mysql|postgres|mongodb|redis)://[^\s"\']+',
            '[DB_CONNECTION_REDACTED]',
            'database'
        ),

        # AWS Keys
        (
            r'\b(AKIA|ABIA|ACCA)[A-Z0-9]{12,}\b',
            '[AWS_KEY_REDACTED]',
            'aws_key'
        ),
    ]

    # 需要告警但不脱敏的模式 (用于检测潜在泄露)
    ALERT_PATTERNS = [
        (r'(?i)internal\s*(config|setting|key|secret)', 'internal_resource'),
        (r'(?i)private\s*(key|info|data)', 'private_resource'),
        (r'(?i)confidential', 'confidential'),
        (r'(?i)do\s*not\s*share', 'restricted'),
    ]

    def __init__(self, strict_mode: bool = False):
        """
        初始化审查器

        Args:
            strict_mode: 严格模式下，更多类型的内容会被脱敏
        """
        self.strict_mode = strict_mode
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self.compiled_sensitive = [
            (re.compile(pattern, re.IGNORECASE if 'password' not in type_name else 0), replacement, type_name)
            for pattern, replacement, type_name in self.SENSITIVE_PATTERNS
        ]
        self.compiled_alert = [
            (re.compile(pattern, re.IGNORECASE), type_name)
            for pattern, type_name in self.ALERT_PATTERNS
        ]

    def redact(self, content: str) -> RedactionResult:
        """
        审查并脱敏敏感信息

        Args:
            content: 待审查内容

        Returns:
            RedactionResult: 包含原文、脱敏后文本、脱敏数量和类型
        """
        redacted = content
        redaction_types = []

        for pattern, replacement, type_name in self.compiled_sensitive:
            matches = pattern.findall(redacted)
            if matches:
                redacted = pattern.sub(replacement, redacted)
                if type_name not in redaction_types:
                    redaction_types.append(type_name)

        return RedactionResult(
            original=content,
            redacted=redacted,
            redacted_count=len(redaction_types),
            redaction_types=redaction_types
        )

    def get_alerts(self, content: str) -> List[str]:
        """
        获取需要告警的模式

        Args:
            content: 待检查内容

        Returns:
            告警类型列表
        """
        alerts = []
        for pattern, type_name in self.compiled_alert:
            if pattern.search(content):
                alerts.append(type_name)
        return alerts

    def scan_for_agent_leakage(
        self,
        content: str,
        current_agent_id: str,
        accessible_agent_ids: List[str]
    ) -> List[str]:
        """
        扫描是否有泄露其他 Agent 信息

        Args:
            content: 待检查内容
            current_agent_id: 当前 Agent ID
            accessible_agent_ids: 可访问的 Agent ID 列表

        Returns:
            泄露的 Agent ID 列表
        """
        leaked_agents = []

        # 检查是否有其他 Agent 的 ID 出现在内容中
        for agent_id in accessible_agent_ids:
            if agent_id != current_agent_id and agent_id in content:
                leaked_agents.append(agent_id)

        return leaked_agents

    def redact_for_agent(
        self,
        content: str,
        target_agent_id: str,
        accessible_agent_ids: List[str]
    ) -> RedactionResult:
        """
        为特定 Agent 审查内容

        Args:
            content: 待审查内容
            target_agent_id: 目标 Agent ID
            accessible_agent_ids: 目标 Agent 可访问的 ID 列表

        Returns:
            RedactionResult: 审查结果
        """
        # 首先进行常规脱敏
        result = self.redact(content)

        # 检查并移除无权访问的 Agent ID
        for agent_id in result.redacted.split():
            if len(agent_id) > 8 and agent_id.startswith(('agent_', 'key_', 'job_')):
                if agent_id not in accessible_agent_ids:
                    result.redacted = result.redacted.replace(
                        agent_id,
                        '[UNAUTHORIZED_REDACTED]'
                    )
                    if 'unauthorized_access' not in result.redaction_types:
                        result.redaction_types.append('unauthorized_access')

        return result


# 全局单例
_default_guard = OutputGuard(strict_mode=False)
_strict_guard = OutputGuard(strict_mode=True)


def get_output_guard(strict: bool = False) -> OutputGuard:
    """获取 OutputGuard 实例"""
    return _strict_guard if strict else _default_guard


def redact_sensitive(content: str) -> str:
    """便捷函数：脱敏敏感信息"""
    return _default_guard.redact(content).redacted


def scan_content(content: str) -> dict:
    """
    便捷函数：全面扫描内容

    Returns:
        包含 redacted_content, alerts, leaked_agents 的字典
    """
    result = _default_guard.redact(content)
    alerts = _default_guard.get_alerts(content)

    return {
        'redacted_content': result.redacted,
        'alerts': alerts,
        'redaction_types': result.redaction_types,
        'redaction_count': result.redacted_count
    }
