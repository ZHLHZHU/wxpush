import socket
import threading
import time
from urllib.parse import unquote
import requests
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
appID = os.getenv("APPID")
appsecret = os.getenv("APPSECRET")
template_id = os.getenv("TEMPLATE_ID")
http_coding = "utf-8"
http_addr = "0.0.0.0"
http_port = 1025
#TODO:增加读配置文件功能，抛弃dotenv

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
            print("完成数据库更新")
    print("完成检查数据库")


def push(from_, to, content):
    sqlite_con = sqlite3.connect("data.db")
    cursor = sqlite_con.cursor()
    cursor.execute("select content from access_token")
    result = cursor.fetchone()
    access_token = result[0]
    # print(access_token)
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s" % access_token
    requests_body = {'touser': to,
                     'template_id': template_id,
                     'url': 'https://www.zhlh6.cn', 'topcolor': '#FF0000',
                     'data': {"from": {"value": from_, "color": "#000000"},
                              "content": {"value": content, "color": "#003366"}}}
    r = requests.post(url=url, json=requests_body)
    return r.content


def abort(conn, code):
    if code == 501:
        msg = "HTTP/1.0 501 Method Not Implemented\r\nContent-Type: text/html\r\n\r\n<HTML><HEAD><TITLE>Method Not Implemented</TITLE></HEAD>\r\n<BODY><P>HTTP request method not supported.</P>\r\n</BODY></HTML>\r\n"
        conn.sendall(msg.encode(http_coding))
        conn.close()


def return_msg(conn, content):
    msg = "HTTP/1.1 200 OK\r\n"
    msg += "Content-Type: text/html\r\n\r\n"
    msg += content
    conn.sendall(msg.encode(http_coding))
    conn.close()


def process_http(conn):
    receive_data = conn.recv(3000)  # GET方法只收2k+字节
    request = receive_data.decode(http_coding)
    try:
        method = request.split(" ")[0]
        args = request.split(" ")[1]
        print(method)
        print(args)
    except:
        abort(500)
        return
    if method != "GET":
        abort(conn, 501)
        return

    args_dict = dict()
    args = args[args.find("?") + 1:]  # 分离出?后面的参数
    for arg in args.split("&"):
        kv = arg.split("=")
        args_dict[kv[0]] = kv[1]
    from_ = unquote(args_dict.get("from"), http_coding)
    to = unquote(args_dict.get("to"), http_coding)
    content = unquote(args_dict.get("content"), http_coding)
    if from_ and to and content:
        return_msg(conn, push(from_, to, content).decode("utf-8"))
    else:
        return_msg(conn, "Parameter error!")


if __name__ == "__main__":
    init()
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.bind((http_addr, http_port))
    sk.listen()
    while True:
        conn, address = sk.accept()
        print("[x]receive from:" + str(address))
        th = threading.Thread(target=process_http, args=(conn,), daemon=True)
        th.start()
