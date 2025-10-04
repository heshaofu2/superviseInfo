#!/usr/bin/env python3
"""
爬虫管理器 - 核心业务逻辑
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, List
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


def run_crawler(generate_report: bool = True):
    """
    执行爬虫任务

    Args:
        generate_report: 是否生成Markdown报告，默认True
    """
    start_time = datetime.now()
    logging.info("=" * 60)
    logging.info(f"开始运行爬虫程序 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
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
    run_results = []  # 收集每个配置的运行结果

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

        # 记录本配置的结果
        config_result = {
            'key': key,
            'name': name,
            'url': url,
            'crawler_type': crawler_type,
            'crawled_count': 0,
            'new_count': 0,
            'total_count': 0,
            'new_items': [],
            'error': None
        }

        try:
            # 创建对应类型的爬虫
            crawler = CrawlerFactory.create_crawler(crawler_type)

            # 爬取数据
            max_pages = crawler_settings.get('max_pages', 20)
            results = crawler.crawl_search_url(url, max_pages)
            logging.info(f"爬取到 {len(results)} 个结果")
            config_result['crawled_count'] = len(results)

            if results:
                # 保存数据并获取新增项
                all_items, new_items = storage.save_data(url, results, source_key=key, source_name=name)
                total_all_items += len(all_items)
                total_new_items += len(new_items)

                # 记录到config_result
                config_result['new_count'] = len(new_items)
                config_result['total_count'] = len(all_items)
                config_result['new_items'] = new_items

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
            config_result['error'] = str(e)

        # 添加到运行结果列表
        run_results.append(config_result)
        logging.info("-" * 60)

    # 总结
    end_time = datetime.now()
    logging.info("\n" + "=" * 60)
    logging.info("运行总结:")
    logging.info(f"- 处理了 {len(search_urls)} 个搜索配置")
    logging.info(f"- 总计数据项: {total_all_items}")
    logging.info(f"- 本次新增: {total_new_items}")
    logging.info(f"- 完成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
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

    # 生成Markdown报告
    if generate_report:
        run_result = {
            'start_time': start_time,
            'end_time': end_time,
            'total_configs': len(search_urls),
            'total_all_items': total_all_items,
            'total_new_items': total_new_items,
            'results': run_results
        }
        report_path = save_markdown_report(run_result)
        logging.info(f"\n报告已生成: {report_path}")


def generate_markdown_report(run_result: Dict) -> str:
    """
    生成Markdown格式的运行报告

    Args:
        run_result: 运行结果字典，包含所有配置的爬取结果

    Returns:
        Markdown格式的报告内容
    """
    start_time = run_result.get('start_time', datetime.now())
    end_time = run_result.get('end_time', datetime.now())
    total_configs = run_result.get('total_configs', 0)
    total_all_items = run_result.get('total_all_items', 0)
    total_new_items = run_result.get('total_new_items', 0)
    results = run_result.get('results', [])

    # 生成报告
    lines = []
    lines.append(f"# 爬虫运行报告")
    lines.append(f"")
    lines.append(f"**运行时间**: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
    lines.append(f"**处理配置**: {total_configs} 个")
    lines.append(f"**总计数据项**: {total_all_items}")
    lines.append(f"**本次新增**: {total_new_items}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 逐个配置的详细结果
    for i, result in enumerate(results, 1):
        lines.append(f"## {i}. {result['name']} ({result['key']})")
        lines.append(f"")
        lines.append(f"- **URL**: {result['url']}")
        lines.append(f"- **爬虫类型**: {result['crawler_type']}")
        lines.append(f"- **爬取结果数**: {result['crawled_count']}")
        lines.append(f"- **新增数量**: {result['new_count']}")
        lines.append(f"- **总计数据项**: {result['total_count']}")
        lines.append(f"")

        # 显示新增项目
        if result['new_items']:
            lines.append(f"### 本次新增项目 ({len(result['new_items'])} 项)")
            lines.append(f"")
            for j, item in enumerate(result['new_items'], 1):
                lines.append(f"{j}. [{item['title']}]({item['url']})")
            lines.append(f"")
        else:
            lines.append(f"*本次运行未发现新项目*")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    return "\n".join(lines)


def save_markdown_report(run_result: Dict, output_dir: str = "result") -> str:
    """
    保存Markdown报告到文件

    Args:
        run_result: 运行结果字典
        output_dir: 报告输出目录

    Returns:
        报告文件路径
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"result_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    # 生成并保存报告
    report_content = generate_markdown_report(run_result)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logging.info(f"已保存运行报告: {filepath}")
    return filepath
