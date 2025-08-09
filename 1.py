import feedparser
import requests
import ssl
import json
from urllib.request import Request, urlopen


def get_rss_news(rss_url):
    """
    通过RSS获取新闻 - 增强版（处理SSL问题）
    """
    info = {}

    # 方法1: 直接使用feedparser（你的原始方法）
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        feed = feedparser.parse(rss_url, request_headers=headers)
        if not feed.bozo and len(getattr(feed, "entries", [])) > 0:
            return parse_feed_data(feed)
    except Exception as e:
        print(f"方法1失败 ({rss_url}): {e}")

    # 方法2: 使用requests处理SSL
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(rss_url, headers=headers, timeout=15, verify=True)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            if len(getattr(feed, "entries", [])) > 0:
                return parse_feed_data(feed)
    except Exception as e:
        print(f"方法2失败 ({rss_url}): {e}")

    # 方法3: 忽略SSL验证（最后手段）
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(rss_url, headers=headers, timeout=15, verify=False)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            if len(getattr(feed, "entries", [])) > 0:
                return parse_feed_data(feed)
    except Exception as e:
        print(f"方法3失败 ({rss_url}): {e}")

    # 方法4: 使用urllib处理SSL
    try:
        req = Request(rss_url)
        req.add_header(
            "User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with urlopen(req, context=context, timeout=15) as response:
            data = response.read()
            feed = feedparser.parse(data)
            if len(getattr(feed, "entries", [])) > 0:
                return parse_feed_data(feed)
    except Exception as e:
        print(f"方法4失败 ({rss_url}): {e}")

    print(f"所有方法都失败了: {rss_url}")
    return {}


def parse_feed_data(feed):
    """解析feed数据"""
    info = {}
    try:
        info["title"] = getattr(feed.feed, "title", "未知标题")
        info["description"] = getattr(feed.feed, "description", "无描述")
        info["updatetime"] = getattr(feed.feed, "updated", "未知")
        info["news"] = []

        for entry in feed.entries[:50]:  # 限制前50条
            news_item = {
                "title": getattr(entry, "title", "无标题"),
                "link": getattr(entry, "link", ""),
                "published": getattr(entry, "published", "未知时间"),
                "summary": getattr(
                    entry, "summary", getattr(entry, "description", "无摘要")
                ),
            }
            info["news"].append(news_item)

        if not info["news"]:
            return {}
        return info
    except Exception as e:
        print(f"解析数据出错: {e}")
        return {}


# 测试多个CNN RSS源
rss_sources = [
    {"name": "BBC", "url": "http://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "CNN", "url": "http://rss.cnn.com/rss/edition.rss"},
    {"name": "FKS", "url": "https://moxie.foxnews.com/google-publisher/latest.xml"},
]


for source in rss_sources:
    print(f"加载{source['name']}...")
    info = get_rss_news(source["url"])
    if info:
        with open(f"news/{source['name']}_news.json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=4)
        print(f"{source['name']}已保存至 {source['name']}_news.json")
    else:
        print(f"{source['name']}获取失败")
