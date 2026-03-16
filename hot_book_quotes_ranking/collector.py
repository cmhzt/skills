"""
热门短视频平台书单/金句热榜采集器（主入口）

功能：
    - 采集抖音、小红书、微信视频号的书单/金句类热榜Top50
    - 获取文案内容、标签等信息
    - 格式化输出到本地文件（JSON + TXT），文件名带时间戳后缀（年月日时）

使用方式：
    from hot_book_quotes_ranking import HotRankingCollector
    
    collector = HotRankingCollector()
    collector.run()
"""

import logging
import warnings
from typing import Dict, List, Any, Optional

from .crawlers import DouyinCrawler, XiaohongshuCrawler, WeixinVideoCrawler
from .utils import save_to_file, save_all_to_file, save_to_txt, sleep_random
from .config import TOP_N

# 抑制SSL警告
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

logger = logging.getLogger(__name__)


class HotRankingCollector:
    """
    热门短视频平台书单/金句热榜采集器
    
    支持平台：
        - 抖音
        - 小红书
        - 微信视频号
    
    采集内容：
        - 热榜标题
        - 热度值
        - 文案内容
        - 相关标签
        - 作者信息
        - 点赞数
        - 链接
    """

    def __init__(self, output_dir: Optional[str] = None, top_n: int = TOP_N):
        """
        初始化采集器
        
        Args:
            output_dir: 自定义输出目录，默认为项目下的output目录
            top_n: 每个平台获取的热榜数量上限，默认50
        """
        self.top_n = top_n
        self.output_dir = output_dir

        # 初始化各平台采集器
        self.crawlers = {
            "抖音": DouyinCrawler(),
            "小红书": XiaohongshuCrawler(),
            "微信视频号": WeixinVideoCrawler(),
        }

        # 存储采集结果
        self.results: Dict[str, List[Dict[str, Any]]] = {}

    def collect_douyin(self) -> List[Dict[str, Any]]:
        """采集抖音热榜"""
        crawler = self.crawlers["抖音"]
        data = crawler.fetch_hot_list()
        self.results["抖音"] = data[:self.top_n]
        return self.results["抖音"]

    def collect_xiaohongshu(self) -> List[Dict[str, Any]]:
        """采集小红书热榜"""
        crawler = self.crawlers["小红书"]
        data = crawler.fetch_hot_list()
        self.results["小红书"] = data[:self.top_n]
        return self.results["小红书"]

    def collect_weixin_video(self) -> List[Dict[str, Any]]:
        """采集微信视频号热榜"""
        crawler = self.crawlers["微信视频号"]
        data = crawler.fetch_hot_list()
        self.results["微信视频号"] = data[:self.top_n]
        return self.results["微信视频号"]

    def collect_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        采集所有平台热榜数据
        
        Returns:
            各平台数据字典 {"平台名": [数据列表]}
        """
        logger.info("=" * 60)
        logger.info("开始采集所有平台书单/金句热榜数据")
        logger.info("=" * 60)

        # 依次采集各平台数据
        self.collect_douyin()
        sleep_random(1.0, 2.0)

        self.collect_xiaohongshu()
        sleep_random(1.0, 2.0)

        self.collect_weixin_video()

        # 统计
        total = sum(len(v) for v in self.results.values())
        logger.info("=" * 60)
        logger.info(f"采集完成！共获取 {total} 条数据")
        for platform, items in self.results.items():
            logger.info(f"  - {platform}: {len(items)} 条")
        logger.info("=" * 60)

        return self.results

    def save_results(self) -> Dict[str, str]:
        """
        保存采集结果到本地文件
        
        Returns:
            保存的文件路径字典
        """
        if not self.results:
            logger.warning("没有可保存的数据，请先执行采集")
            return {}

        saved_files = {}
        kwargs = {}
        if self.output_dir:
            kwargs["output_dir"] = self.output_dir

        # 1. 分平台保存JSON
        for platform, items in self.results.items():
            if items:
                filepath = save_to_file(items, platform, **kwargs)
                saved_files[f"{platform}_json"] = filepath

        # 2. 全平台汇总JSON
        filepath = save_all_to_file(self.results, **kwargs)
        saved_files["全平台汇总_json"] = filepath

        # 3. 全平台汇总TXT（更易读）
        filepath = save_to_txt(self.results, **kwargs)
        saved_files["全平台汇总_txt"] = filepath

        logger.info(f"\n文件保存完成，共生成 {len(saved_files)} 个文件:")
        for name, path in saved_files.items():
            logger.info(f"  📁 {name}: {path}")

        return saved_files

    def filter_book_quote_items(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        从采集结果中筛选出书单/金句类内容
        
        Returns:
            筛选后的数据字典
        """
        filtered = {}
        for platform, items in self.results.items():
            book_quote_items = [item for item in items if item.get("is_book_quote", False)]
            if book_quote_items:
                filtered[platform] = book_quote_items
                logger.info(
                    f"[{platform}] 筛选出 {len(book_quote_items)}/{len(items)} 条书单/金句类内容"
                )
        return filtered

    def run(self, filter_only_book_quotes: bool = False) -> Dict[str, str]:
        """
        一键运行：采集 -> (可选)筛选 -> 保存
        
        Args:
            filter_only_book_quotes: 是否只保留书单/金句类内容
        
        Returns:
            保存的文件路径字典
        """
        # 步骤1: 采集所有平台数据
        self.collect_all()

        # 步骤2: 可选筛选
        if filter_only_book_quotes:
            filtered = self.filter_book_quote_items()
            if filtered:
                self.results = filtered
                logger.info("已筛选为仅书单/金句类内容")

        # 步骤3: 保存结果
        saved_files = self.save_results()
        return saved_files

    def get_summary(self) -> str:
        """获取采集结果摘要"""
        if not self.results:
            return "暂无采集数据"

        lines = ["📊 采集结果摘要:", ""]
        total = 0
        for platform, items in self.results.items():
            count = len(items)
            total += count
            book_quote_count = sum(1 for item in items if item.get("is_book_quote", False))
            lines.append(f"  【{platform}】")
            lines.append(f"    - 总数据: {count} 条")
            lines.append(f"    - 书单/金句类: {book_quote_count} 条")
            if items:
                lines.append(f"    - 热度最高: {items[0].get('title', '无标题')}")
            lines.append("")

        lines.append(f"  📈 总计: {total} 条数据")
        return "\n".join(lines)
