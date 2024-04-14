# -*- coding: utf-8 -*-
# @File     : yamibo_checkin.py
# @Time     : 2021/04/07 15:48
# @Author   : Jckling

import os

import cloudscraper
import requests
from bs4 import BeautifulSoup
from lxml import html

# cookies
COOKIES = os.environ.get("YAMIBO_COOKIES")
SESSION = requests.Session()
msg = []

HEADERS = {
    "Host": "bbs.yamibo.com",
    "Connection": "keep-alive",
    "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-full-version": "123.0.6312.106",
    "sec-ch-ua-arch": "x86",
    "sec-ch-ua-platform": "Windows",
    "sec-ch-ua-platform-version": "15.0.0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-bitness": "64",
    "sec-ch-ua-full-version-list": '"Google Chrome";v="123.0.6312.106", "Not:A-Brand";v="8.0.0.0", "Chromium";v="123.0.6312.106"',
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://bbs.yamibo.com/plugin.php?id=zqlj_sign",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,ja;q=0.7,zh-TW;q=0.6",
    "Cookie": COOKIES,
}

# Bypass Cloudflare
scraper = cloudscraper.create_scraper(sess=SESSION)


# 登录
def fhash():
    url = "https://bbs.yamibo.com/plugin.php?id=zqlj_sign"
    r = scraper.get(url)
    tree = html.fromstring(r.text)

    try:
        hash = tree.xpath('//*[@id="scbar_form"]/input[2]')[0].attrib['value']
        return hash
    except Exception as e:
        print("no form hash")
        print(r.headers)
        return ""


# 签到
def check_in():
    url = "https://bbs.yamibo.com/plugin.php?id=zqlj_sign&sign=" + fhash()
    r = scraper.get(url)
    tree = html.fromstring(r.text)

    try:
        message = tree.xpath('//*[@id="messagetext"]/p[1]/text()')[0]
        global msg
        if "打卡成功" in message:
            msg += [{"name": "签到信息", "value": "签到成功"}]
        elif "打过卡" in message:
            msg += [{"name": "签到信息", "value": "已签到"}]
        elif "登录" in message:
            msg += [{"name": "签到信息", "value": "登录失败，Cookie 可能已失效"}]
            return False
        else:
            msg += [{"name": "签到信息", "value": message}]
            return False
        return True
    except Exception as e:
        msg += [{"name": "签到信息", "value": e}]
        return False


# 查询
def query_credit():
    # 对象信息
    r = scraper.get("https://bbs.yamibo.com/plugin.php?id=zqlj_sign")
    tree = html.fromstring(r.text)

    try:
        checkin_msg = tree.xpath('//div[@class="bm signbtn cl"]/a/text()')[0]
        stat = tree.xpath('//*[@id="wp"]/div[2]/div[2]/div[3]/div[2]/ul/li/text()')
        global msg
        msg += [{"name": s.split("：")[0], "value": s.split("：")[1]} for s in stat]
    except Exception as e:
        msg += [{"name": "查询对象失败", "value": e}]

    # 积分信息
    r = scraper.get("https://bbs.yamibo.com/home.php?mod=spacecp&ac=credit")
    soup = BeautifulSoup(r.text, "lxml")
    tree = html.fromstring(str(soup))
    try:
        credit = tree.xpath('//ul[@class="creditl mtm bbda cl"]/li/text()')
        data = [i.strip() for i in credit]
        msg += [
            {"name": "对象", "value": data[1]},
            {"name": "积分", "value": data[2]},
            {"name": "总积分", "value": data[3]},
            {"name": "规则", "value": "总积分 = 积分 + 对象/3"}
        ]
    except Exception as e:
        msg += [{"name": "查询积分失败", "value": e}]


def main():
    SESSION.headers.update(HEADERS)
    if check_in():
        query_credit()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" 300 签到开始 ".center(60, "="))
    print(main())
    print(" 300 签到结束 ".center(60, "="), "\n")
