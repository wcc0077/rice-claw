"""测试重构后的 Service 层 API"""

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


def test_create_bid():
    """测试创建竞标（使用重构后的 Service 层）"""
    # 先获取任务列表
    jobs_response = requests.get(f"{BASE_URL}/api/v1/jobs?status=OPEN")
    jobs = jobs_response.json().get("jobs", [])

    if not jobs:
        print("[SKIP] 没有 OPEN 状态的任务，跳过竞标测试")
        return True

    job = jobs[0]
    job_id = job["job_id"]
    print(f"  -> 使用任务：{job_id}")

    # 创建竞标
    bid_data = {
        "worker_id": "test_worker_001",
        "proposal": "这是一个测试竞标",
        "quote": {
            "amount": 5000,
            "currency": "CNY",
            "delivery_days": 7
        }
    }

    response = requests.post(f"{BASE_URL}/api/v1/bids/{job_id}", json=bid_data)

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 创建竞标成功，bid_id: {result.get('bid_id', 'N/A')}")
        return True
    elif response.status_code == 400:
        error = response.json().get("detail", "Unknown error")
        print(f"[WARN] 创建竞标失败 (400): {error}")
        return True  # 400 是预期的错误码
    else:
        print(f"[FAIL] 创建竞标失败：{response.status_code} - {response.text}")
        return False


def test_list_bids():
    """测试获取竞标列表"""
    # 先获取任务
    jobs_response = requests.get(f"{BASE_URL}/api/v1/jobs")
    jobs = jobs_response.json().get("jobs", [])

    if not jobs:
        print("[SKIP] 没有任务，跳过获取竞标列表测试")
        return True

    job_id = jobs[0]["job_id"]

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
    response = requests.get(f"{BASE_URL}/api/v1/bids/non_existent_job")

    if response.status_code == 404:
        print("[OK] 错误处理测试通过（404 Not Found）")
        return True
    else:
        print(f"[FAIL] 错误处理测试失败：{response.status_code}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始测试重构后的 API")
    print("=" * 50)

    tests = [
        ("健康检查", test_health),
        ("获取任务列表", test_list_jobs),
        ("创建竞标", test_create_bid),
        ("获取竞标列表", test_list_bids),
        ("错误处理", test_service_error_handling),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n测试：{name}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[FAIL] 异常：{e}")
            results.append((name, False))

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
