import threading
import time
import requests
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
appID = os.getenv("APPID")
appsecret = os.getenv("APPSECRET")


def init():
    sqlite_con = sqlite3.connect("data.db")
    cursor = sqlite_con.cursor()
    cursor.execute(
        "create table if not exists access_token(content text primary key, start_time int,remain_time int)")  # 建表
    sqlite_con.commit()
    sqlite_con.close()  # 建表
    update_access_token()  # 第一次获取access_token
    timer = threading.Timer(10, update_access_token)
    timer.start()


def update_access_token():
    """
    更新access_token
    :return: None
    """
    sqlite_con = sqlite3.connect("data.db")
    cursor = sqlite_con.cursor()
    cursor.execute("select content,start_time,remain_time from access_token")
    result = cursor.fetchone()
    if int(time.time()) > result[1] + result[2] + 60 or not result:  # 如果access_token过期或者没有获取过
        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (
            appID, appsecret)
        r = requests.get(url)
        if r.json().get("errcode", "0") == "0":
            rjson = r.json()
            cursor = sqlite_con.cursor()
            cursor.execute("update access_token set content=?,start_time=?,remain_time=?",
                           (rjson["access_token"], int(time.time()), rjson["expires_in"]))
            cursor.close()
            sqlite_con.commit()
    print("完成更新数据库")


def push():
    sqlite_con = sqlite3.connect("data.db")
    cursor = sqlite_con.cursor()
    cursor.execute("select content from access_token")
    result = cursor.fetchone()
    access_token = result[0]
    # print(access_token)
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s" % access_token
    requests_body = {'touser': '',
                     'template_id': '',
                     'url': 'https://www.zhlh6.com', 'topcolor': '#FF0000',
                     'data': {"from": {"value": "Z&L", "color": "#000000"},
                              "content": {"value": "helloworld!?!", "color": "#003366"}}}
    r = requests.post(url=url, json=requests_body)
    print(r.content)


if __name__ == "__main__":
    init()
    push()
    # TODO:提供外部接口调用
