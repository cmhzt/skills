"""
工具类：提供通用的请求、解析、文件操作等功能
"""

import json
import os
import time
import random
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from fake_useragent import UserAgent

from .config import (
    REQUEST_TIMEOUT,
    RETRY_TIMES,
    REQUEST_INTERVAL,
    COMMON_HEADERS,
    OUTPUT_DIR,
)

logger = logging.getLogger(__name__)


def get_random_ua() -> str:
    """获取随机 User-Agent"""
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        # 备用UA列表
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ]
        return random.choice(ua_list)


def make_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    cookies: Optional[Dict[str, str]] = None,
    timeout: int = REQUEST_TIMEOUT,
    retry: int = RETRY_TIMES,
) -> Optional[requests.Response]:
    """
    通用HTTP请求方法，带重试和随机UA
    
    Args:
        url: 请求URL
        method: 请求方法
        headers: 自定义请求头
        params: URL参数
        data: 表单数据
        json_data: JSON数据
        cookies: Cookie
        timeout: 超时时间
        retry: 重试次数
    
    Returns:
        Response对象或None
    """
    req_headers = {**COMMON_HEADERS}
    req_headers["User-Agent"] = get_random_ua()
    if headers:
        req_headers.update(headers)

    for attempt in range(retry):
        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=req_headers,
                params=params,
                data=data,
                json=json_data,
                cookies=cookies,
                timeout=timeout,
                verify=False,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(
                f"请求失败 [{url}] 第{attempt + 1}次尝试: {e}"
            )
            if attempt < retry - 1:
                sleep_time = REQUEST_INTERVAL * (attempt + 1) + random.uniform(0.5, 1.5)
                time.sleep(sleep_time)
            else:
                logger.error(f"请求最终失败 [{url}]: {e}")
    return None


def get_timestamp_suffix() -> str:
    """获取时间戳后缀，格式：年月日时 (YYYYMMDDHH)"""
    return datetime.now().strftime("%Y%m%d%H")


def save_to_file(
    data: List[Dict[str, Any]],
    platform: str,
    output_dir: str = OUTPUT_DIR,
) -> str:
    """
    将数据保存到本地JSON文件
    
    Args:
        data: 要保存的数据列表
        platform: 平台名称
        output_dir: 输出目录
    
    Returns:
        保存的文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = get_timestamp_suffix()
    filename = f"{platform}_书单金句热榜_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    output_data = {
        "platform": platform,
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(data),
        "items": data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"[{platform}] 数据已保存至: {filepath}")
    return filepath


def save_all_to_file(
    all_data: Dict[str, List[Dict[str, Any]]],
    output_dir: str = OUTPUT_DIR,
) -> str:
    """
    将所有平台数据汇总保存到一个文件
    
    Args:
        all_data: 所有平台的数据 {platform_name: [items]}
        output_dir: 输出目录
    
    Returns:
        保存的文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = get_timestamp_suffix()
    filename = f"全平台_书单金句热榜_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    total_count = sum(len(items) for items in all_data.values())
    output_data = {
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": total_count,
        "platforms": {},
    }

    for platform, items in all_data.items():
        output_data["platforms"][platform] = {
            "count": len(items),
            "items": items,
        }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"全平台汇总数据已保存至: {filepath}")
    return filepath


def save_to_txt(
    all_data: Dict[str, List[Dict[str, Any]]],
    output_dir: str = OUTPUT_DIR,
) -> str:
    """
    将所有平台数据保存为可读性更好的TXT文件
    
    Args:
        all_data: 所有平台的数据
        output_dir: 输出目录
    
    Returns:
        保存的文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = get_timestamp_suffix()
    filename = f"全平台_书单金句热榜_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    lines = []
    lines.append("=" * 80)
    lines.append(f"  热门短视频平台 书单/金句类热榜 Top50")
    lines.append(f"  采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    for platform, items in all_data.items():
        lines.append(f"{'─' * 80}")
        lines.append(f"  【{platform}】 共 {len(items)} 条")
        lines.append(f"{'─' * 80}")
        lines.append("")

        for i, item in enumerate(items, 1):
            lines.append(f"  {i}. {item.get('title', '无标题')}")
            if item.get("hot_value"):
                lines.append(f"     🔥 热度: {item['hot_value']}")
            if item.get("content"):
                # 内容截断显示
                content = item["content"]
                if len(content) > 200:
                    content = content[:200] + "..."
                lines.append(f"     📝 文案: {content}")
            if item.get("tags"):
                tags_str = ", ".join(item["tags"][:10])
                lines.append(f"     🏷️  标签: {tags_str}")
            if item.get("author"):
                lines.append(f"     👤 作者: {item['author']}")
            if item.get("likes"):
                lines.append(f"     ❤️  点赞: {item['likes']}")
            if item.get("url"):
                lines.append(f"     🔗 链接: {item['url']}")
            lines.append("")

    lines.append("=" * 80)
    lines.append(f"  数据来源：抖音、小红书、微信视频号")
    lines.append(f"  说明：数据通过公开渠道采集，仅供参考")
    lines.append("=" * 80)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"TXT格式数据已保存至: {filepath}")
    return filepath


def is_book_quote_content(title: str, keywords: Optional[List[str]] = None) -> bool:
    """
    判断标题是否属于书单/金句类内容
    
    Args:
        title: 标题文本
        keywords: 关键词列表
    
    Returns:
        是否属于书单/金句类
    """
    from .config import BOOK_QUOTE_KEYWORDS

    if keywords is None:
        keywords = BOOK_QUOTE_KEYWORDS

    title_lower = title.lower()
    return any(kw in title_lower for kw in keywords)


def sleep_random(min_sec: float = 0.5, max_sec: float = 2.0):
    """随机等待，模拟人工操作"""
    time.sleep(random.uniform(min_sec, max_sec))
