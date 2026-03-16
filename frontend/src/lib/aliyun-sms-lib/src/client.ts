// This file is auto-generated, don't edit it
import Console from '@alicloud/tea-console';
import Env from '@alicloud/darabonba-env';
import OpenApi, * as $OpenApi from '@alicloud/openapi-client';
import Dysmsapi, * as $Dysmsapi from '@alicloud/dysmsapi20180501';
import Util from '@alicloud/tea-util';
import Number from '@darabonba/number';
import * as $tea from '@alicloud/tea-typescript';


export default class Client {

  // 使用AK&SK初始化账号Client 
  static createDysmsapiClient(): Dysmsapi {
    let config = new $OpenApi.Config({
      accessKeyId: Env.getEnv("ACCESS_KEY_ID"),
      accessKeySecret: Env.getEnv("ACCESS_KEY_SECRET"),
    });
    config.endpoint = "dysmsapi.ap-southeast-1.aliyuncs.com";
    return new Dysmsapi(config);
  }

  static async sendMessageWithTemplate(client: Dysmsapi, to: string, from: string, templateCode: string, templateParam: string, smsUpExtendCode: string): Promise<void> {
    let req = new $Dysmsapi.SendMessageWithTemplateRequest({
      to: to,
      from: from,
      templateCode: templateCode,
      templateParam: templateParam,
      smsUpExtendCode: smsUpExtendCode,
    });
    let resp = await client.sendMessageWithTemplate(req);
    Console.log(Util.toJSONString(Util.toMap(resp)));
  }

  static async main(args: string[]): Promise<void> {
    // 接收短信号码。号码格式为:国际区号+号码。例如:861503871****。
    let to = args[0];
    // 发送方标识。发往中国传入签名,请在控制台申请短信签名;发往非中国地区传入senderId。
    let from = args[1];
    // 模板code
    let templateCode = args[2];
    // 短信模板变量对应的实际值,参数格式为JSON格式。如果模板中存在变量,该参数为必填项。例如:{"name":"xd","value":"hello"}
    let templateParam = args[3];
    // 上行短信扩展码
    let smsUpExtendCode = args[4];
    let client = Client.createDysmsapiClient();
    await Client.sendMessageWithTemplate(client, to, from, templateCode, templateParam, smsUpExtendCode);
  }

}

Client.main(process.argv.slice(2));