import configparser
import threading
import time
from typing import Optional
import requests
from fastapi import FastAPI, Query
import uvicorn

config = configparser.ConfigParser()
config.read("wxpush.ini")
appID = config.get("weixin", "APPID")
appsecret = config.get("weixin", "APPSECRET")
template_id = config.get("weixin", "TEMPLATE_ID")
app = FastAPI(docs_url=None, redoc_url=None)


def update_access_token():
    """
    更新access_token
    :return: None
    """
    access_token = config.get("token", "access_token")
    start_time = config.get("token", "start_time")
    remain_time = config.get("token", "remain_time")
    if access_token == "" or start_time == "" or remain_time == "" or int(
            time.time()) > int(start_time) + int(remain_time) + 500:  # 如果access_token过期或者没有获取过
        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (
            appID, appsecret)
        r = requests.get(url)
        if r.json().get("errcode", "0") == "0":
            rjson = r.json()
            config.set("token", "access_token", rjson["access_token"])
            config.set("token", "start_time", str(int(time.time())))
            config.set("token", "remain_time", str(rjson["expires_in"]))
            config.write(open("wxpush.ini", "w"))


def push(from_, to, content, redirect):
    """
    使用微信公众号测试接口推送消息
    :param from_: 发件人，对应消息模板的参数
    :param to: 收件人的openID
    :param content: 消息内容
    :return: None
    """
    access_token = config.get("token", "access_token")
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s" % access_token
    requests_body = {'touser': to,
                     'template_id': template_id,
                     'url': redirect, 'topcolor': '#FF0000',
                     'data': {"from": {"value": from_, "color": "#000000"},
                              "content": {"value": content, "color": "#003366"}}}
    r = requests.post(url=url, json=requests_body)
    return r.content


@app.get("/")
def request_push(to: str, content: str, redirect: str,
                 from_: Optional[str] = Query(None, alias="from")):
    return push(from_, to, content, redirect)


if __name__ == '__main__':
    update_access_token()  # 第一次获取access_token
    timer = threading.Timer(120, update_access_token)  # 每10秒更新一次access_token
    timer.start()
    uvicorn.run(app, host="0.0.0.0", port=1025, log_level="info")
