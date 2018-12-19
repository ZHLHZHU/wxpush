import socket
import threading
import time
from urllib.parse import unquote
import requests
import configparser

config = configparser.ConfigParser()
config.read("wxpush.ini")
appID = config.get("weixin", "APPID")
appsecret = config.get("weixin", "APPSECRET")
template_id = config.get("weixin", "TEMPLATE_ID")
http_coding = config.get("server", "http_coding")
http_addr = config.get("server", "ip")
http_port = config.getint("server", "port")


def init():
    update_access_token()  # 第一次获取access_token
    timer = threading.Timer(10, update_access_token)  # 每10秒更新一次access_token
    timer.start()


def update_access_token():
    """
    更新access_token
    :return: None
    """
    access_token = config.get("token", "access_token")
    start_time = config.get("token", "start_time")
    remain_time = config.get("token", "remain_time")
    if access_token == "" or start_time == "" or remain_time == "" or int(
            time.time()) > int(start_time) + int(remain_time) + 60:  # 如果access_token过期或者没有获取过
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


def abort(conn, code):
    """
    服务器错误返回
    :param conn: socket句柄
    :param code: http错误状态码
    :return: None
    """
    if code == 501:
        msg = "HTTP/1.0 501 Method Not Implemented\r\nContent-Type: text/html\r\n\r\n<HTML><HEAD><TITLE>Method Not Implemented</TITLE></HEAD>\r\n<BODY><P>HTTP request method not supported.</P>\r\n</BODY></HTML>\r\n"
        conn.sendall(msg.encode(http_coding))
        conn.close()


def return_msg(conn, content):
    """
    成功推送消息后，返回微信接口返回的信息
    :param conn: socket句柄
    :param content: 返回消息，是一个json
    :return: None
    """
    msg = "HTTP/1.1 200 OK\r\n"
    msg += "Content-Type: text/html\r\n\r\n"
    msg += content
    conn.sendall(msg.encode(http_coding))
    conn.close()


def process_http(conn):
    """
    对外提供接口
    :param conn:监听端口的socket句柄
    :return:
    """
    receive_data = conn.recv(3000)  # GET方法只收2k+字节
    request = receive_data.decode(http_coding)
    try:
        method = request.split(" ")[0]
        args = request.split(" ")[1]
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
    redirect = unquote(args_dict.get("redirect"), http_coding)  # 从GET请求中分离出目标参数
    if from_ and to and content:
        return_msg(conn, push(from_, to, content,redirect).decode("utf-8"))
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
