"""
各平台数据采集器：
- 抖音热榜采集
- 小红书热榜采集
- 微信视频号热榜采集

采集策略说明：
    由于各平台官方API通常需要登录态或加密签名，本工具优先使用以下策略：
    1. 优先尝试平台公开/半公开接口
    2. 若失败则使用第三方热榜聚合API（如vvhan、tophub等）
    3. 若全部失败则使用网页爬取方式
    4. 最终兜底生成模拟示例数据（标注数据来源）
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

from .config import (
    DOUYIN_CONFIG,
    XIAOHONGSHU_CONFIG,
    WEIXIN_VIDEO_CONFIG,
    TOPHUB_CONFIG,
    TOP_N,
    BOOK_QUOTE_KEYWORDS,
)
from .utils import make_request, is_book_quote_content, sleep_random

logger = logging.getLogger(__name__)


# ============================================================================
#  抖音热榜采集
# ============================================================================

class DouyinCrawler:
    """抖音热榜采集器"""

    def __init__(self):
        self.config = DOUYIN_CONFIG
        self.platform = self.config["name"]

    def fetch_hot_list(self) -> List[Dict[str, Any]]:
        """
        获取抖音热榜数据，按优先级尝试多种方式
        
        Returns:
            热榜数据列表
        """
        logger.info(f"[{self.platform}] 开始采集热榜数据...")

        # 方式1: 尝试第三方聚合API
        result = self._fetch_from_third_party()
        if result:
            logger.info(f"[{self.platform}] 通过第三方API获取到 {len(result)} 条数据")
            return result[:TOP_N]

        # 方式2: 尝试tophub今日热榜
        result = self._fetch_from_tophub()
        if result:
            logger.info(f"[{self.platform}] 通过TopHub获取到 {len(result)} 条数据")
            return result[:TOP_N]

        # 方式3: 尝试抖音网页版
        result = self._fetch_from_web()
        if result:
            logger.info(f"[{self.platform}] 通过网页版获取到 {len(result)} 条数据")
            return result[:TOP_N]

        logger.warning(f"[{self.platform}] 所有采集方式均失败，使用示例数据")
        return self._generate_sample_data()

    def _fetch_from_third_party(self) -> Optional[List[Dict[str, Any]]]:
        """通过第三方聚合API获取"""
        try:
            url = self.config["third_party_url"]
            resp = make_request(url)
            if not resp:
                return None

            data = resp.json()
            items = []

            # 适配vvhan API格式
            hot_list = data.get("data", [])
            if not hot_list and isinstance(data, list):
                hot_list = data

            for idx, item in enumerate(hot_list):
                title = item.get("title", "") or item.get("name", "") or item.get("word", "")
                if not title:
                    continue

                parsed = {
                    "rank": idx + 1,
                    "title": title.strip(),
                    "hot_value": item.get("hot", "") or item.get("hotValue", "") or item.get("score", ""),
                    "content": item.get("desc", "") or item.get("description", "") or "",
                    "tags": self._extract_tags(title),
                    "author": item.get("author", "") or "",
                    "likes": item.get("likes", "") or "",
                    "url": item.get("url", "") or item.get("link", "") or "",
                    "cover": item.get("pic", "") or item.get("cover", "") or "",
                    "source": f"{self.platform}-第三方API",
                    "is_book_quote": is_book_quote_content(title),
                }
                items.append(parsed)

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] 第三方API采集失败: {e}")
            return None

    def _fetch_from_tophub(self) -> Optional[List[Dict[str, Any]]]:
        """通过今日热榜(tophub)获取"""
        try:
            url = TOPHUB_CONFIG["douyin_url"]
            resp = make_request(url)
            if not resp:
                return None

            soup = BeautifulSoup(resp.text, "lxml")
            items = []

            # 解析今日热榜页面
            table = soup.find("table", class_="table")
            if not table:
                # 尝试其他选择器
                entries = soup.select(".al .t a, .jc a, td.al a")
                for idx, entry in enumerate(entries):
                    title = entry.get_text(strip=True)
                    if not title:
                        continue
                    items.append({
                        "rank": idx + 1,
                        "title": title,
                        "hot_value": "",
                        "content": "",
                        "tags": self._extract_tags(title),
                        "author": "",
                        "likes": "",
                        "url": entry.get("href", ""),
                        "cover": "",
                        "source": f"{self.platform}-TopHub",
                        "is_book_quote": is_book_quote_content(title),
                    })
            else:
                rows = table.find_all("tr")[1:]  # 跳过表头
                for idx, row in enumerate(rows):
                    cols = row.find_all("td")
                    if len(cols) < 2:
                        continue
                    title_td = cols[1] if len(cols) > 1 else cols[0]
                    title_link = title_td.find("a")
                    title = title_link.get_text(strip=True) if title_link else title_td.get_text(strip=True)

                    hot_value = ""
                    if len(cols) > 2:
                        hot_value = cols[2].get_text(strip=True)

                    items.append({
                        "rank": idx + 1,
                        "title": title,
                        "hot_value": hot_value,
                        "content": "",
                        "tags": self._extract_tags(title),
                        "author": "",
                        "likes": "",
                        "url": title_link.get("href", "") if title_link else "",
                        "cover": "",
                        "source": f"{self.platform}-TopHub",
                        "is_book_quote": is_book_quote_content(title),
                    })

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] TopHub采集失败: {e}")
            return None

    def _fetch_from_web(self) -> Optional[List[Dict[str, Any]]]:
        """通过抖音网页版热榜获取"""
        try:
            url = self.config["hot_board_url"]
            headers = {
                "Referer": "https://www.douyin.com/",
            }
            if self.config.get("cookie"):
                headers["Cookie"] = self.config["cookie"]

            resp = make_request(url, headers=headers)
            if not resp:
                return None

            soup = BeautifulSoup(resp.text, "lxml")
            items = []

            # 尝试解析抖音热榜页面结构
            # 抖音热榜页面是动态渲染的，尝试从脚本标签获取数据
            scripts = soup.find_all("script")
            for script in scripts:
                text = script.string or ""
                if "hotList" in text or "hot_list" in text or "trending" in text:
                    # 尝试提取JSON数据
                    json_matches = re.findall(r'\{[^{}]*"word"[^{}]*\}', text)
                    for match in json_matches:
                        try:
                            item_data = json.loads(match)
                            title = item_data.get("word", "") or item_data.get("title", "")
                            if title:
                                items.append({
                                    "rank": len(items) + 1,
                                    "title": title.strip(),
                                    "hot_value": item_data.get("hot_value", ""),
                                    "content": "",
                                    "tags": self._extract_tags(title),
                                    "author": "",
                                    "likes": "",
                                    "url": "",
                                    "cover": "",
                                    "source": f"{self.platform}-网页版",
                                    "is_book_quote": is_book_quote_content(title),
                                })
                        except json.JSONDecodeError:
                            continue

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] 网页版采集失败: {e}")
            return None

    def _extract_tags(self, title: str) -> List[str]:
        """从标题中提取相关标签"""
        tags = []
        for kw in BOOK_QUOTE_KEYWORDS:
            if kw in title:
                tags.append(kw)
        # 提取#号标签
        hashtags = re.findall(r'#(\S+?)(?:\s|#|$)', title)
        tags.extend(hashtags)
        return list(set(tags))

    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """生成示例数据（当所有采集方式都失败时使用）"""
        logger.warning(f"[{self.platform}] 正在生成示例数据，请注意这不是真实数据")
        sample_titles = [
            "人生就是一场修行#书单推荐",
            "这段话治愈了多少人#金句",
            "读完这本书 我沉默了#好书推荐",
            "余华说：活着本身就是一种力量#名言语录",
            "张爱玲最扎心的一段话#文案",
            "《人间值得》里最经典的一句话",
            "莫言获奖后说了一段话引人深思",
            "这本书建议你20岁之前一定要读",
            "深夜读到这段话 瞬间泪目了",
            "鲁迅先生说的这句话太清醒了",
        ]

        items = []
        for idx, title in enumerate(sample_titles):
            items.append({
                "rank": idx + 1,
                "title": title,
                "hot_value": f"模拟热度{(10 - idx) * 100}w",
                "content": f"这是「{title}」的示例文案内容，实际采集时会替换为真实内容。",
                "tags": self._extract_tags(title),
                "author": "示例作者",
                "likes": f"{(10 - idx) * 10}w",
                "url": "",
                "cover": "",
                "source": f"{self.platform}-示例数据",
                "is_book_quote": True,
            })
        return items


# ============================================================================
#  小红书热榜采集
# ============================================================================

class XiaohongshuCrawler:
    """小红书热榜采集器"""

    def __init__(self):
        self.config = XIAOHONGSHU_CONFIG
        self.platform = self.config["name"]

    def fetch_hot_list(self) -> List[Dict[str, Any]]:
        """获取小红书热榜数据"""
        logger.info(f"[{self.platform}] 开始采集热榜数据...")

        # 方式1: 第三方聚合API
        result = self._fetch_from_third_party()
        if result:
            logger.info(f"[{self.platform}] 通过第三方API获取到 {len(result)} 条数据")
            return result[:TOP_N]

        # 方式2: tophub
        result = self._fetch_from_tophub()
        if result:
            logger.info(f"[{self.platform}] 通过TopHub获取到 {len(result)} 条数据")
            return result[:TOP_N]

        # 方式3: 小红书网页版
        result = self._fetch_from_web()
        if result:
            logger.info(f"[{self.platform}] 通过网页版获取到 {len(result)} 条数据")
            return result[:TOP_N]

        logger.warning(f"[{self.platform}] 所有采集方式均失败，使用示例数据")
        return self._generate_sample_data()

    def _fetch_from_third_party(self) -> Optional[List[Dict[str, Any]]]:
        """通过第三方聚合API获取"""
        try:
            url = self.config["third_party_url"]
            resp = make_request(url)
            if not resp:
                return None

            data = resp.json()
            items = []

            hot_list = data.get("data", [])
            if not hot_list and isinstance(data, list):
                hot_list = data

            for idx, item in enumerate(hot_list):
                title = item.get("title", "") or item.get("name", "") or item.get("word", "")
                if not title:
                    continue

                parsed = {
                    "rank": idx + 1,
                    "title": title.strip(),
                    "hot_value": item.get("hot", "") or item.get("hotValue", "") or item.get("score", ""),
                    "content": item.get("desc", "") or item.get("description", "") or item.get("note", "") or "",
                    "tags": self._extract_tags(title),
                    "author": item.get("author", "") or item.get("nickname", "") or "",
                    "likes": item.get("likes", "") or item.get("likeCount", "") or "",
                    "url": item.get("url", "") or item.get("link", "") or "",
                    "cover": item.get("pic", "") or item.get("cover", "") or item.get("image", "") or "",
                    "source": f"{self.platform}-第三方API",
                    "is_book_quote": is_book_quote_content(title),
                }
                items.append(parsed)

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] 第三方API采集失败: {e}")
            return None

    def _fetch_from_tophub(self) -> Optional[List[Dict[str, Any]]]:
        """通过今日热榜获取"""
        try:
            url = TOPHUB_CONFIG["xiaohongshu_url"]
            resp = make_request(url)
            if not resp:
                return None

            soup = BeautifulSoup(resp.text, "lxml")
            items = []

            table = soup.find("table", class_="table")
            if table:
                rows = table.find_all("tr")[1:]
                for idx, row in enumerate(rows):
                    cols = row.find_all("td")
                    if len(cols) < 2:
                        continue
                    title_td = cols[1] if len(cols) > 1 else cols[0]
                    title_link = title_td.find("a")
                    title = title_link.get_text(strip=True) if title_link else title_td.get_text(strip=True)

                    hot_value = ""
                    if len(cols) > 2:
                        hot_value = cols[2].get_text(strip=True)

                    items.append({
                        "rank": idx + 1,
                        "title": title,
                        "hot_value": hot_value,
                        "content": "",
                        "tags": self._extract_tags(title),
                        "author": "",
                        "likes": "",
                        "url": title_link.get("href", "") if title_link else "",
                        "cover": "",
                        "source": f"{self.platform}-TopHub",
                        "is_book_quote": is_book_quote_content(title),
                    })
            else:
                entries = soup.select(".al .t a, .jc a, td.al a")
                for idx, entry in enumerate(entries):
                    title = entry.get_text(strip=True)
                    if title:
                        items.append({
                            "rank": idx + 1,
                            "title": title,
                            "hot_value": "",
                            "content": "",
                            "tags": self._extract_tags(title),
                            "author": "",
                            "likes": "",
                            "url": entry.get("href", ""),
                            "cover": "",
                            "source": f"{self.platform}-TopHub",
                            "is_book_quote": is_book_quote_content(title),
                        })

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] TopHub采集失败: {e}")
            return None

    def _fetch_from_web(self) -> Optional[List[Dict[str, Any]]]:
        """通过小红书网页版获取"""
        try:
            url = self.config["explore_url"]
            headers = {
                "Referer": "https://www.xiaohongshu.com/",
            }
            if self.config.get("cookie"):
                headers["Cookie"] = self.config["cookie"]

            resp = make_request(url, headers=headers)
            if not resp:
                return None

            soup = BeautifulSoup(resp.text, "lxml")
            items = []

            # 尝试解析小红书探索页
            # 小红书也是动态渲染，尝试从脚本和meta中提取
            scripts = soup.find_all("script")
            for script in scripts:
                text = script.string or ""
                if "note" in text.lower() or "explore" in text.lower():
                    try:
                        # 尝试匹配JSON对象
                        json_str = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*;', text)
                        if json_str:
                            state = json.loads(json_str.group(1))
                            notes = state.get("explore", {}).get("feed", [])
                            for idx, note in enumerate(notes):
                                note_data = note.get("note_card", {}) or note
                                title = note_data.get("title", "") or note_data.get("display_title", "")
                                if title:
                                    items.append({
                                        "rank": idx + 1,
                                        "title": title.strip(),
                                        "hot_value": "",
                                        "content": note_data.get("desc", ""),
                                        "tags": self._extract_tags(title),
                                        "author": note_data.get("user", {}).get("nickname", ""),
                                        "likes": note_data.get("liked_count", ""),
                                        "url": f"https://www.xiaohongshu.com/explore/{note_data.get('id', '')}",
                                        "cover": note_data.get("cover", {}).get("url", ""),
                                        "source": f"{self.platform}-网页版",
                                        "is_book_quote": is_book_quote_content(title),
                                    })
                    except (json.JSONDecodeError, AttributeError):
                        continue

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] 网页版采集失败: {e}")
            return None

    def _extract_tags(self, title: str) -> List[str]:
        """从标题中提取相关标签"""
        tags = []
        for kw in BOOK_QUOTE_KEYWORDS:
            if kw in title:
                tags.append(kw)
        hashtags = re.findall(r'#(\S+?)(?:\s|#|$)', title)
        tags.extend(hashtags)
        return list(set(tags))

    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """生成示例数据"""
        logger.warning(f"[{self.platform}] 正在生成示例数据，请注意这不是真实数据")
        sample_titles = [
            "这本书读完让人沉默很久#书单推荐",
            "张爱玲说：笑，全世界便与你同声笑#金句摘抄",
            "30岁之前一定要读的10本书#好书推荐",
            "治愈系文案｜总有一句戳中你#文案分享",
            "深夜emo时读到的一段话#语录",
            "《被讨厌的勇气》里最触动我的话",
            "杨绛先生这段话简直人间清醒",
            "收藏！50句绝美古诗词文案",
            "看完《活着》我哭了三次",
            "林徽因最温柔的一句话送给所有女孩",
        ]

        items = []
        for idx, title in enumerate(sample_titles):
            items.append({
                "rank": idx + 1,
                "title": title,
                "hot_value": f"模拟热度{(10 - idx) * 80}w",
                "content": f"这是「{title}」的示例文案内容，实际采集时会替换为真实内容。",
                "tags": self._extract_tags(title),
                "author": "示例作者",
                "likes": f"{(10 - idx) * 5}w",
                "url": "",
                "cover": "",
                "source": f"{self.platform}-示例数据",
                "is_book_quote": True,
            })
        return items


# ============================================================================
#  微信视频号热榜采集
# ============================================================================

class WeixinVideoCrawler:
    """微信视频号热榜采集器"""

    def __init__(self):
        self.config = WEIXIN_VIDEO_CONFIG
        self.platform = self.config["name"]

    def fetch_hot_list(self) -> List[Dict[str, Any]]:
        """获取微信视频号热榜数据"""
        logger.info(f"[{self.platform}] 开始采集热榜数据...")

        # 方式1: 第三方聚合API
        result = self._fetch_from_third_party()
        if result:
            logger.info(f"[{self.platform}] 通过第三方API获取到 {len(result)} 条数据")
            return result[:TOP_N]

        # 方式2: 备用数据源
        result = self._fetch_from_backup()
        if result:
            logger.info(f"[{self.platform}] 通过备用数据源获取到 {len(result)} 条数据")
            return result[:TOP_N]

        # 方式3: tophub
        result = self._fetch_from_tophub()
        if result:
            logger.info(f"[{self.platform}] 通过TopHub获取到 {len(result)} 条数据")
            return result[:TOP_N]

        logger.warning(f"[{self.platform}] 所有采集方式均失败，使用示例数据")
        return self._generate_sample_data()

    def _fetch_from_third_party(self) -> Optional[List[Dict[str, Any]]]:
        """通过第三方聚合API获取"""
        try:
            url = self.config["third_party_url"]
            resp = make_request(url)
            if not resp:
                return None

            data = resp.json()
            items = []

            hot_list = data.get("data", [])
            if not hot_list and isinstance(data, list):
                hot_list = data

            for idx, item in enumerate(hot_list):
                title = item.get("title", "") or item.get("name", "") or item.get("word", "")
                if not title:
                    continue

                parsed = {
                    "rank": idx + 1,
                    "title": title.strip(),
                    "hot_value": item.get("hot", "") or item.get("hotValue", "") or item.get("score", ""),
                    "content": item.get("desc", "") or item.get("description", "") or "",
                    "tags": self._extract_tags(title),
                    "author": item.get("author", "") or "",
                    "likes": item.get("likes", "") or "",
                    "url": item.get("url", "") or item.get("link", "") or "",
                    "cover": item.get("pic", "") or item.get("cover", "") or "",
                    "source": f"{self.platform}-第三方API",
                    "is_book_quote": is_book_quote_content(title),
                }
                items.append(parsed)

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] 第三方API采集失败: {e}")
            return None

    def _fetch_from_backup(self) -> Optional[List[Dict[str, Any]]]:
        """通过备用数据源获取"""
        for backup_url in self.config.get("backup_urls", []):
            try:
                resp = make_request(backup_url)
                if not resp:
                    continue

                data = resp.json()
                items = []

                # 适配不同API返回格式
                hot_list = (
                    data.get("data", [])
                    or data.get("result", [])
                    or data.get("list", [])
                )
                if isinstance(hot_list, dict):
                    hot_list = hot_list.get("list", []) or hot_list.get("items", [])

                for idx, item in enumerate(hot_list):
                    title = (
                        item.get("title", "")
                        or item.get("name", "")
                        or item.get("keyword", "")
                    )
                    if not title:
                        continue

                    items.append({
                        "rank": idx + 1,
                        "title": title.strip(),
                        "hot_value": item.get("hot", "") or item.get("hotnum", "") or "",
                        "content": item.get("desc", "") or item.get("digest", "") or "",
                        "tags": self._extract_tags(title),
                        "author": item.get("author", "") or "",
                        "likes": item.get("likes", "") or "",
                        "url": item.get("url", "") or item.get("link", "") or "",
                        "cover": item.get("pic", "") or item.get("cover", "") or "",
                        "source": f"{self.platform}-备用数据源",
                        "is_book_quote": is_book_quote_content(title),
                    })

                if items:
                    return items
            except Exception as e:
                logger.warning(f"[{self.platform}] 备用数据源采集失败 [{backup_url}]: {e}")
                continue
        return None

    def _fetch_from_tophub(self) -> Optional[List[Dict[str, Any]]]:
        """通过今日热榜获取"""
        try:
            url = TOPHUB_CONFIG["weixin_url"]
            resp = make_request(url)
            if not resp:
                return None

            soup = BeautifulSoup(resp.text, "lxml")
            items = []

            table = soup.find("table", class_="table")
            if table:
                rows = table.find_all("tr")[1:]
                for idx, row in enumerate(rows):
                    cols = row.find_all("td")
                    if len(cols) < 2:
                        continue
                    title_td = cols[1] if len(cols) > 1 else cols[0]
                    title_link = title_td.find("a")
                    title = title_link.get_text(strip=True) if title_link else title_td.get_text(strip=True)

                    hot_value = ""
                    if len(cols) > 2:
                        hot_value = cols[2].get_text(strip=True)

                    items.append({
                        "rank": idx + 1,
                        "title": title,
                        "hot_value": hot_value,
                        "content": "",
                        "tags": self._extract_tags(title),
                        "author": "",
                        "likes": "",
                        "url": title_link.get("href", "") if title_link else "",
                        "cover": "",
                        "source": f"{self.platform}-TopHub",
                        "is_book_quote": is_book_quote_content(title),
                    })

            return items if items else None
        except Exception as e:
            logger.warning(f"[{self.platform}] TopHub采集失败: {e}")
            return None

    def _extract_tags(self, title: str) -> List[str]:
        """从标题中提取相关标签"""
        tags = []
        for kw in BOOK_QUOTE_KEYWORDS:
            if kw in title:
                tags.append(kw)
        hashtags = re.findall(r'#(\S+?)(?:\s|#|$)', title)
        tags.extend(hashtags)
        return list(set(tags))

    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """生成示例数据"""
        logger.warning(f"[{self.platform}] 正在生成示例数据，请注意这不是真实数据")
        sample_titles = [
            "人这一生要读懂三句话#人生感悟",
            "稻盛和夫说：成功不在于能力#励志语录",
            "这本书改变了我的认知#读书推荐",
            "周国平最走心的一段话#金句",
            "季羡林写给年轻人的忠告",
            "《平凡的世界》最经典的一段话",
            "白岩松说出了多少人的心声",
            "读完《百年孤独》终于理解了这句话",
            "真正的强大是内心的平静#治愈文案",
            "王小波最浪漫的一句话送给你",
        ]

        items = []
        for idx, title in enumerate(sample_titles):
            items.append({
                "rank": idx + 1,
                "title": title,
                "hot_value": f"模拟热度{(10 - idx) * 60}w",
                "content": f"这是「{title}」的示例文案内容，实际采集时会替换为真实内容。",
                "tags": self._extract_tags(title),
                "author": "示例作者",
                "likes": f"{(10 - idx) * 8}w",
                "url": "",
                "cover": "",
                "source": f"{self.platform}-示例数据",
                "is_book_quote": True,
            })
        return items
