# wxpush
wxpush用于搭建个性化的微信消息推送平台。  
原理是依靠微信的公众测试号的模板消息进行推送，将重要消息实时推送给自己。

## 安装&使用
### 准备环境
```bash
git clone https://github.com/ZHLHZHU/wxpush
cd wxpush
pipenv install
```
### 配置文件
1. 把**wxpush.ini.sample**改名为**wxpush.ini**
2. 在[微信测试号管理](https://mp.weixin.qq.com/debug/cgi-bin/sandboxinfo?action=showinfo&t=sandbox/index)页面获得appid和appsecret，并填入wxpush.ini中
3. 创建一个测试模板，模板标题随意，在模板内容中填入:
```
{{from.DATA}}：
{{content.DATA}}
```
4. 把新建的测试模板的ID填入**wxpush.ini**的template_id字段中
5. **server** section中的配置按需修改，**token** section中的配置项保持空白

### 运行
```bash
pipenv run python main.py
```
发送GET请求：
  
http://**ip**:1025/?from=**Title**&to=**openID**&content=**text**&redirect=**url**
* openID可在[微信测试号管理](https://mp.weixin.qq.com/debug/cgi-bin/sandboxinfo?action=showinfo&t=sandbox/index)页面-用户列表-微信号获得
* redirect的url为点击模板消息后跳转的地址
