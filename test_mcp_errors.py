"""Test MCP Error Handling Module."""

import sys
sys.path.insert(0, 'backend/src')

from mcp.errors import (
    MCPError,
    AuthenticationError,
    PermissionDeniedError,
    JobNotFoundError,
    JobSingleTaskConstraintError,
    BidNotFoundError,
    BidSingleTaskConstraintError,
    ValidationError,
)


def test_error_output():
    """Test error message output for agents."""

    print("=" * 60)
    print("MCP Error Handling Test")
    print("=" * 60)

    # Test AuthenticationError
    print("\n1. AuthenticationError:")
    try:
        raise AuthenticationError()
    except AuthenticationError as e:
        print(f"   error_code: {e.error_code}")
        print(f"   message: {e.message}")
        print(f"   message_en: {e.message_en}")
        print(f"   suggestion: {e.suggestion}")

    # Test JobNotFoundError
    print("\n2. JobNotFoundError:")
    try:
        raise JobNotFoundError(job_id="job_123")
    except JobNotFoundError as e:
        print(f"   error_code: {e.error_code}")
        print(f"   message: {e.message}")
        print(f"   suggestion: {e.suggestion}")

    # Test JobSingleTaskConstraintError
    print("\n3. JobSingleTaskConstraintError:")
    try:
        raise JobSingleTaskConstraintError(
            active_job_title="测试任务",
            active_job_status="ACTIVE",
            message="您已有一个进行中的任务",
            suggestion="请等待当前任务完成后再发布新任务"
        )
    except JobSingleTaskConstraintError as e:
        print(f"   error_code: {e.error_code}")
        print(f"   message: {e.message}")
        print(f"   suggestion: {e.suggestion}")

    # Test BidSingleTaskConstraintError
    print("\n4. BidSingleTaskConstraintError:")
    try:
        raise BidSingleTaskConstraintError(
            active_job_title="竞标任务",
            active_bid_status="BIDDING"
        )
    except BidSingleTaskConstraintError as e:
        print(f"   error_code: {e.error_code}")
        print(f"   message: {e.message}")
        print(f"   suggestion: {e.suggestion}")

    # Test PermissionDeniedError
    print("\n5. PermissionDeniedError:")
    try:
        raise PermissionDeniedError(
            action="删除",
            resource_type="任务",
            resource_id="job_123",
            agent_id="agent_456",
            message="您无权删除此任务",
            suggestion="只有任务创建者才能删除任务"
        )
    except PermissionDeniedError as e:
        print(f"   error_code: {e.error_code}")
        print(f"   message: {e.message}")
        print(f"   suggestion: {e.suggestion}")
        print(f"   details: {e.to_dict()}")

    # Test ValidationError
    print("\n6. ValidationError:")
    try:
        raise ValidationError(
            message="预算范围不合法：budget_min 不能大于 budget_max",
            suggestion="请检查预算设置，确保 budget_min <= budget_max"
        )
    except ValidationError as e:
        print(f"   error_code: {e.error_code}")
        print(f"   message: {e.message}")
        print(f"   suggestion: {e.suggestion}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_error_output()
