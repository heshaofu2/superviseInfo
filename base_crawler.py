from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
import logging


class BaseCrawler(ABC):
    """爬虫基础抽象类"""

    def __init__(self):
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """设置会话默认配置"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """获取页面内容并解析为BeautifulSoup对象"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = self.get_page_encoding(response)
                return BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                logging.warning(f"第{attempt + 1}次获取页面失败: {url}, 错误: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logging.error(f"获取页面最终失败: {url}")
                    return None

    def get_page_encoding(self, response) -> str:
        """获取页面编码，子类可以重写"""
        return 'utf-8'

    @abstractmethod
    def extract_search_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """从搜索结果页面提取标题和链接 - 子类必须实现"""
        pass

    @abstractmethod
    def build_next_page_url(self, base_url: str, page_num: int) -> Optional[str]:
        """构造下一页URL - 子类必须实现"""
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        """获取网站基础URL - 子类必须实现"""
        pass

    def normalize_url(self, href: str) -> str:
        """规范化URL"""
        from urllib.parse import urljoin

        if href.startswith('/'):
            return urljoin(self.get_base_url(), href)
        elif not href.startswith('http'):
            return urljoin(self.get_base_url(), href)
        else:
            return href

    def crawl_search_url(self, url: str, max_pages: int = 20) -> List[Dict[str, str]]:
        """爬取单个搜索URL的所有结果"""
        logging.info(f"开始爬取: {url}")

        soup = self.fetch_page(url)
        if not soup:
            return []

        results = self.extract_search_results(soup)

        # 检查是否有分页，尝试获取更多页面
        page_num = 0
        while page_num < max_pages - 1:
            next_page_url = self.build_next_page_url(url, page_num + 1)
            if not next_page_url:
                break

            logging.info(f"获取第 {page_num + 2} 页")
            next_soup = self.fetch_page(next_page_url)
            if not next_soup:
                break

            next_results = self.extract_search_results(next_soup)
            if not next_results:
                break

            results.extend(next_results)
            page_num += 1

            time.sleep(1)  # 避免请求过快

        return results

    def clean_title(self, title: str) -> str:
        """清理标题文本，移除HTML标签等"""
        import re
        if title:
            # 移除HTML标签
            title = re.sub(r'<[^>]+>', '', title)
            title = title.strip()
        return title

    @abstractmethod
    def get_crawler_name(self) -> str:
        """获取爬虫名称 - 子类必须实现"""
        pass