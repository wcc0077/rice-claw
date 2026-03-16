# -*- coding: utf-8 -*-
"""Authentication API endpoints for admin console."""

import re
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select

from ..auth.jwt_config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from ..db.database import SessionLocal
from ..models.db_models import AdminUser
from ..models.schemas import (
    SendSMSRequest,
    SendSMSResponse,
    SMSLoginRequest,
    SMSLoginResponse,
    LoginRequest,
    TokenResponse,
)
from ..services.sms_service import SMSService
from loguru import logger

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Phone validation regex (Chinese mobile)
PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


def create_jwt_token(user_id: str) -> str:
    """Create JWT token for user."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def generate_username_from_phone(phone: str) -> str:
    """Generate username from phone number (e.g., user_138****8000)."""
    masked = f"{phone[:3]}****{phone[-4:]}"
    return f"user_{masked}"


@router.post("/sms/send", response_model=SendSMSResponse)
async def send_sms_code(request: SendSMSRequest):
    """
    Send SMS verification code.

    Rate limited to 5 codes per hour per phone.
    """
    # Validate phone format
    if not PHONE_PATTERN.match(request.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    # Send verification code
    try:
        result = SMSService.send_verification_code(request.phone, purpose="login")

        if not result["success"]:
            # Check if it's a rate limit error
            if "秒后再试" in result["message"] or "分钟后再试" in result["message"]:
                raise HTTPException(status_code=429, detail=result["message"])
            # For SMS service errors, return the actual error message for debugging
            logger.error(f"SMS send failed for {request.phone[:3]}****{request.phone[-4:]}: {result['message']}")
            raise HTTPException(status_code=500, detail=result["message"])

        return SendSMSResponse(success=True, message="验证码已发送")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in SMS send: {e}")
        raise HTTPException(status_code=500, detail="发送验证码失败，请稍后重试")


@router.post("/sms/login", response_model=SMSLoginResponse)
async def sms_login(request: SMSLoginRequest):
    """
    Login or register with SMS verification code.

    If phone is not registered, a new account is created automatically.
    """
    # Validate phone format
    if not PHONE_PATTERN.match(request.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    # Validate code format (6 digits)
    if not re.match(r"^\d{6}$", request.code):
        raise HTTPException(status_code=400, detail="验证码格式不正确")

    # Verify SMS code
    verify_result = SMSService.verify_code(request.phone, request.code, purpose="login")

    if not verify_result["valid"]:
        raise HTTPException(status_code=400, detail=verify_result["message"])

    # Find or create user
    is_new_user = False
    with SessionLocal() as db:
        stmt = select(AdminUser).where(AdminUser.phone == request.phone)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Auto-register new user
            is_new_user = True
            user_id = f"admin_{secrets.token_hex(8)}"
            username = generate_username_from_phone(request.phone)

            user = AdminUser(
                user_id=user_id,
                username=username,
                phone=request.phone,
                phone_verified=True,
                role="admin",
                status=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New admin user registered: {user_id} via phone {request.phone[:3]}****{request.phone[-4:]}")
        else:
            # Update phone verified status
            if not user.phone_verified:
                user.phone_verified = True
                db.commit()

    # Create JWT token
    token = create_jwt_token(user.user_id)

    return SMSLoginResponse(
        success=True,
        token=token,
        user={
            "user_id": user.user_id,
            "username": user.username,
            "phone": user.phone,
            "phone_verified": user.phone_verified,
            "role": user.role,
        },
        is_new_user=is_new_user,
    )


@router.post("/password/login", response_model=TokenResponse)
async def password_login(request: LoginRequest):
    """
    Login with username and password (legacy method).
    """
    with SessionLocal() as db:
        stmt = select(AdminUser).where(AdminUser.username == request.username)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.password_hash:
            raise HTTPException(status_code=401, detail="该账户未设置密码，请使用短信登录")

        if not pwd_context.verify(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.status:
            raise HTTPException(status_code=403, detail="账户已被禁用")

    # Create JWT token
    token = create_jwt_token(user.user_id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        agent_id=user.user_id,
    )