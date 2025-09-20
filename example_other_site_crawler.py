from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
from base_crawler import BaseCrawler


class ExampleOtherSiteCrawler(BaseCrawler):
    """示例：其他网站爬虫实现

    这是一个示例实现，展示如何为其他网站创建爬虫
    """

    def get_base_url(self) -> str:
        return 'https://example.gov.cn'

    def get_crawler_name(self) -> str:
        return 'example_other_site'

    def get_page_encoding(self, response) -> str:
        """重写页面编码检测（如果需要）"""
        # 某些网站可能使用不同的编码
        return 'gbk'  # 或其他编码

    def extract_search_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """从其他网站搜索结果页面提取标题和链接"""
        results = []

        # 示例：其他网站可能使用不同的HTML结构
        # 这里展示一个通用的提取方法

        # 方法1: 查找特定的结果容器
        result_containers = soup.select('.result-item, .search-result, .content-item')

        if result_containers:
            logging.info(f"找到 {len(result_containers)} 个搜索结果容器")

            for container in result_containers:
                # 查找标题链接
                title_link = container.find('a', href=True)
                if title_link:
                    href = title_link.get('href', '')
                    title = title_link.get('title') or title_link.get_text().strip()

                    # 清理标题
                    title = self.clean_title(title)

                    if title and href and self._is_valid_result(title, href):
                        full_url = self.normalize_url(href)
                        results.append({
                            'title': title,
                            'url': full_url
                        })

        # 方法2: 如果没有找到特定容器，尝试通用方法
        if not results:
            logging.info("未找到特定容器，尝试通用链接提取")
            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href', '')
                title = link.get('title') or link.get_text().strip()

                if self._is_valid_result(title, href):
                    full_url = self.normalize_url(href)
                    results.append({
                        'title': title,
                        'url': full_url
                    })

        # 去重
        unique_results = self._deduplicate_results(results)
        logging.info(f"提取到 {len(unique_results)} 个唯一结果")
        return unique_results

    def _is_valid_result(self, title: str, href: str) -> bool:
        """判断是否为有效的结果链接"""
        if not title or len(title) < 5:
            return False

        # 过滤掉无效链接
        invalid_keywords = ['javascript', '#', 'mailto']
        for keyword in invalid_keywords:
            if keyword in href.lower():
                return False

        # 过滤掉导航文本
        invalid_titles = ['首页', '返回', '上一页', '下一页', '更多', '导航']
        for keyword in invalid_titles:
            if keyword in title:
                return False

        # 检查是否为内容页面（根据具体网站调整）
        if any(pattern in href for pattern in ['/article/', '/news/', '/detail/', '.html']):
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
        """构造下一页URL - 根据具体网站的分页方式实现"""

        # 示例1: 使用page参数
        if 'page=' in base_url:
            import re
            return re.sub(r'page=\d+', f'page={page_num}', base_url)

        # 示例2: 使用p参数
        elif 'p=' in base_url:
            import re
            return re.sub(r'p=\d+', f'p={page_num}', base_url)

        # 示例3: 添加页码参数
        else:
            separator = '&' if '?' in base_url else '?'
            return f"{base_url}{separator}page={page_num}"

    def setup_session(self):
        """重写会话设置（如果需要特殊配置）"""
        super().setup_session()

        # 示例：某些网站可能需要特殊的请求头
        self.session.headers.update({
            'Referer': self.get_base_url(),
            'X-Requested-With': 'XMLHttpRequest',  # 如果是AJAX请求
        })


# 使用示例：注册新的爬虫类型
def register_example_crawler():
    """注册示例爬虫到工厂"""
    from crawler_factory import CrawlerFactory
    CrawlerFactory.register_crawler('example_other_site', ExampleOtherSiteCrawler)
    logging.info("已注册示例爬虫类型: example_other_site")


if __name__ == "__main__":
    # 测试示例爬虫
    register_example_crawler()

    from crawler_factory import CrawlerFactory
    crawler = CrawlerFactory.create_crawler('example_other_site')
    print(f"爬虫名称: {crawler.get_crawler_name()}")
    print(f"基础URL: {crawler.get_base_url()}")
    print(f"可用爬虫类型: {CrawlerFactory.get_available_crawlers()}")