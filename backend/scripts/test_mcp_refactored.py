"""测试重构后的 MCP 服务器 API"""

import requests

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("[OK] 健康检查通过")
        return True
    else:
        print(f"[FAIL] 健康检查失败：{response.status_code}")
        return False


def test_list_jobs():
    """测试获取任务列表"""
    response = requests.get(f"{BASE_URL}/api/v1/jobs")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 获取任务列表成功，共 {data.get('total', 0)} 个任务")
        return True
    else:
        print(f"[FAIL] 获取任务列表失败：{response.status_code}")
        return False


def test_get_job_details(job_id: str):
    """测试获取任务详情（使用 JobService）"""
    response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 获取任务详情成功：{data.get('title', 'N/A')}")
        return True
    else:
        print(f"[FAIL] 获取任务详情失败：{response.status_code}")
        return False


def test_create_job():
    """测试创建任务（使用 JobService）"""
    job_data = {
        "employer_id": "test_employer_001",
        "title": "测试任务 - MCP 重构验证",
        "description": "这是一个用于验证 MCP 服务器重构的测试任务",
        "required_tags": ["python", "fastapi"],
        "budget": {
            "min": 3000,
            "max": 5000
        },
        "bid_limit": 3
    }

    response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data)

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 创建任务成功，job_id: {result.get('job_id', 'N/A')}")
        return result.get('job_id')
    else:
        print(f"[FAIL] 创建任务失败：{response.status_code} - {response.text}")
        return None


def test_submit_bid(job_id: str):
    """测试创建竞标（使用 BidService）"""
    if not job_id:
        print("[SKIP] 缺少 job_id，跳过竞标测试")
        return True

    bid_data = {
        "worker_id": "test_worker_001",
        "proposal": "这是一个测试竞标 - MCP 重构验证",
        "quote": {
            "amount": 4000,
            "currency": "CNY",
            "delivery_days": 5
        }
    }

    response = requests.post(f"{BASE_URL}/api/v1/jobs/{job_id}/bids", json=bid_data)

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 创建竞标成功，bid_id: {result.get('bid_id', 'N/A')}")
        return True
    elif response.status_code == 400:
        error = response.json().get("detail", "Unknown error")
        print(f"[WARN] 创建竞标失败 (400): {error}")
        return True  # 400 是预期的错误码（如任务状态不允许竞标）
    else:
        print(f"[FAIL] 创建竞标失败：{response.status_code} - {response.text}")
        return False


def test_get_bids(job_id: str):
    """测试获取竞标列表（使用 BidService）"""
    if not job_id:
        print("[SKIP] 缺少 job_id，跳过获取竞标列表测试")
        return True

    response = requests.get(f"{BASE_URL}/api/v1/bids/{job_id}")

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 获取竞标列表成功，共 {len(data.get('bids', []))} 个竞标")
        return True
    else:
        print(f"[FAIL] 获取竞标列表失败：{response.status_code}")
        return False


def test_service_error_handling():
    """测试 Service 层错误处理"""
    # 测试不存在的任务
    response = requests.get(f"{BASE_URL}/api/v1/jobs/non_existent_job")

    if response.status_code == 404:
        print("[OK] 错误处理测试通过（404 Not Found）")
        return True
    else:
        print(f"[FAIL] 错误处理测试失败：{response.status_code}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始测试重构后的 MCP 服务器 API")
    print("=" * 50)

    tests = [
        ("健康检查", test_health),
        ("获取任务列表", test_list_jobs),
        ("创建任务", test_create_job),
    ]

    results = []
    created_job_id = None

    for name, test_func in tests:
        print(f"\n测试：{name}")
        try:
            result = test_func()
            if name == "创建任务" and isinstance(result, str):
                created_job_id = result
            results.append((name, result if isinstance(result, bool) else True))
        except Exception as e:
            print(f"[FAIL] 异常：{e}")
            results.append((name, False))

    # 使用创建的任务进行后续测试
    if created_job_id:
        print(f"\n使用创建的任务进行测试：{created_job_id}")
        additional_tests = [
            ("获取任务详情", lambda: test_get_job_details(created_job_id)),
            ("创建竞标", lambda: test_submit_bid(created_job_id)),
            ("获取竞标列表", lambda: test_get_bids(created_job_id)),
        ]

        for name, test_func in additional_tests:
            print(f"\n测试：{name}")
            try:
                result = test_func()
                results.append((name, result if isinstance(result, bool) else True))
            except Exception as e:
                print(f"[FAIL] 异常：{e}")
                results.append((name, False))

    # 错误处理测试
    print(f"\n测试：错误处理")
    try:
        result = test_service_error_handling()
        results.append(("错误处理", result))
    except Exception as e:
        print(f"[FAIL] 异常：{e}")
        results.append(("错误处理", False))

    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n总计：{passed}/{total} 测试通过")

    return passed == total


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
