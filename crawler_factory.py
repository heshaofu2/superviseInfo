from typing import Dict, Type
from base_crawler import BaseCrawler
from sichuan_fgw_crawler import SichuanFGWCrawler
import logging


class CrawlerFactory:
    """爬虫工厂类，用于创建不同网站的爬虫实例"""

    # 注册的爬虫类
    _crawlers: Dict[str, Type[BaseCrawler]] = {
        'sichuan_fgw': SichuanFGWCrawler,
        # 后续可以添加其他网站的爬虫
        # 'other_site': OtherSiteCrawler,
    }

    @classmethod
    def create_crawler(cls, crawler_type: str) -> BaseCrawler:
        """创建指定类型的爬虫实例"""
        if crawler_type not in cls._crawlers:
            available_types = list(cls._crawlers.keys())
            raise ValueError(f"不支持的爬虫类型: {crawler_type}，可用类型: {available_types}")

        crawler_class = cls._crawlers[crawler_type]
        logging.info(f"创建 {crawler_type} 爬虫实例")
        return crawler_class()

    @classmethod
    def register_crawler(cls, crawler_type: str, crawler_class: Type[BaseCrawler]):
        """注册新的爬虫类型"""
        cls._crawlers[crawler_type] = crawler_class
        logging.info(f"注册新的爬虫类型: {crawler_type}")

    @classmethod
    def get_available_crawlers(cls) -> list:
        """获取所有可用的爬虫类型"""
        return list(cls._crawlers.keys())

    @classmethod
    def get_crawler_info(cls, crawler_type: str) -> Dict[str, str]:
        """获取爬虫信息"""
        if crawler_type not in cls._crawlers:
            return {}

        crawler = cls.create_crawler(crawler_type)
        return {
            'type': crawler_type,
            'name': crawler.get_crawler_name(),
            'base_url': crawler.get_base_url()
        }