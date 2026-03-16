"""WebSocket 路由处理

端点：
- WS /ws/{agent_id} - WebSocket 连接端点
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from ..db.database import get_db, SessionLocal
from ..db import bids as bid_dal
from ..db import job_workers as job_worker_dal
from ..db import artifacts as artifact_dal
from ..db import artifact_versions as artifact_version_dal
from ..db import jobs as job_dal
from ..db.agents import get_agent_by_api_key
from .manager import ConnectionManager, get_connection_manager

router = APIRouter()


async def verify_agent_token(token: str) -> Optional[Any]:
    """验证 Agent Token

    Args:
        token: Agent API Token

    Returns:
        Agent 对象 (如果验证成功) 或 None
    """
    db = SessionLocal()
    try:
        agent = get_agent_by_api_key(db, token)
        if agent:
            # 更新 last_seen_at
            from ..db.agents import update_last_seen
            update_last_seen(db, agent)
        return agent
    finally:
        db.close()


async def handle_grab_order(
    data: Dict[str, Any],
    agent_id: str,
    manager: ConnectionManager,
    db: Session,
    websocket: WebSocket
):
    """处理抢单消息

    请求格式:
    {
        "type": "grab_order",
        "data": {
            "job_id": "job_xxx"
        }
    }

    返回格式:
    {
        "type": "grab_result",
        "data": {
            "success": true/false,
            "bid_id": "bid_xxx",
            "job_id": "job_xxx",
            "message": "..."
        }
    }
    """
    job_id = data.get("data", {}).get("job_id")
    if not job_id:
        await websocket.send_json({
            "type": "error",
            "data": {"code": "INVALID_REQUEST", "message": "Missing job_id"}
        })
        return

    try:
        # 1. 创建 bid (抢单记录)
        bid_data = {
            "job_id": job_id,
            "worker_id": agent_id,
            "proposal": data.get("data", {}).get("proposal", ""),
            "quote": data.get("data", {}).get("quote", {}),
        }

        bid = bid_dal.create_bid(db, bid_data)

        # 2. 创建 job_worker 关联
        job_worker_data = {
            "job_id": job_id,
            "bid_id": bid.bid_id,
            "worker_id": agent_id,
            "status": "PENDING",
        }
        job_worker_dal.create_job_worker(db, job_worker_data)

        # 3. 订阅这个 bid 的消息
        await manager.subscribe_bid(agent_id, bid.bid_id)

        # 4. 返回成功结果
        await websocket.send_json({
            "type": "grab_result",
            "data": {
                "success": True,
                "bid_id": bid.bid_id,
                "job_id": job_id,
                "message": "抢单成功，等待派单"
            }
        })

        # 5. 通知雇主有新的抢单
        job = job_dal.get_job(db, job_id)
        if job:
            await manager.send_to_agent(job.employer_id, {
                "type": "new_bid",
                "data": {
                    "job_id": job_id,
                    "bid_id": bid.bid_id,
                    "worker_id": agent_id
                }
            })

    except ValueError as e:
        # 抢单失败 (如任务不存在、已达上限等)
        await websocket.send_json({
            "type": "grab_result",
            "data": {
                "success": False,
                "job_id": job_id,
                "message": str(e)
            }
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"code": "INTERNAL_ERROR", "message": str(e)}
        })


async def handle_chat(
    data: Dict[str, Any],
    agent_id: str,
    manager: ConnectionManager,
    db: Session,
    websocket: WebSocket
):
    """处理聊天消息

    请求格式:
    {
        "type": "chat",
        "data": {
            "bid_id": "bid_xxx",  # 关键：区分是哪个任务
            "to_agent_id": "agent_xxx",
            "content": "..."
        }
    }
    """
    from ..db.messages import create_message

    bid_id = data.get("data", {}).get("bid_id")
    to_agent_id = data.get("data", {}).get("to_agent_id")
    content = data.get("data", {}).get("content")

    if not all([bid_id, to_agent_id, content]):
        await websocket.send_json({
            "type": "error",
            "data": {"code": "INVALID_REQUEST", "message": "Missing required fields"}
        })
        return

    try:
        # 获取 job_id (从 bid 关联)
        from ..db.bids import get_bid
        bid = get_bid(db, bid_id)
        if not bid:
            raise ValueError("Bid not found")

        # 1. 创建消息记录
        message_data = {
            "job_id": bid.job_id,
            "from_agent_id": agent_id,
            "to_agent_id": to_agent_id,
            "content": content,
            "message_type": "text",
        }
        create_message(db, message_data)

        # 2. 转发给接收方 (带 bid_id 上下文)
        await manager.send_to_bid(bid_id, {
            "type": "new_message",
            "data": {
                "from_agent_id": agent_id,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"code": "CHAT_ERROR", "message": str(e)}
        })


async def handle_deliver(
    data: Dict[str, Any],
    agent_id: str,
    manager: ConnectionManager,
    db: Session,
    websocket: WebSocket
):
    """处理交付消息

    请求格式:
    {
        "type": "deliver",
        "data": {
            "bid_id": "bid_xxx",
            "file_url": "https://...",
            "version": 1,
            "description": "..."
        }
    }
    """
    from ..db.artifacts import create_artifact
    from ..db.artifact_versions import create_artifact_version

    bid_id = data.get("data", {}).get("bid_id")
    file_url = data.get("data", {}).get("file_url")
    version = data.get("data", {}).get("version", 1)
    description = data.get("data", {}).get("description")

    if not all([bid_id, file_url]):
        await websocket.send_json({
            "type": "error",
            "data": {"code": "INVALID_REQUEST", "message": "Missing required fields"}
        })
        return

    try:
        # 获取 bid 和 job
        from ..db.bids import get_bid
        bid = get_bid(db, bid_id)
        if not bid:
            raise ValueError("Bid not found")

        # 1. 创建 artifacts 记录
        artifact_data = {
            "job_id": bid.job_id,
            "worker_id": agent_id,
            "artifact_type": "demo",  # 交付过程中先标记为 demo
            "title": f"Delivery v{version}",
            "content": description or "",
        }
        artifact = create_artifact(db, artifact_data)

        # 2. 创建 artifact_version 记录
        version_data = {
            "artifact_id": artifact.artifact_id,
            "version_number": version,
            "file_url": file_url,
            "worker_id": agent_id,
            "description": description,
            "is_final": False,
        }
        create_artifact_version(db, version_data)

        # 3. 更新 job_worker 状态为 DELIVERED
        from ..db.job_workers import get_job_workers_for_job, update_job_worker_status
        job_workers = get_job_workers_for_job(db, bid.job_id)
        for jw in job_workers:
            if jw["bid_id"] == bid_id:
                update_job_worker_status(db, jw["id"], "DELIVERED")
                break

        # 4. 通知雇主有新的交付
        from ..db.jobs import get_job
        job = get_job(db, bid.job_id)
        if job:
            await manager.send_to_agent(job.employer_id, {
                "type": "delivery_submitted",
                "data": {
                    "job_id": bid.job_id,
                    "bid_id": bid_id,
                    "artifact_id": artifact.artifact_id,
                    "version": version
                }
            })

        # 5. 返回成功
        await websocket.send_json({
            "type": "deliver_result",
            "data": {
                "success": True,
                "artifact_id": artifact.artifact_id,
                "message": "交付成功"
            }
        })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"code": "DELIVER_ERROR", "message": str(e)}
        })


async def handle_ping(
    data: Dict[str, Any],
    websocket: WebSocket
):
    """处理心跳请求"""
    timestamp = data.get("data", {}).get("timestamp", 0)
    await websocket.send_json({
        "type": "pong",
        "data": {"timestamp": timestamp}
    })


@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    token: str = Query(..., description="Agent API Token"),
):
    """WebSocket 连接端点

    连接示例:
        ws://localhost:8000/ws/agent_xxx?token=your_api_token

    支持的消息类型:
    - grab_order: 抢单
    - chat: 聊天
    - deliver: 交付
    - ping: 心跳
    """
    # 1. 验证 agent token
    try:
        agent = await verify_agent_token(token)
        if not agent or agent.agent_id != agent_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception as e:
        await websocket.close(code=4002, reason=f"Auth failed: {str(e)}")
        return

    # 2. 获取 manager 和 db
    manager = await get_connection_manager()
    db = SessionLocal()

    # 3. 建立连接
    connection_id = await manager.connect(websocket, agent_id)
    print(f"[WS] Agent {agent_id} connected ({connection_id})")

    # 4. 推送离线消息
    offline_messages = await manager.get_offline_messages(agent_id)
    for msg in offline_messages:
        await websocket.send_json(msg)

    # 5. 处理消息循环
    try:
        while True:
            # 接收消息
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            msg_type = data.get("type")

            # 根据类型分发处理
            if msg_type == "grab_order":
                await handle_grab_order(data, agent_id, manager, db, websocket)

            elif msg_type == "chat":
                await handle_chat(data, agent_id, manager, db, websocket)

            elif msg_type == "deliver":
                await handle_deliver(data, agent_id, manager, db, websocket)

            elif msg_type == "ping":
                await handle_ping(data, websocket)

            elif msg_type == "subscribe_bid":
                # 手动订阅 bid (用于接收历史 bid 的消息)
                bid_id = data.get("data", {}).get("bid_id")
                if bid_id:
                    await manager.subscribe_bid(agent_id, bid_id)

            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"code": "UNKNOWN_MESSAGE_TYPE", "message": f"Unknown type: {msg_type}"}
                })

    except WebSocketDisconnect:
        print(f"[WS] Agent {agent_id} disconnected")
        await manager.disconnect(agent_id)
    except Exception as e:
        print(f"[WS] Error handling message for {agent_id}: {e}")
        await manager.disconnect(agent_id)
    finally:
        db.close()
