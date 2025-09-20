from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
from base_crawler import BaseCrawler


class SichuanFGWCrawler(BaseCrawler):
    """四川省发改委网站爬虫实现"""

    def get_base_url(self) -> str:
        return 'https://fgw.sc.gov.cn'

    def get_crawler_name(self) -> str:
        return 'sichuan_fgw'

    def extract_search_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """从四川省发改委搜索结果页面提取标题和链接"""
        results = []

        # 查找搜索结果容器
        result_items = soup.select('.wordGuide')
        if result_items:
            logging.info(f"找到 {len(result_items)} 个搜索结果项")

            for item in result_items:
                # 查找标题链接
                title_link = item.select('.bigTit a')
                if title_link:
                    link_elem = title_link[0]
                    href = link_elem.get('href', '')
                    title = link_elem.get('title') or link_elem.get_text().strip()

                    # 清理标题（移除HTML标签）
                    title = self.clean_title(title)

                    if title and href:
                        full_url = self.normalize_url(href)
                        results.append({
                            'title': title,
                            'url': full_url
                        })

        # 如果没有找到.wordGuide容器，尝试查找所有相关链接
        if not results:
            logging.info("未找到.wordGuide容器，尝试提取所有相关链接")
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                title = link.get('title') or link.get_text().strip()

                # 过滤掉导航链接和无效链接
                if self._is_valid_result_link(title, href):
                    full_url = self.normalize_url(href)
                    results.append({
                        'title': title,
                        'url': full_url
                    })

        # 去重
        unique_results = self._deduplicate_results(results)
        logging.info(f"提取到 {len(unique_results)} 个唯一结果")
        return unique_results

    def _is_valid_result_link(self, title: str, href: str) -> bool:
        """判断是否为有效的结果链接"""
        if not title or len(title) < 10:
            return False

        # 过滤掉导航链接和无效链接
        invalid_keywords = ['javascript', '#', 'mailto']
        for keyword in invalid_keywords:
            if keyword in href.lower():
                return False

        # 过滤掉导航文本
        invalid_titles = ['首页', '返回', '上一页', '下一页', '更多', '导航', '搜索']
        for keyword in invalid_titles:
            if keyword in title:
                return False

        # 检查是否为内容页面
        if '.shtml' in href or 'detail' in href:
            return True

        return False

    def _deduplicate_results(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """去重"""
        seen = set()
        unique_results = []
        for result in results:
            identifier = (result['title'], result['url'])
            if identifier not in seen:
                seen.add(identifier)
                unique_results.append(result)
        return unique_results

    def build_next_page_url(self, base_url: str, page_num: int) -> Optional[str]:
        """构造四川省发改委网站的下一页URL"""
        if 'pageNum=' in base_url:
            # 替换pageNum参数
            import re
            return re.sub(r'pageNum=\d+', f'pageNum={page_num}', base_url)
        else:
            # 添加pageNum参数
            separator = '&' if '?' in base_url else '?'
            return f"{base_url}{separator}pageNum={page_num}"