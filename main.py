#!/usr/bin/env python3
import logging
import sys
import json
import os
from datetime import datetime
from crawler_factory import CrawlerFactory
from storage import DataStorage


def load_config():
    """加载配置文件"""
    config_file = "urls_config.json"
    if not os.path.exists(config_file):
        logging.error(f"配置文件 {config_file} 不存在")
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        return None


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


def main():
    """主函数"""
    setup_logging()
    logging.info("=" * 60)
    logging.info(f"开始运行爬虫程序 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)

    # 加载配置
    config = load_config()
    if not config:
        logging.error("无法加载配置文件，程序退出")
        return

    # 获取启用的搜索URLs
    search_urls = []
    url_configs = config.get('search_urls', {})

    for key, url_config in url_configs.items():
        if url_config.get('enabled', True):
            search_urls.append({
                'key': key,
                'name': url_config.get('name', key),
                'url': url_config.get('url'),
                'description': url_config.get('description', ''),
                'crawler_type': url_config.get('crawler_type', 'sichuan_fgw')
            })

    if not search_urls:
        logging.error("没有找到启用的搜索URL")
        return

    logging.info(f"加载了 {len(search_urls)} 个搜索配置:")
    for url_config in search_urls:
        logging.info(f"  - {url_config['key']}: {url_config['name']}")

    # 初始化存储
    storage = DataStorage()
    crawler_settings = config.get('crawler_settings', {})

    total_new_items = 0
    total_all_items = 0

    # 处理每个搜索URL
    for i, url_config in enumerate(search_urls, 1):
        key = url_config['key']
        name = url_config['name']
        url = url_config['url']
        crawler_type = url_config['crawler_type']

        logging.info(f"\n处理第 {i}/{len(search_urls)} 个搜索配置...")
        logging.info(f"配置Key: {key}")
        logging.info(f"配置名称: {name}")
        logging.info(f"爬虫类型: {crawler_type}")
        logging.info(f"URL: {url}")

        try:
            # 创建对应类型的爬虫
            crawler = CrawlerFactory.create_crawler(crawler_type)

            # 爬取数据
            max_pages = crawler_settings.get('max_pages', 20)
            results = crawler.crawl_search_url(url, max_pages)
            logging.info(f"爬取到 {len(results)} 个结果")

            if results:
                # 保存数据并获取新增项
                all_items, new_items = storage.save_data(url, results, source_key=key, source_name=name)
                total_all_items += len(all_items)
                total_new_items += len(new_items)

                if new_items:
                    logging.info(f"发现 {len(new_items)} 个新项目:")
                    for item in new_items[:5]:  # 只显示前5个
                        logging.info(f"  - {item['title']}")
                    if len(new_items) > 5:
                        logging.info(f"  ... 还有 {len(new_items) - 5} 个新项目")
                else:
                    logging.info("没有发现新项目")

                # 显示数据摘要
                summary = storage.get_summary(url, source_name=name)
                logging.info(f"数据摘要: 总计 {summary['total_items']} 项，"
                           f"最后更新: {summary['last_updated']}")

            else:
                logging.warning("未能获取到任何结果")

        except Exception as e:
            logging.error(f"处理URL时发生错误: {str(e)}")

        logging.info("-" * 60)

    # 总结
    logging.info("\n" + "=" * 60)
    logging.info("运行总结:")
    logging.info(f"- 处理了 {len(search_urls)} 个搜索配置")
    logging.info(f"- 总计数据项: {total_all_items}")
    logging.info(f"- 本次新增: {total_new_items}")
    logging.info(f"- 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)

    # 显示所有数据源摘要
    all_summaries = storage.get_all_summaries()
    if all_summaries:
        logging.info("\n所有数据源状态:")
        for summary in all_summaries:
            source_name = summary.get('source_name', '未知来源')
            source_key = summary.get('source_key', '未知Key')
            logging.info(f"- [{source_key}] {source_name}")
            logging.info(f"  总计: {summary['total_items']} 项, "
                       f"最后更新: {summary['last_updated']}")


if __name__ == "__main__":
    main()