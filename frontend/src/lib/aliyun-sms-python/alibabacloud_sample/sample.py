# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys

from typing import List

from alibabacloud_dysmsapi20180501.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_darabonba_env.client import Client as EnvClient
from alibabacloud_dysmsapi20180501 import models as dysmsapi_models
from alibabacloud_tea_console.client import Client as ConsoleClient
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_dysmsapi_client() -> DysmsapiClient:
        """
        使用AK&SK初始化账号Client
        """
        config = open_api_models.Config(
            access_key_id=EnvClient.get_env('ACCESS_KEY_ID'),
            access_key_secret=EnvClient.get_env('ACCESS_KEY_SECRET')
        )
        config.endpoint = 'dysmsapi.ap-southeast-1.aliyuncs.com'
        return DysmsapiClient(config)

    @staticmethod
    def send_message_with_template(
        client: DysmsapiClient,
        to: str,
        from_: str,
        template_code: str,
        template_param: str,
        sms_up_extend_code: str,
    ) -> None:
        req = dysmsapi_models.SendMessageWithTemplateRequest(
            to=to,
            from=from,
            template_code=template_code,
            template_param=template_param,
            sms_up_extend_code=sms_up_extend_code
        )
        resp = client.send_message_with_template(req)
        ConsoleClient.log(UtilClient.to_jsonstring(UtilClient.to_map(resp)))

    @staticmethod
    async def send_message_with_template_async(
        client: DysmsapiClient,
        to: str,
        from_: str,
        template_code: str,
        template_param: str,
        sms_up_extend_code: str,
    ) -> None:
        req = dysmsapi_models.SendMessageWithTemplateRequest(
            to=to,
            from=from,
            template_code=template_code,
            template_param=template_param,
            sms_up_extend_code=sms_up_extend_code
        )
        resp = await client.send_message_with_template_async(req)
        ConsoleClient.log(UtilClient.to_jsonstring(UtilClient.to_map(resp)))

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        # 接收短信号码。号码格式为:国际区号+号码。例如:861503871****。
        to = args[0]
        # 发送方标识。发往中国传入签名,请在控制台申请短信签名;发往非中国地区传入senderId。
        from = args[1]
        # 模板code
        template_code = args[2]
        # 短信模板变量对应的实际值,参数格式为JSON格式。如果模板中存在变量,该参数为必填项。例如:{"name":"xd","value":"hello"}
        template_param = args[3]
        # 上行短信扩展码
        sms_up_extend_code = args[4]
        client = Sample.create_dysmsapi_client()
        Sample.send_message_with_template(client, to, from, template_code, template_param, sms_up_extend_code)

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        # 接收短信号码。号码格式为:国际区号+号码。例如:861503871****。
        to = args[0]
        # 发送方标识。发往中国传入签名,请在控制台申请短信签名;发往非中国地区传入senderId。
        from = args[1]
        # 模板code
        template_code = args[2]
        # 短信模板变量对应的实际值,参数格式为JSON格式。如果模板中存在变量,该参数为必填项。例如:{"name":"xd","value":"hello"}
        template_param = args[3]
        # 上行短信扩展码
        sms_up_extend_code = args[4]
        client = Sample.create_dysmsapi_client()
        await Sample.send_message_with_template_async(client, to, from, template_code, template_param, sms_up_extend_code)


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
