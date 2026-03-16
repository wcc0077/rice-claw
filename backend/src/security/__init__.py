"""Security Module - 安全防护模块

This module provides comprehensive security measures for the AI agent marketplace:

1. PromptGuard - Prompt Injection 检测和防护
2. OutputGuard - 输出内容审查和脱敏
3. RateLimiter - 速率限制和资源保护

Usage:
    from src.security import PromptGuard, OutputGuard, RateLimiter

    # Prompt Injection 检测
    guard = PromptGuard()
    result = guard.analyze(user_content)
    if result.threat_level == ThreatLevel.DANGEROUS:
        raise ValueError("危险内容")

    # 输出审查
    output_guard = OutputGuard()
    redacted = output_guard.redact(content).redacted

    # 速率限制
    from src.security.rate_limiter import raise_if_rate_limited
    await raise_if_rate_limited(redis, agent_id, "api_per_second")
"""

from .prompt_guard import (
    PromptGuard,
    ThreatLevel,
    AnalysisResult,
    get_prompt_guard,
    analyze_content,
    is_content_safe,
)

from .output_guard import (
    OutputGuard,
    RedactionResult,
    get_output_guard,
    redact_sensitive,
    scan_content,
)

from .rate_limiter import (
    RateLimiter,
    RateLimitMiddleware,
    RateLimitConfig,
    check_rate_limit,
    raise_if_rate_limited,
)


__all__ = [
    # Prompt Guard
    "PromptGuard",
    "ThreatLevel",
    "AnalysisResult",
    "get_prompt_guard",
    "analyze_content",
    "is_content_safe",

    # Output Guard
    "OutputGuard",
    "RedactionResult",
    "get_output_guard",
    "redact_sensitive",
    "scan_content",

    # Rate Limiter
    "RateLimiter",
    "RateLimitMiddleware",
    "RateLimitConfig",
    "check_rate_limit",
    "raise_if_rate_limited",
]
