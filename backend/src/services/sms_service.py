# -*- coding: utf-8 -*-
"""阿里云短信服务模块"""

import os
import random
import secrets
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

# Domestic SMS SDK for Chinese phone numbers
from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysms_models

from ..db.database import SessionLocal
from ..models.db_models import SmsVerificationCode, SmsRateLimit


def utcnow():
    """获取当前UTC时间（无时区，与数据库保持一致）"""
    return datetime.utcnow()


class SMSService:
    """阿里云短信服务"""

    _client: Optional[DysmsapiClient] = None

    @classmethod
    def get_client(cls) -> DysmsapiClient:
        """获取短信客户端单例"""
        if cls._client is None:
            access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID")
            access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET")

            # Check for placeholder values
            if access_key_id == "your_access_key_id_here" or not access_key_id:
                raise ValueError("ALIYUN_ACCESS_KEY_ID 未配置。请在 GitHub Secrets 中添加 ALIYUN_ACCESS_KEY_ID")
            if access_key_secret == "your_access_key_secret_here" or not access_key_secret:
                raise ValueError("ALIYUN_ACCESS_KEY_SECRET 未配置。请在 GitHub Secrets 中添加 ALIYUN_ACCESS_KEY_SECRET")

            # Debug logging (mask sensitive data)
            logger.info(f"Initializing SMS client with AccessKey ID: {access_key_id[:8] + '***' if len(access_key_id) > 8 else '***'}")

            config = open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
            )
            # Domestic SMS endpoint for Chinese phone numbers
            config.endpoint = "dysmsapi.aliyuncs.com"
            cls._client = DysmsapiClient(config)
        return cls._client

    @staticmethod
    def generate_code() -> str:
        """生成6位数字验证码"""
        return "".join([str(random.randint(0, 9)) for _ in range(6)])

    @staticmethod
    def generate_code_id() -> str:
        """生成验证码记录ID"""
        return f"code_{secrets.token_hex(16)}"

    @classmethod
    def send_verification_code(cls, phone: str, purpose: str = "login") -> dict:
        """
        发送短信验证码

        Args:
            phone: 手机号（不带区号，如 13800138000）
            purpose: 用途 ('login' | 'bind_phone')

        Returns:
            dict: {"success": bool, "message": str, "code_id": str}
        """
        # 检查发送频率限制
        rate_check = cls._check_rate_limit(phone)
        if not rate_check["allowed"]:
            return {"success": False, "message": rate_check["message"]}

        # 生成验证码
        code = cls.generate_code()
        code_id = cls.generate_code_id()

        # 存储验证码到数据库
        expires_at = utcnow() + timedelta(minutes=5)
        with SessionLocal() as db:
            verification = SmsVerificationCode(
                code_id=code_id,
                phone=phone,
                code=code,
                purpose=purpose,
                expires_at=expires_at,
            )
            db.add(verification)

            # 更新频率限制
            rate_limit = db.get(SmsRateLimit, phone)
            if rate_limit:
                rate_limit.send_count += 1
                rate_limit.last_sent_at = utcnow()
            else:
                rate_limit = SmsRateLimit(
                    phone=phone,
                    send_count=1,
                    window_start=utcnow(),
                    last_sent_at=utcnow(),
                )
                db.add(rate_limit)

            db.commit()

        # 发送短信
        try:
            result = cls._send_sms(phone, code)
            if result["success"]:
                logger.info(f"SMS sent successfully to {phone[:3]}****{phone[-4:]}")
                return {
                    "success": True,
                    "message": "验证码已发送",
                    "code_id": code_id,
                }
            else:
                logger.error(f"SMS failed: {result['message']}")
                return {"success": False, "message": result["message"]}
        except Exception as e:
            logger.exception(f"SMS service error: {e}")
            return {"success": False, "message": "短信发送失败，请稍后重试"}

    @classmethod
    def _check_rate_limit(cls, phone: str) -> dict:
        """检查发送频率限制（已禁用，用于开发测试）"""
        # 频率限制已禁用，允许无限制发送
        return {"allowed": True}

    @classmethod
    def _send_sms(cls, phone: str, code: str) -> dict:
        """调用阿里云API发送短信（国内版API - SendSms）"""
        client = cls.get_client()

        sign_name = os.getenv("ALIYUN_SMS_SIGN_NAME", "虾有钳")
        template_code = os.getenv("ALIYUN_SMS_TEMPLATE_CODE")
        template_param = f'{{"code":"{code}"}}'

        logger.debug(f"Sending SMS - phone: {phone}, sign_name: {sign_name}, template: {template_code}")

        # 使用国内版API: SendSmsRequest
        request = dysms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=sign_name,
            template_code=template_code,
            template_param=template_param,
        )

        try:
            response = client.send_sms(request)

            # Log full response for debugging
            logger.debug(f"Aliyun SMS response: {response}")
            if response.body:
                logger.debug(f"Response body - code: {response.body.code}, "
                           f"message: {response.body.message}, "
                           f"biz_id: {response.body.biz_id}, "
                           f"request_id: {response.body.request_id}")

            # Domestic API uses 'code' field (string "OK" means success)
            if response.body and response.body.code == "OK":
                return {"success": True}
            else:
                error_code = response.body.code if response.body else "NO_RESPONSE"
                error_msg = response.body.message if response.body else "Unknown error"
                logger.error(f"Aliyun SMS error - code: {error_code}, message: {error_msg}")
                return {"success": False, "message": f"短信发送失败: {error_code} - {error_msg}"}

        except Exception as e:
            logger.exception(f"Aliyun SMS exception: {e}")
            return {"success": False, "message": str(e)}

    @classmethod
    def verify_code(cls, phone: str, code: str, purpose: str = "login") -> dict:
        """
        验证短信验证码

        Args:
            phone: 手机号
            code: 用户输入的验证码
            purpose: 用途

        Returns:
            dict: {"valid": bool, "message": str}
        """
        with SessionLocal() as db:
            # 查找最新的未使用验证码
            from sqlalchemy import select

            stmt = (
                select(SmsVerificationCode)
                .where(SmsVerificationCode.phone == phone)
                .where(SmsVerificationCode.purpose == purpose)
                .where(SmsVerificationCode.used == False)
                .where(SmsVerificationCode.expires_at > utcnow())
                .order_by(SmsVerificationCode.created_at.desc())
            )

            result = db.execute(stmt)
            verification = result.scalars().first()

            if not verification:
                return {"valid": False, "message": "验证码已失效，请重新获取"}

            # 检查尝试次数
            if verification.attempt_count >= 5:
                verification.used = True
                db.commit()
                return {"valid": False, "message": "验证尝试次数过多，请重新获取"}

            # 验证码匹配
            if verification.code == code:
                verification.used = True
                db.commit()
                return {"valid": True, "message": "验证成功"}
            else:
                verification.attempt_count += 1
                db.commit()
                remaining = 5 - verification.attempt_count
                return {
                    "valid": False,
                    "message": f"验证码错误，还剩{remaining}次机会",
                }