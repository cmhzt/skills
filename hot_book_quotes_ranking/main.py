#!/usr/bin/env python3
"""
热门短视频平台 书单/金句类热榜 Top50 采集工具

使用方法：
    python main.py                  # 采集所有平台数据
    python main.py --filter         # 只保留书单/金句类内容
    python main.py --output ./data  # 指定输出目录
    python main.py --top 30         # 每个平台只获取前30条

功能说明：
    1. 采集抖音、小红书、微信视频号的热榜数据
    2. 提取书单/金句类相关内容
    3. 获取文案内容、标签、作者、点赞数等信息
    4. 格式化输出到本地文件（JSON + TXT），文件名带时间戳后缀（年月日时）
"""

import sys
import os
import argparse
import logging

# 将上级目录加入路径，支持直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hot_book_quotes_ranking.collector import HotRankingCollector


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # 抑制第三方库的过多日志
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="热门短视频平台 书单/金句类热榜 Top50 采集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                     采集所有平台的热榜数据
  python main.py --filter            只保留书单/金句类内容
  python main.py --output ./mydata   指定输出目录
  python main.py --top 20            每个平台取前20条
  python main.py -v                  显示详细日志
        """,
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help="只保留书单/金句类相关内容",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出目录路径（默认为项目下的output目录）",
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=50,
        help="每个平台获取的数量上限（默认50）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志",
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    logger.info("🚀 热门短视频平台书单/金句热榜采集工具启动")
    logger.info(f"   每平台获取Top: {args.top}")
    logger.info(f"   仅书单/金句类: {'是' if args.filter else '否'}")
    if args.output:
        logger.info(f"   输出目录: {args.output}")
    logger.info("")

    # 创建采集器
    collector = HotRankingCollector(
        output_dir=args.output,
        top_n=args.top,
    )

    try:
        # 执行采集
        saved_files = collector.run(filter_only_book_quotes=args.filter)

        # 打印摘要
        logger.info("")
        logger.info(collector.get_summary())
        logger.info("")

        if saved_files:
            logger.info("✅ 采集完成！生成的文件:")
            for name, path in saved_files.items():
                logger.info(f"   📁 {name}: {path}")
        else:
            logger.warning("⚠️ 未生成任何文件")

    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断采集")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 采集过程出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
