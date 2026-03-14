"""声誉体系 API 测试脚本

运行方式:
    cd backend
    uv run python scripts/test_reputation_api.py
"""

import requests
import time

BASE_URL = "http://localhost:8001/api/v1"


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_reputation_api():
    """测试声誉体系相关 API"""

    # 1. 创建测试工人
    print_section("1. 创建测试工人 Agent")
    worker_payload = {
        "agent_id": "test_worker_001",
        "agent_type": "worker",
        "name": "测试工人 001",
        "capabilities": ["python", "web 开发"],
        "description": "一个测试用的工人 agent"
    }
    resp = requests.post(f"{BASE_URL}/agents", json=worker_payload)
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"工人创建成功!")
        print(f"  - 声誉分数：{data.get('reputation_score', 'N/A')}")
        print(f"  - 声誉等级：{data.get('reputation_level', 'N/A')}")
        print(f"  - 声誉星级：{data.get('reputation_stars', 'N/A')}")
    else:
        print(f"错误：{resp.text}")

    # 2. 创建测试雇主
    print_section("2. 创建测试雇主 Agent")
    employer_payload = {
        "agent_id": "test_employer_001",
        "agent_type": "employer",
        "name": "测试雇主 001",
        "capabilities": [],
        "description": "一个测试用的雇主 agent"
    }
    resp = requests.post(f"{BASE_URL}/agents", json=employer_payload)
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"雇主创建成功：{data.get('name')}")
    else:
        print(f"错误：{resp.text}")

    # 3. 创建测试任务
    print_section("3. 创建测试任务")
    job_payload = {
        "employer_id": "test_employer_001",
        "title": "测试任务 - Python 开发",
        "description": "这是一个测试任务",
        "required_tags": ["python", "web"],
        "budget": {"min": 1000, "max": 2000, "currency": "CNY"},
        "bid_limit": 5
    }
    resp = requests.post(f"{BASE_URL}/jobs", json=job_payload)
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        job_id = data.get('job_id')
        print(f"任务创建成功：{job_id}")
    else:
        print(f"错误：{resp.text}")
        job_id = None

    if not job_id:
        print("\n 任务创建失败，跳过后续测试")
        return

    # 4. 工人提交竞标
    print_section("4. 工人提交竞标")
    bid_payload = {
        "worker_id": "test_worker_001",
        "proposal": "我有 5 年 Python 开发经验，可以按时完成",
        "quote": {
            "amount": 1500,
            "currency": "CNY",
            "delivery_days": 7
        }
    }
    resp = requests.post(f"{BASE_URL}/bids/{job_id}", json=bid_payload)
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        bid_id = data.get('bid_id')
        print(f"竞标提交成功：{bid_id}")
    else:
        print(f"错误：{resp.text}")
        bid_id = None

    if not bid_id:
        # 尝试获取已有的竞标
        resp = requests.get(f"{BASE_URL}/bids/{job_id}")
        if resp.status_code == 200:
            bids = resp.json().get('bids', [])
            if bids:
                bid_id = bids[0].get('bid_id')
                print(f"使用已有竞标：{bid_id}")

    if not bid_id:
        print("\n 竞标获取失败，跳过评分测试")
        return

    # 5. 雇主接受竞标
    print_section("5. 雇主接受竞标")
    resp = requests.post(f"{BASE_URL}/bids/{job_id}/{bid_id}/accept")
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        print("竞标接受成功")
    else:
        print(f"错误：{resp.text}")

    # 6. 模拟订单完成 (需要调用 my-orders API 更新状态)
    print_section("6. 更新订单状态为 COMPLETED")

    # 先更新为 IN_PROGRESS
    update_payload = {"status": "IN_PROGRESS"}
    resp = requests.patch(
        f"{BASE_URL}/my-orders/{bid_id}/status?worker_id=test_worker_001",
        json=update_payload
    )
    print(f"更新为 IN_PROGRESS: 状态码={resp.status_code}")
    if resp.status_code != 200:
        print(f"错误：{resp.text}")

    # 再更新为 COMPLETED
    update_payload = {"status": "COMPLETED"}
    resp = requests.patch(
        f"{BASE_URL}/my-orders/{bid_id}/status?worker_id=test_worker_001",
        json=update_payload
    )
    print(f"更新为 COMPLETED: 状态码={resp.status_code}")
    if resp.status_code == 200:
        print("订单状态更新成功")
    else:
        print(f"错误：{resp.text}")
        print("注意：如果此端点需要认证，请手动更新数据库")

    # 7. 雇主评分
    print_section("7. 雇主对订单进行评分")
    rating_payload = {
        "bid_id": bid_id,
        "rating": 5,  # 5 星好评
        "comment": "工作完成得很好！"
    }
    resp = requests.post(f"{BASE_URL}/bids/{job_id}/{bid_id}/rate", json=rating_payload)
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"评分成功!")
        print(f"  - 评分：{data.get('rating')}星")
        print(f"  - 评论：{data.get('comment')}")
        worker_rep = data.get('worker_reputation', {})
        print(f"  - 新声誉分数：{worker_rep.get('score', 'N/A')}")
        print(f"  - 变化：{worker_rep.get('change', 'N/A')}")
    else:
        print(f"错误：{resp.text}")
        print("注意：如果订单状态不是 COMPLETED/DELIVERED，评分会失败")

    # 8. 查看工人最终声誉
    print_section("8. 查看工人最终声誉")
    resp = requests.get(f"{BASE_URL}/agents/test_worker_001")
    print(f"状态码：{resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"工人信息:")
        print(f"  - 声誉分数：{data.get('reputation_score', 'N/A')}")
        print(f"  - 声誉等级：{data.get('reputation_level', 'N/A')}")
        print(f"  - 声誉星级：{data.get('reputation_stars', 'N/A')}")
        print(f"  - 完成订单数：{data.get('completed_jobs', 'N/A')}")
    else:
        print(f"错误：{resp.text}")

    print_section("测试完成")


if __name__ == "__main__":
    print("声誉体系 API 测试")
    print("请确保后端服务已启动：uv run uvicorn src.main:app --reload")
    print("\n开始测试...\n")

    try:
        test_reputation_api()
    except requests.exceptions.ConnectionError:
        print("\n错误：无法连接到后端服务")
        print("请确保后端服务正在运行：uv run uvicorn src.main:app --reload")
    except Exception as e:
        print(f"\n测试出错：{e}")
