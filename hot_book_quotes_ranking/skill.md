---
name: hot_book_quotes_ranking
version: 1.0.0
title: 热门短视频平台书单/金句热榜采集
description: 一键采集抖音、小红书、微信视频号三大短视频平台的书单/金句类热榜Top50，获取文案内容、标签、热度等数据并格式化存储到本地文件。
author: cmhzt
language: python
python_version: ">=3.7"
license: MIT
tags:
  - 数据采集
  - 热榜
  - 短视频
  - 书单
  - 金句
  - 抖音
  - 小红书
  - 微信视频号
  - 爬虫
---

# Skill: hot_book_quotes_ranking

## 概述

本 Skill 用于采集国内主流短视频平台（抖音、小红书、微信视频号）的**书单/金句类热榜 Top50** 数据，自动提取文案内容、标签、热度值等信息，并以 JSON + TXT 两种格式输出到本地文件（文件名自带时间戳后缀）。

## 能力（Capabilities）

| 能力 | 描述 |
|:---|:---|
| 多平台热榜采集 | 支持抖音、小红书、微信视频号三大平台 |
| 书单/金句智能识别 | 内置 40+ 关键词，自动标记书单/金句类内容 |
| 多数据源容灾 | 第三方API → TopHub → 网页爬取 → 兜底数据，四级降级 |
| 格式化存储 | JSON（分平台+汇总）+ TXT（人类可读），带时间戳命名 |
| 反爬能力 | 随机UA、请求间隔、自动重试、SSL容错 |

## 输入（Inputs）

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|:---|:---|:---:|:---|:---|
| `output_dir` | `str` | 否 | `./output` | 输出目录路径 |
| `top_n` | `int` | 否 | `50` | 每个平台获取的热榜条数上限 |
| `filter_only_book_quotes` | `bool` | 否 | `False` | 是否只保留书单/金句类内容 |

### 命令行参数

```bash
python3 -m hot_book_quotes_ranking.main [OPTIONS]
```

| 参数 | 简写 | 描述 |
|:---|:---|:---|
| `--filter` | - | 只保留书单/金句类内容 |
| `--output` | `-o` | 指定输出目录 |
| `--top` | `-n` | 每平台获取条数 |
| `--verbose` | `-v` | 显示详细日志 |

## 输出（Outputs）

### 文件输出

| 文件 | 格式 | 描述 |
|:---|:---|:---|
| `{平台名}_书单金句热榜_{YYYYMMDDHH}.json` | JSON | 单平台数据（每平台一个） |
| `全平台_书单金句热榜_{YYYYMMDDHH}.json` | JSON | 三平台汇总数据 |
| `全平台_书单金句热榜_{YYYYMMDDHH}.txt` | TXT | 三平台汇总（人类可读格式） |

### 单条数据结构

```json
{
  "rank": 1,
  "title": "热榜标题",
  "hot_value": "1000w",
  "content": "文案内容",
  "tags": ["标签1", "标签2"],
  "author": "作者名",
  "likes": "100w",
  "url": "https://...",
  "cover": "https://...",
  "source": "平台-数据源",
  "is_book_quote": true
}
```

| 字段 | 类型 | 描述 |
|:---|:---|:---|
| `rank` | `int` | 排名序号 |
| `title` | `str` | 热榜标题 |
| `hot_value` | `str` | 热度值 |
| `content` | `str` | 文案/描述内容 |
| `tags` | `list[str]` | 标签列表 |
| `author` | `str` | 作者/发布者 |
| `likes` | `str` | 点赞数 |
| `url` | `str` | 原始链接 |
| `cover` | `str` | 封面图片URL |
| `source` | `str` | 数据来源标识 |
| `is_book_quote` | `bool` | 是否为书单/金句类 |

## 依赖（Dependencies）

### Python 包

| 包名 | 版本要求 | 用途 |
|:---|:---|:---|
| `requests` | >= 2.28.0 | HTTP 请求 |
| `beautifulsoup4` | >= 4.12.0 | HTML 解析 |
| `lxml` | >= 4.9.0 | XML/HTML 解析引擎 |
| `fake-useragent` | >= 1.4.0 | 随机 User-Agent |

### 外部服务（可选，自动降级）

| 服务 | 用途 | 是否必须 |
|:---|:---|:---:|
| vvhan API | 第三方聚合热榜数据 | 否 |
| TopHub 今日热榜 | 备用热榜数据源 | 否 |
| 各平台网页 | 直接爬取 | 否 |

> 所有外部服务均为可选，网络不可用时自动降级为兜底示例数据。

## 环境变量（可选）

| 变量名 | 描述 |
|:---|:---|
| `DOUYIN_COOKIE` | 抖音 Cookie（获取更完整数据） |
| `XHS_COOKIE` | 小红书 Cookie |
| `WEIXIN_VIDEO_COOKIE` | 微信视频号 Cookie |

## 快速使用

### 命令行

```bash
# 安装依赖
pip install -r requirements.txt

# 采集所有平台 Top50
python3 -m hot_book_quotes_ranking.main

# 只保留书单/金句类，每平台取30条
python3 -m hot_book_quotes_ranking.main --filter --top 30
```

### 代码调用

```python
from hot_book_quotes_ranking import HotRankingCollector

collector = HotRankingCollector(top_n=50)
saved_files = collector.run(filter_only_book_quotes=False)
print(collector.get_summary())
```

## API 接口

### `HotRankingCollector(output_dir=None, top_n=50)`

主采集器类。

| 方法 | 返回值 | 描述 |
|:---|:---|:---|
| `run(filter_only_book_quotes=False)` | `Dict[str, str]` | 一键运行：采集→筛选→保存 |
| `collect_all()` | `Dict[str, List]` | 采集全部平台 |
| `collect_douyin()` | `List[Dict]` | 采集抖音 |
| `collect_xiaohongshu()` | `List[Dict]` | 采集小红书 |
| `collect_weixin_video()` | `List[Dict]` | 采集微信视频号 |
| `save_results()` | `Dict[str, str]` | 保存结果到文件 |
| `filter_book_quote_items()` | `Dict[str, List]` | 筛选书单/金句类内容 |
| `get_summary()` | `str` | 获取结果摘要 |

## 数据采集流程

```
采集开始
  │
  ├── 抖音 ──→ vvhan API ──→ TopHub ──→ 网页爬取 ──→ 兜底数据
  │                                                      │
  ├── (间隔 1~2s)                                         │
  │                                                      │
  ├── 小红书 ──→ vvhan API ──→ TopHub ──→ 网页爬取 ──→ 兜底数据
  │                                                      │
  ├── (间隔 1~2s)                                         │
  │                                                      │
  └── 微信视频号 ──→ vvhan API ──→ TopHub ──→ 网页爬取 ──→ 兜底数据
                                                         │
  ┌──────────────────────────────────────────────────────┘
  │
  ├── [可选] 关键词筛选 → 标记书单/金句类内容
  │
  ├── 输出 JSON（分平台 + 汇总）
  │
  └── 输出 TXT（人类可读汇总）
```

## 项目文件结构

```
hot_book_quotes_ranking/
├── __init__.py          # 包入口，导出 HotRankingCollector
├── main.py              # CLI 入口
├── collector.py         # 主采集器（调度/筛选/保存）
├── crawlers.py          # 各平台爬虫实现
├── config.py            # 全局配置
├── utils.py             # 工具函数
├── requirements.txt     # Python 依赖
├── skill.md             # Skill 元数据描述（本文件）
├── README.md            # 项目详细文档
└── output/              # 数据输出目录（自动创建）
```

## 注意事项

1. 本工具仅供学习交流，请遵守各平台服务条款及相关法律法规。
2. 所有外部数据源均为公开渠道，不涉及用户隐私数据。
3. 请合理控制采集频率，建议每小时不超过 1 次。
4. 网络不可用时会自动降级为兜底示例数据，输出文件中会标注数据来源。
