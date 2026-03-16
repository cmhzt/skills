"""
配置文件：定义各平台采集相关的配置参数
"""

import os

# ============== 通用配置 ==============
# 请求超时时间（秒）
REQUEST_TIMEOUT = 15
# 请求重试次数
RETRY_TIMES = 3
# 请求间隔（秒），避免触发反爬
REQUEST_INTERVAL = 1.5
# 热榜获取数量上限
TOP_N = 50
# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# ============== 通用请求头 ==============
COMMON_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# ============== 书单/金句类关键词 ==============
# 用于在热榜中筛选书单/金句类内容的关键词
BOOK_QUOTE_KEYWORDS = [
    "书单", "金句", "名言", "语录", "文案", "治愈", "扎心",
    "人生感悟", "情感", "心灵鸡汤", "励志", "读书", "推荐书",
    "经典语句", "暖心", "走心", "戳心", "泪目", "共鸣",
    "人间清醒", "醍醐灌顶", "深度好文", "好书推荐", "必读",
    "句子", "文字", "摘抄", "笔记", "书摘", "好词好句",
    "正能量", "哲理", "鸡汤", "夜读", "晚安", "早安",
    "情话", "独白", "旁白", "解说文案", "热门文案",
]

# ============== 抖音配置 ==============
DOUYIN_CONFIG = {
    "name": "抖音",
    # 抖音热榜API（公开接口）
    "hot_search_url": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
    # 抖音热点榜
    "hot_board_url": "https://www.douyin.com/hot",
    # 备用：第三方热榜聚合
    "third_party_url": "https://api.vvhan.com/api/hotlist/douyinHot",
    # cookie（如需登录态，请手动填入）
    "cookie": os.environ.get("DOUYIN_COOKIE", ""),
}

# ============== 小红书配置 ==============
XIAOHONGSHU_CONFIG = {
    "name": "小红书",
    # 小红书发现页/热搜
    "hot_search_url": "https://edith.xiaohongshu.com/api/sns/v1/search/hot_list",
    # 小红书探索页
    "explore_url": "https://www.xiaohongshu.com/explore",
    # 备用：第三方热榜聚合
    "third_party_url": "https://api.vvhan.com/api/hotlist/xiaohongshuHot",
    # cookie（如需登录态，请手动填入）
    "cookie": os.environ.get("XHS_COOKIE", ""),
}

# ============== 微信视频号配置 ==============
WEIXIN_VIDEO_CONFIG = {
    "name": "微信视频号",
    # 微信视频号暂无公开热榜API，使用第三方数据源
    "third_party_url": "https://api.vvhan.com/api/hotlist/wxVideoHot",
    # 备用数据源
    "backup_urls": [
        "https://api.gumengya.com/Api/WechatHot",
    ],
    # cookie（如需登录态，请手动填入）
    "cookie": os.environ.get("WEIXIN_VIDEO_COOKIE", ""),
}

# ============== 今日热榜配置（备用数据源） ==============
TOPHUB_CONFIG = {
    # 今日热榜 - 抖音
    "douyin_url": "https://tophub.today/n/DpQvNABoNE",
    # 今日热榜 - 小红书
    "xiaohongshu_url": "https://tophub.today/n/ltMV6de4AJ",
    # 今日热榜 - 微信视频号(暂无独立页面，使用微信热搜)
    "weixin_url": "https://tophub.today/n/WnBe01o371",
}
