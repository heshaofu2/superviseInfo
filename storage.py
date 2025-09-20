import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple
import logging


class DataStorage:
    """数据存储和增量更新管理"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_name(self, url: str, source_name: str = None) -> str:
        """生成文件名，优先使用source_name，否则使用URL哈希"""
        if source_name:
            # 清理文件名，移除特殊字符
            import re
            clean_name = re.sub(r'[^\w\u4e00-\u9fff\-_]', '_', source_name)
            return clean_name
        else:
            # 兼容旧版本，使用URL哈希
            return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_data_file(self, url: str, source_name: str = None) -> str:
        """获取数据文件路径"""
        file_name = self._get_file_name(url, source_name)
        return os.path.join(self.data_dir, f"{file_name}.json")

    def _get_history_file(self, url: str, source_name: str = None) -> str:
        """获取历史记录文件路径"""
        file_name = self._get_file_name(url, source_name)
        return os.path.join(self.data_dir, f"{file_name}_history.json")

    def load_existing_data(self, url: str, source_name: str = None) -> Dict:
        """加载已存在的数据"""
        data_file = self._get_data_file(url, source_name)
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"加载数据文件失败: {e}")
                return {}
        return {}

    def save_data(self, url: str, results: List[Dict[str, str]], source_key: str = None, source_name: str = None) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        保存数据并返回新增的结果
        返回: (所有结果, 新增结果)
        """
        existing_data = self.load_existing_data(url, source_name)
        existing_items = existing_data.get('items', [])

        # 创建已存在项目的集合（基于URL去重）
        existing_urls = {item['url'] for item in existing_items}

        # 找出新增的项目
        new_items = [item for item in results if item['url'] not in existing_urls]

        # 合并所有项目（去重）
        all_items = existing_items + new_items

        # 保存更新后的数据
        updated_data = {
            'url': url,
            'source_key': source_key,
            'source_name': source_name,
            'last_updated': datetime.now().isoformat(),
            'total_count': len(all_items),
            'items': all_items
        }

        data_file = self._get_data_file(url, source_name)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        # 记录历史
        self._save_history(url, new_items, source_key, source_name)

        logging.info(f"保存数据完成: 总计 {len(all_items)} 项，新增 {len(new_items)} 项")
        return all_items, new_items

    def _save_history(self, url: str, new_items: List[Dict[str, str]], source_key: str = None, source_name: str = None):
        """保存历史记录"""
        if not new_items:
            return

        history_file = self._get_history_file(url, source_name)
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'source_key': source_key,
            'source_name': source_name,
            'new_items_count': len(new_items),
            'new_items': new_items
        }

        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                logging.error(f"加载历史文件失败: {e}")

        history.append(history_entry)

        # 只保留最近50次记录
        if len(history) > 50:
            history = history[-50:]

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def get_summary(self, url: str, source_name: str = None) -> Dict:
        """获取数据摘要"""
        data = self.load_existing_data(url, source_name)
        history_file = self._get_history_file(url, source_name)

        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                pass

        return {
            'url': url,
            'source_key': data.get('source_key'),
            'source_name': data.get('source_name'),
            'total_items': data.get('total_count', 0),
            'last_updated': data.get('last_updated', 'Never'),
            'history_entries': len(history),
            'latest_new_items': history[-1]['new_items_count'] if history else 0
        }

    def export_to_csv(self, url: str, output_file: str):
        """导出数据到CSV文件"""
        import csv
        data = self.load_existing_data(url)
        items = data.get('items', [])

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['标题', '链接地址', '发现时间'])

            for item in items:
                writer.writerow([
                    item['title'],
                    item['url'],
                    item.get('discovered_at', '')
                ])

        logging.info(f"已导出 {len(items)} 条记录到 {output_file}")

    def get_all_summaries(self) -> List[Dict]:
        """获取所有数据源的摘要"""
        summaries = []
        if not os.path.exists(self.data_dir):
            return summaries

        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and not filename.endswith('_history.json'):
                try:
                    filepath = os.path.join(self.data_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        summaries.append({
                            'url': data.get('url', 'Unknown'),
                            'source_key': data.get('source_key'),
                            'source_name': data.get('source_name'),
                            'total_items': data.get('total_count', 0),
                            'last_updated': data.get('last_updated', 'Never')
                        })
                except Exception as e:
                    logging.error(f"读取文件 {filename} 失败: {e}")

        return summaries