"""声誉体系计算模块 - 简化版

规则说明：
- 初始分数：1500 分
- 分数范围：1000-3000 分

维度与计算：
1. 履约分：每完成 1 单 +10 分，每取消 1 单 -20 分（范围：-200 ~ +200）
2. 质量分：雇主评分平均转换（范围：-100 ~ +100）
   - 5 星：+50 分
   - 4 星：+20 分
   - 3 星：0 分
   - 2 星：-20 分
   - 1 星：-50 分
3. 活跃分：近 30 天每完成 1 单 +15 分（范围：0 ~ +150）

声誉等级：
- 2500-3000: 顶级 (⭐⭐⭐⭐⭐)
- 2000-2500: 优秀 (⭐⭐⭐⭐)
- 1500-2000: 良好 (⭐⭐⭐)
- 1200-1500: 一般 (⭐⭐)
- 1000-1200: 较差 (⭐)
"""

from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session

from ..models.db_models import Agent, Bid


# 声誉等级配置
REPUTATION_LEVELS = [
    (2500, "顶级", "⭐⭐⭐⭐⭐"),
    (2000, "优秀", "⭐⭐⭐⭐"),
    (1500, "良好", "⭐⭐⭐"),
    (1200, "一般", "⭐⭐"),
    (1000, "较差", "⭐"),
]

# 分数限制
MIN_SCORE = 1000
MAX_SCORE = 3000
BASE_SCORE = 1500

# 维度权重限制
MAX_FULFILLMENT_SCORE = 200
MAX_QUALITY_SCORE = 100
MAX_ACTIVITY_SCORE = 150


def clamp(value: int, min_val: int, max_val: int) -> int:
    """限制值在指定范围内"""
    return max(min_val, min(max_val, value))


def get_reputation_level(score: int) -> Tuple[str, str]:
    """根据分数返回声誉等级

    Returns:
        (等级名称，星级符号)
    """
    for threshold, name, stars in REPUTATION_LEVELS:
        if score >= threshold:
            return name, stars
    return "较差", "⭐"


def calculate_quality_score(rating: float) -> int:
    """将雇主评分转换为质量分

    线性映射：
    - 5 星 -> +50 分
    - 4 星 -> +20 分
    - 3 星 -> 0 分
    - 2 星 -> -20 分
    - 1 星 -> -50 分
    """
    # 使用线性插值：rating 1-5 映射到 -50 到 +50
    # 公式：(rating - 3) * 25
    return int((rating - 3) * 25)


def calculate_reputation(db: Session, agent_id: str) -> int:
    """计算 agent 的声誉分数

    Args:
        db: 数据库会话
        agent_id: agent ID

    Returns:
        新的声誉分数 (1000-3000)
    """
    # 获取该 agent 的所有竞标记录
    all_bids = db.query(Bid).filter(Bid.worker_id == agent_id).all()

    if not all_bids:
        # 新 agent，返回基准分
        return BASE_SCORE

    # 1. 履约分计算
    completed_bids = [b for b in all_bids if b.status in ['COMPLETED', 'DELIVERED']]
    cancelled_bids = [b for b in all_bids if b.status == 'CANCELLED']

    fulfillment_score = len(completed_bids) * 10 - len(cancelled_bids) * 20
    fulfillment_score = clamp(fulfillment_score, -MAX_FULFILLMENT_SCORE, MAX_FULFILLMENT_SCORE)

    # 2. 质量分计算（取所有已完成订单的平均评分）
    rated_bids = [b for b in completed_bids if b.employer_rating is not None]

    if rated_bids:
        avg_rating = sum(b.employer_rating for b in rated_bids if b.employer_rating is not None) / len(rated_bids)
        quality_score = calculate_quality_score(avg_rating)
        # 限制在 -100 到 +100 之间
        quality_score = clamp(quality_score, -MAX_QUALITY_SCORE, MAX_QUALITY_SCORE)
    else:
        quality_score = 0

    # 3. 活跃分计算（近 30 天完成的订单）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_completed = db.query(Bid).filter(
        Bid.worker_id == agent_id,
        Bid.status.in_(['COMPLETED', 'DELIVERED']),
        Bid.submitted_at >= thirty_days_ago
    ).count()

    activity_score = min(recent_completed * 15, MAX_ACTIVITY_SCORE)

    # 综合计算
    new_score = BASE_SCORE + fulfillment_score + quality_score + activity_score

    # 限制在 1000-3000 范围内
    return clamp(new_score, MIN_SCORE, MAX_SCORE)


def update_agent_reputation(db: Session, agent_id: str) -> Agent:
    """更新 agent 的声誉分数

    Args:
        db: 数据库会话
        agent_id: agent ID

    Returns:
        更新后的 Agent 对象
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    # 计算新的声誉分数
    new_score = calculate_reputation(db, agent_id)

    # 更新
    agent.reputation_score = new_score
    agent.reputation_updated_at = datetime.now()

    db.commit()
    db.refresh(agent)

    return agent


def get_reputation_change_description(old_score: int, new_score: int) -> str:
    """获取声誉分数变化描述"""
    diff = new_score - old_score

    if diff > 0:
        return f"声誉 +{diff} (订单完成，表现优秀)"
    elif diff < 0:
        return f"声誉 {diff} (订单取消或评价不佳)"
    else:
        return "声誉无变化"
