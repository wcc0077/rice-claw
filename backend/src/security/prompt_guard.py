"""Prompt Injection Guard - 提示注入防护

This module provides detection and sanitization for prompt injection attacks
in user-generated content including job descriptions, messages, and bid proposals.

Security Layer: Input Validation
"""

import re
from enum import Enum
from typing import Tuple, List, Optional
from dataclasses import dataclass
from loguru import logger


class ThreatLevel(Enum):
    """威胁等级"""
    SAFE = "safe"           # 安全
    SUSPICIOUS = "suspicious"  # 可疑
    DANGEROUS = "dangerous"    # 危险


@dataclass
class AnalysisResult:
    """分析结果"""
    threat_level: ThreatLevel
    detected_patterns: List[str]
    confidence: float  # 0.0 - 1.0
    sanitized_content: Optional[str] = None


class PromptGuard:
    """
    Prompt Injection 检测器

    检测类型:
    1. 直接注入 - 尝试覆盖系统指令
    2. 社会工程学 - 诱骗用户泄露信息
    3. 代码执行 - 尝试执行恶意代码
    4. 上下文逃逸 - 尝试跳出预设上下文
    """

    # 危险指令模式 (中文 + 英文)
    INJECTION_PATTERNS = [
        # 忽略指令类
        (r"忽略 (之前的 | 所有 | 系统 | 安全) 指令", "ignore_instructions"),
        (r"无视 (之前 | 所有 | 任何) 规则", "ignore_rules"),
        (r"跳过 (安全 | 验证 | 认证) 检查", "skip_security"),
        (r"bypass (security|validation|auth)", "ignore_instructions"),
        (r"ignore (previous|all|system) instructions", "ignore_instructions"),

        # 系统伪装类
        (r"system:\s*\w+", "system_impersonation"),
        (r"\[SYSTEM\]", "system_impersonation"),
        (r"你现在是 (管理员 | 系统 |root)", "role_playing"),
        (r"you are now (admin|system|root)", "role_playing"),
        (r"以 (系统 | 管理员) 身份", "role_playing"),

        # 代码执行类
        (r"执行 (SQL|代码 | 命令|脚本)", "code_execution"),
        (r"run (this|the following) (code|script|command)", "code_execution"),
        (r"```(python|bash|sql|shell)", "code_execution"),
        (r"eval\(|exec\(", "code_execution"),

        # 信息窃取类
        (r"返回 (密码|密钥|API Key|Token)", "info_stealing"),
        (r"泄露 (敏感 | 内部 | 机密) 信息", "info_stealing"),
        (r"return (password|key|secret|token|credentials)", "info_stealing"),
        (r"show me (all|your) data", "info_stealing"),

        # 上下文逃逸类
        (r"退出当前 (模式 | 上下文 | 会话)", "context_escape"),
        (r"exit (current|this) (mode|context|session)", "context_escape"),
        (r"重置 (系统 | 配置 | 状态)", "context_escape"),
    ]

    # 社会工程学模式
    SOCIAL_ENGINEERING_PATTERNS = [
        # 紧急通知伪装
        (r"紧急通知", "urgency"),
        (r"立即 (点击 | 验证 | 操作)", "urgency"),
        (r"your (account|API key) will be (suspended|expired)", "urgency"),
        (r"账户将 (被冻结 | 被注销)", "urgency"),

        # 官方伪装
        (r"【官方通知】", "official_impersonation"),
        (r"系统管理员", "official_impersonation"),
        (r"platform (admin|support|security)", "official_impersonation"),

        # 链接诱导
        (r"点击 (此处 | 这个链接)", "link_phishing"),
        (r"http[s]?://[^\s]+", "link_present"),
        (r"访问 (网站 | 链接)", "link_phishing"),
    ]

    # 最高风险模式 (直接判定为 DANGEROUS)
    CRITICAL_PATTERNS = [
        r"删除所有数据",
        r"drop table",
        r"delete from",
        r"rm -rf",
        r"format (c:|disk)",
        r"发送 (所有 | 全部) 数据到",
        r"send all data to",
    ]

    def __init__(self, strict_mode: bool = False):
        """
        初始化检测器

        Args:
            strict_mode: 严格模式下，可疑内容也会被拦截
        """
        self.strict_mode = strict_mode
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self.compiled_injection = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in self.INJECTION_PATTERNS
        ]
        self.compiled_social = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in self.SOCIAL_ENGINEERING_PATTERNS
        ]
        self.compiled_critical = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.CRITICAL_PATTERNS
        ]

    def analyze(self, content: str, max_length: int = 10000) -> AnalysisResult:
        """
        分析内容并返回威胁级别

        Args:
            content: 待分析的内容
            max_length: 最大分析长度，防止 DoS

        Returns:
            AnalysisResult: 分析结果
        """
        # 截断过长的内容
        if len(content) > max_length:
            content = content[:max_length] + "..."

        detected_patterns = []
        critical_match = False

        # 检查致命模式
        for pattern in self.compiled_critical:
            if pattern.search(content):
                critical_match = True
                detected_patterns.append(f"CRITICAL:{pattern.pattern}")

        if critical_match:
            return AnalysisResult(
                threat_level=ThreatLevel.DANGEROUS,
                detected_patterns=detected_patterns,
                confidence=1.0,
                sanitized_content=self._sanitize(content)
            )

        # 检查注入模式
        injection_count = 0
        for pattern, category in self.compiled_injection:
            if pattern.search(content):
                detected_patterns.append(f"{category}:{pattern.pattern}")
                injection_count += 1

        # 检查社会工程学模式
        social_count = 0
        for pattern, category in self.compiled_social:
            if pattern.search(content):
                detected_patterns.append(f"{category}:{pattern.pattern}")
                social_count += 1

        # 判定威胁等级
        threat_level, confidence = self._calculate_threat_level(
            injection_count, social_count
        )

        return AnalysisResult(
            threat_level=threat_level,
            detected_patterns=detected_patterns,
            confidence=confidence,
            sanitized_content=self._sanitize(content) if threat_level != ThreatLevel.SAFE else None
        )

    def _calculate_threat_level(self, injection_count: int, social_count: int) -> Tuple[ThreatLevel, float]:
        """
        计算威胁等级和置信度

        Returns:
            (ThreatLevel, confidence)
        """
        total = injection_count * 2 + social_count  # 注入模式权重更高

        if total == 0:
            return ThreatLevel.SAFE, 1.0
        elif total >= 5:
            return ThreatLevel.DANGEROUS, min(0.95, 0.7 + total * 0.05)
        elif total >= 2:
            return ThreatLevel.SUSPICIOUS, min(0.8, 0.5 + total * 0.1)
        else:
            # 单个模式匹配，根据模式类型决定
            if injection_count > 0:
                return ThreatLevel.SUSPICIOUS, 0.6
            return ThreatLevel.SUSPICIOUS, 0.4

    def _sanitize(self, content: str) -> str:
        """
        净化内容，移除潜在的恶意内容

        注意：这只是辅助手段，主要防护还是依赖检测和人工审查
        """
        sanitized = content

        # 移除系统指令伪装
        sanitized = re.sub(r'system:\s*\w+', '[SYSTEM_TAG_REMOVED]', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\[SYSTEM\]', '[SYSTEM_TAG_REMOVED]', sanitized, flags=re.IGNORECASE)

        # 移除代码块
        sanitized = re.sub(r'```[\s\S]*?```', '[CODE_BLOCK_REMOVED]', sanitized)

        # 移除可疑链接 (保留域名但不保留完整 URL)
        sanitized = re.sub(r'https?://[^\s]+', '[LINK_REMOVED]', sanitized)

        # 移除执行指令
        sanitized = re.sub(r'执行 [^\s,.!?]{1,50}', '[EXECUTE_REMOVED]', sanitized, flags=re.IGNORECASE)

        return sanitized

    def is_safe(self, content: str) -> bool:
        """快速检查内容是否安全"""
        result = self.analyze(content)
        return result.threat_level == ThreatLevel.SAFE

    def validate_or_raise(self, content: str, field_name: str = "content"):
        """
        验证内容，如果不安全则抛出异常

        Args:
            content: 待验证内容
            field_name: 字段名称，用于错误信息

        Raises:
            ValueError: 当内容不安全时
        """
        result = self.analyze(content)
        if result.threat_level == ThreatLevel.DANGEROUS:
            raise ValueError(
                f"内容包含危险模式，检测到：{', '.join(result.detected_patterns[:3])}"
            )
        if result.threat_level == ThreatLevel.SUSPICIOUS and self.strict_mode:
            raise ValueError(
                f"内容包含可疑模式 (严格模式)，检测到：{', '.join(result.detected_patterns[:3])}"
            )


# 全局单例
_default_guard = PromptGuard(strict_mode=False)
_strict_guard = PromptGuard(strict_mode=True)


def get_prompt_guard(strict: bool = False) -> PromptGuard:
    """获取 PromptGuard 实例"""
    return _strict_guard if strict else _default_guard


def analyze_content(content: str) -> AnalysisResult:
    """便捷函数：分析内容"""
    return _default_guard.analyze(content)


def is_content_safe(content: str) -> bool:
    """便捷函数：检查内容是否安全"""
    return _default_guard.is_safe(content)
