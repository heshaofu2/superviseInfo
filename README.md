# 多网站监督信息爬虫系统

本程序是一个可扩展的多网站爬虫系统，目前支持四川省发改委网站的搜索结果爬取，并提供了抽象架构来支持其他网站的爬虫实现。

## 功能特点

- 🔍 自动爬取多个搜索关键词的结果
- 🏗️ **模块化抽象架构**，支持多网站扩展
- 💾 本地文件存储，支持增量更新
- 📊 详细的数据统计和历史记录
- 🔄 自动去重，避免重复数据
- 📝 完整的日志记录
- 🛡️ 错误重试机制
- ⚙️ **JSON配置文件**管理，支持URL分组和爬虫类型配置

## 安装依赖

```bash
pip install -r requirements.txt
```

## 系统架构

### 抽象架构设计

本系统采用抽象工厂模式，支持多种网站的爬虫实现：

- **BaseCrawler**: 抽象基类，定义通用爬虫接口
- **CrawlerFactory**: 爬虫工厂，管理不同网站的爬虫实例
- **具体实现**: 如SichuanFGWCrawler（四川省发改委）

### 配置文件说明

`urls_config.json` 支持为每个搜索URL配置：
- `name`: 搜索配置名称
- `description`: 描述信息
- `url`: 搜索URL
- `crawler_type`: 爬虫类型（如"sichuan_fgw"）
- `enabled`: 是否启用

### 项目结构

```
superviseInfo/
├── main.py                      # 主程序入口
├── base_crawler.py              # 爬虫抽象基类
├── sichuan_fgw_crawler.py       # 四川省发改委爬虫实现
├── crawler_factory.py           # 爬虫工厂
├── example_other_site_crawler.py # 其他网站爬虫示例
├── storage.py                   # 数据存储管理
├── run.py                      # 多模式运行脚本
├── urls_config.json            # URL配置文件
├── requirements.txt            # 依赖包列表
├── README.md                   # 使用说明
├── crawler.log                 # 运行日志
└── data/                      # 数据存储目录
    ├── {hash}.json            # 搜索结果数据
    └── {hash}_history.json    # 历史记录
```

## 扩展支持其他网站

### 1. 创建新的爬虫类

```python
from base_crawler import BaseCrawler

class MyWebsiteCrawler(BaseCrawler):
    def get_base_url(self) -> str:
        return 'https://mywebsite.com'

    def get_crawler_name(self) -> str:
        return 'my_website'

    def extract_search_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        # 实现具体的结果提取逻辑
        pass

    def build_next_page_url(self, base_url: str, page_num: int) -> Optional[str]:
        # 实现分页URL构造逻辑
        pass
```

### 2. 注册到爬虫工厂

```python
from crawler_factory import CrawlerFactory
CrawlerFactory.register_crawler('my_website', MyWebsiteCrawler)
```

### 3. 在配置文件中添加URL

```json
{
  "search_urls": {
    "my_search": {
      "name": "我的搜索",
      "url": "https://mywebsite.com/search?q=keyword",
      "crawler_type": "my_website",
      "enabled": true
    }
  }
}
```

## 使用方法

### 1. 直接运行
```bash
python main.py
```

### 2. 定期运行（推荐）
可以使用cron或其他定时任务工具定期执行：

```bash
# 每小时运行一次
0 * * * * cd /path/to/project && python main.py

# 每天早上9点运行
0 9 * * * cd /path/to/project && python main.py
```

## 输出结果

### 数据文件
程序会在 `data/` 目录下创建以下文件：
- `{url_hash}.json` - 存储所有搜索结果
- `{url_hash}_history.json` - 存储增量更新历史

### 日志文件
- `crawler.log` - 详细的运行日志

### 数据格式示例
```json
{
  "url": "搜索URL",
  "last_updated": "2024-01-01T10:00:00",
  "total_count": 150,
  "items": [
    {
      "title": "文档标题",
      "url": "文档链接"
    }
  ]
}
```

## 配置说明

可以在 `config.py` 中修改配置：

### 搜索URL配置
```python
SEARCH_URLS = [
    {
        "name": "关键词名称",
        "url": "搜索URL"
    }
]
```

### 爬虫配置
- `max_retries`: 最大重试次数
- `request_timeout`: 请求超时时间
- `delay_between_requests`: 请求间隔
- `max_pages`: 最大爬取页数

## 监控和维护

### 查看运行状态
程序运行时会输出：
- 总数据项数量
- 本次新增项数量
- 各搜索源的状态

### 数据导出
可以使用以下代码导出CSV格式：

```python
from storage import DataStorage

storage = DataStorage()
storage.export_to_csv(url, "output.csv")
```

## 注意事项

1. **遵守robots.txt**: 程序设置了合理的请求间隔，请勿过于频繁运行
2. **网络稳定性**: 建议在网络稳定的环境下运行
3. **存储空间**: 长期运行需要定期清理日志文件
4. **网站变更**: 如果网站结构发生变化，可能需要更新解析逻辑

## 故障排除

### 常见问题

1. **无法获取结果**
   - 检查网络连接
   - 确认目标网站是否可访问
   - 查看日志文件获取详细错误信息

2. **解析结果为空**
   - 网站结构可能发生变化
   - 需要更新CSS选择器逻辑

3. **文件权限错误**
   - 确保程序有权限创建和写入data目录
   - 检查磁盘空间是否充足

### 日志分析
程序会记录详细的运行日志，包括：
- 请求状态
- 解析结果
- 错误信息
- 数据保存状态

查看最近的日志：
```bash
tail -f crawler.log
```

## 项目结构

```
superviseInfo/
├── main.py           # 主程序入口
├── crawler.py        # 爬虫核心逻辑
├── storage.py        # 数据存储管理
├── config.py         # 配置文件
├── requirements.txt  # 依赖包列表
├── README.md         # 使用说明
├── crawler.log       # 运行日志
└── data/            # 数据存储目录
    ├── {hash}.json  # 搜索结果数据
    └── {hash}_history.json  # 历史记录
```