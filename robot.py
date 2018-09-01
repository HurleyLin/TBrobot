#!/usr/bin/python3
#_*_ coding:utf-8 _*_

import top.api

appkey = '25048626'
secret = '5d72a2d66e5d157eb4a2ce989eaded58'
adzone_id = 18432900120

import itchat, time
from itchat.content import *
import json
import requests
import re
from urllib.request import urlretrieve
from datetime import datetime
import threading
import os
import top

current_path = os.path.dirname(os.path.abspath(__file__))

#注销微信
#itchat.logout()

# 通过淘宝客API搜索优惠券
def get_tk_coupon(kw, size=2):
    req = top.api.TbkDgItemCouponGetRequest()
    req.set_app_info(top.appinfo(appkey, secret))
    req.adzone_id = int(adzone_id)
    req.platform = 2
    req.page_size = size
    req.q = kw
    req.page_no = 1
    try:
        resp = req.getResponse()['tbk_dg_item_coupon_get_response']['results']['tbk_coupon']
        print(resp)
        return resp
    except Exception as e:
        print(e)
        return None

# 获取淘口令
def get_token(url, text):
    req = top.api.TbkTpwdCreateRequest()
    req.set_app_info(top.appinfo(appkey, secret))
    req.text = text
    req.url = url
    try:
        resp = req.getResponse()['tbk_tpwd_create_response']['data']['model']
        return resp
    except Exception as e:
        print(e)
        return None

# 收到好友邀请自动添加好友
@itchat.msg_register(FRIENDS)
def add_friend(msg):
    itchat.add_friend(**msg['Text']) # 该操作会自动将新好友的消息录入，不需要重载通讯录
    itchat.send_msg('Nice to meet you!', msg['RecommendInfo']['UserName'])


# 只接收来自于群聊的文本消息
#@itchat.msg_register(TEXT, isGroupChat=True)
# 接收来自好友和群聊的文本消息
#@itchat.msg_register(TEXT, isGroupChat=True, isFriendChat=True)

# 回复群聊搜索
#@itchat.msg_register(TEXT, isGroupChat=True)
# 只接收来自好友的文本消息
#@itchat.msg_register(TEXT, isFriendChat=True)
@itchat.msg_register(TEXT, isGroupChat=False,isFriendChat=True)
def text_reply(msg):
    # 如果消息为@我，且我的群昵称为“@我 + 商品”
    #if msg['isAt'] and msg['Content'][0:8] == '@@我 + 商品':
    if 1:
        # 截取消息正文字符串，提取出搜索词
        #searchword = msg['Content'][9:]
        searchword = msg['Content'][0:]
        #print(msg)
        #print(searchword)

        #私聊
        #print('消息来自于：{0}，内容为：{1}\n'.format(msg['User']['NickName'], msg['Content']))

        #群聊
        print('消息来自于：{0}，内容为：{1}\n'.format(['ActualNickName'], msg['Content']))
        #print(msg['User']['NickName'])
        # 通过搜索词获取淘宝客商品优惠券信息
        response = get_tk_coupon(searchword)
        if (response != None):
            # 遍历获取到的淘宝客商品优惠券信息
            for r in response:
                # 商品标题
                ordername = r['title']
                # 商品当前价
                orderprice = r['zk_final_price']
                # 优惠券信息
                coupon_info = r['coupon_info']
                # 通过正则表达式提取优惠券信息中的面额
                coupon_demonination = int(re.findall(r'(\d+)', coupon_info)[-1])
                # 商品图片
                orderimg = r['pict_url']
                # 获取淘口令
                token = get_token(url=r['coupon_click_url'], text=r['title'])
                # 券后价
                couponprice = round(float(orderprice) - int(coupon_demonination), 1)
                # 通过新浪微博API生成优惠券链接的短链
                link = r['item_url']
                link_resp = requests.get(
                    'http://api.weibo.com/2/short_url/shorten.json?source=2849184197&url_long=' + link).text
                link_short = json.loads(link_resp, encoding='utf-8')['urls'][0]['url_short']
                # 拼接组合文本消息字符串
                msgs = '''/:gift{name}\n/:rose【在售价】{orderprice}元\n/:heart【券后价】{conponprice}元\n/:cake 【抢购链接】{link_short}\n-----------------\n复制这条信息\n{token}打开【手机淘宝】，即可查看\n------------------\n
                '''.format(name=ordername, orderprice=orderprice, conponprice=couponprice, token=token,
                           link_short=link_short)
                # 发送文本消息
                itchat.send(msg=str(msgs), toUserName=msg['FromUserName'])

                '''不发送图片
                # 发送商品图片
                try:
                    image = urlretrieve(url=orderimg, filename=r'%s' % os.path.join(current_path, 'orderimg.jpg'))
                    itchat.send_image(fileDir=r'%s' % os.path.join(current_path, 'orderimg.jpg'),
                                      toUserName=msg['FromUserName'])
                except Exception as e:
                    print("发送图片失败，{}\n".format(e))
                '''
            # 等待3秒继续发送
            time.sleep(2)
        else:
            itchat.send(msg="不好意思，该商品没有加入淘抢购", toUserName=msg['FromUserName'])

# 定时发送消息
def send_order_info():
    n = 1
    while True:
        # 判断当前时间是否大于早上7点且小于晚上十一点
        if datetime.today().hour > 8 and datetime.today().hour < 23:
            print('现在时间：', datetime.today())
            # 获取群聊列表
            chatroom = itchat.get_chatrooms()
            # 遍历群聊列表
            for c in chatroom:
                n = datetime.today().hour - 7
                print(c['UserName'], c['NickName'])
                # 只选择指定的群聊
                if c['NickName'] == '天猫内部精选优惠券1群':
                    try:
                        # 获取淘宝客商品优惠券信息
                        response = get_tk_coupon('')
                        # 遍历商品优惠券信息
                        for r in response:
                            # 商品标题
                            ordername = r['title']
                            # 商品当前价
                            orderprice = r['zk_final_price']
                            coupon_info = r['coupon_info']
                            coupon_demonination = int(re.findall(r'(\d+)', coupon_info)[-1])
                            # 商品图片
                            orderimg = r['pict_url']
                            # 获取淘口令
                            token = get_token(url=r['coupon_click_url'], text=r['title'])
                            # 券后价
                            couponprice = round(float(orderprice) - int(coupon_demonination), 1)
                            # 生成短链
                            link = r['item_url']
                            link_resp = requests.get(
                                'http://api.weibo.com/2/short_url/shorten.json?source=2849184197&url_long=' + link).text
                            link_short = json.loads(link_resp, encoding='utf-8')['urls'][0]['url_short']
                            msgs = '''【{times}点档特惠精选】\n/:gift{name}\n/:rose【在售价】{orderprice}元\n/:heart【券后价】{conponprice}元\n/:cake 【抢购链接】{link_short}\n-----------------\n复制这条信息\n{token}打开【手机淘宝】，即可查看
                            '''.format(times=str(datetime.today().hour),
                                       name=ordername,
                                       orderprice=orderprice,
                                       conponprice=couponprice,
                                       token=token,
                                       link_short=link_short)
                            # 发送文本消息
                            itchat.send(msg=str(msgs), toUserName=c['UserName'])
                            # 发送商品图片
                            try:
                                image = urlretrieve(url=orderimg,
                                                    filename=r'%s' % os.path.join(current_path, 'orderimg.jpg'))
                                itchat.send_image(fileDir=r'%s' % os.path.join(current_path, 'orderimg.jpg'),

                                                  toUserName=c['UserName'])
                            except Exception as e:
                                print("发送图片失败，{}\n".format(e))
                        time.sleep(3)
                    except Exception as e:
                        print('发送失败', e)
            n += 1
        else:
            n = 1
        time.sleep(3600)


if __name__ == '__main__':

    # 登录
    itchat.auto_login(hotReload=True, enableCmdQR=False, picDir=r'%s' % os.path.join(current_path, 'qrcode.jpg'))
    # 创建一个线程用于侦听微信的消息
    t_reply = threading.Thread(target=itchat.run)
    # 创建一个线程用于定时发送消息
    #t_send = threading.Thread(target=send_order_info)

    # 启动线程
    t_reply.start()
    #t_send.start()
    t_reply.join()
    #t_send.join()
