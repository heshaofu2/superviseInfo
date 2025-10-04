#!/usr/bin/env python3
"""
运行脚本 - 支持不同运行模式
"""
import argparse
import logging
import sys
from crawler_manager import run_crawler
from storage import DataStorage


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('crawler.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def show_status():
    """显示所有数据源状态"""
    storage = DataStorage()
    summaries = storage.get_all_summaries()

    if not summaries:
        print("没有找到任何数据源")
        return

    print("\n=== 数据源状态 ===")
    for i, summary in enumerate(summaries, 1):
        print(f"{i}. {summary['url'][:80]}...")
        print(f"   总计: {summary['total_items']} 项")
        print(f"   最后更新: {summary['last_updated']}")
        print()


def export_data():
    """导出数据到CSV"""
    storage = DataStorage()
    summaries = storage.get_all_summaries()

    if not summaries:
        print("没有找到任何数据源")
        return

    print("选择要导出的数据源:")
    for i, summary in enumerate(summaries, 1):
        print(f"{i}. {summary['url'][:80]}... ({summary['total_items']} 项)")

    try:
        choice = int(input("\n请输入序号: ")) - 1
        if 0 <= choice < len(summaries):
            url = summaries[choice]['url']
            filename = f"export_{choice + 1}.csv"
            storage.export_to_csv(url, filename)
            print(f"数据已导出到: {filename}")
        else:
            print("无效的选择")
    except ValueError:
        print("请输入有效数字")


def main():
    parser = argparse.ArgumentParser(description="四川省发改委网站监督信息爬虫")
    parser.add_argument("--mode", "-m",
                       choices=["crawl", "status", "export"],
                       default="crawl",
                       help="运行模式: crawl(爬取), status(状态), export(导出)")

    args = parser.parse_args()

    if args.mode == "crawl":
        setup_logging()
        print("开始爬取数据...")
        run_crawler()
    elif args.mode == "status":
        show_status()
    elif args.mode == "export":
        export_data()


if __name__ == "__main__":
    main()