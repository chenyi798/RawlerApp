import requests
import time
import random
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InfinitePageCrawler:
    def __init__(self, base_url, headers=None, delay_range=(1, 3), max_retries=3):
        """
        初始化爬虫
        
        Args:
            base_url: 基础URL（包含页码占位符）
            headers: 请求头
            delay_range: 延迟时间范围（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 统计数据
        self.stats = {
            'pages_crawled': 0,
            'total_data': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def random_delay(self):
        """随机延迟"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
        return delay
    
    def fetch_page(self, url, retry_count=0):
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                logger.warning(f"请求失败，第{retry_count + 1}次重试: {url}, 错误: {e}")
                time.sleep(2 ** retry_count)  # 指数退避
                return self.fetch_page(url, retry_count + 1)
            else:
                logger.error(f"请求失败，已达最大重试次数: {url}")
                return None
    
    def parse_page(self, html):
        """解析页面内容（需要根据实际情况重写）"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 示例：提取所有链接
        links = []
        for a in soup.find_all('a', href=True):
            links.append({
                'text': a.get_text(strip=True),
                'url': a['href']
            })
        
        # 示例：提取所有文章
        articles = []
        for article in soup.find_all('article'):
            title = article.find('h2')
            content = article.find('div', class_='content')
            if title and content:
                articles.append({
                    'title': title.get_text(strip=True),
                    'content': content.get_text(strip=True)
                })
        
        return {
            'links': links,
            'articles': articles,
            'page_size': len(html)
        }
    
    def has_next_page(self, soup, current_page):
        """检查是否有下一页（需要根据实际情况重写）"""
        # 方法1：检查下一页链接
        next_link = soup.find('a', text='下一页')
        if next_link:
            return True
        
        # 方法2：检查页码按钮
        next_page_btn = soup.find('a', href=f'?page={current_page + 1}')
        if next_page_btn:
            return True
        
        # 方法3：根据内容判断（如果页面为空或404内容）
        content = soup.find('div', id='content')
        if content and len(content.get_text(strip=True)) < 10:
            return False
        
        # 默认继续爬取，直到遇到特定条件
        return True
    
    def save_data(self, data, page_num, format='json'):
        """保存数据到文件"""
        filename = f"page_{page_num}_data.{format}"
        
        if format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif format == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                for item in data.get('articles', []):
                    f.write(f"标题: {item['title']}\n")
                    f.write(f"内容: {item['content']}\n")
                    f.write("-" * 50 + "\n")
        
        logger.info(f"第 {page_num} 页数据已保存到 {filename}")
    
    def crawl(self, start_page=1, max_empty_pages=3, save_interval=10):
        """
        开始爬取
        
        Args:
            start_page: 起始页码
            max_empty_pages: 最大连续空页面数
            save_interval: 数据保存间隔
        """
        self.stats['start_time'] = datetime.now()
        logger.info("开始爬取...")
        
        page_num = start_page
        empty_pages_count = 0
        all_data = []
        
        while True:
            try:
                # 构建URL
                if '{page}' in self.base_url:
                    url = self.base_url.format(page=page_num)
                elif '?page=' in self.base_url:
                    url = self.base_url.replace('page=1', f'page={page_num}')
                else:
                    url = f"{self.base_url}?page={page_num}"
                
                logger.info(f"正在爬取第 {page_num} 页: {url}")
                
                # 获取页面
                html = self.fetch_page(url)
                if not html:
                    empty_pages_count += 1
                    logger.warning(f"第 {page_num} 页获取失败")
                    if empty_pages_count >= max_empty_pages:
                        logger.info(f"连续 {max_empty_pages} 页失败，停止爬取")
                        break
                    page_num += 1
                    continue
                
                # 解析页面
                soup = BeautifulSoup(html, 'html.parser')
                data = self.parse_page(html)
                
                # 检查是否有有效数据
                if not data['articles'] and not data['links']:
                    empty_pages_count += 1
                    logger.warning(f"第 {page_num} 页没有数据")
                    if empty_pages_count >= max_empty_pages:
                        logger.info(f"连续 {max_empty_pages} 页无数据，停止爬取")
                        break
                else:
                    empty_pages_count = 0
                    self.stats['pages_crawled'] += 1
                    self.stats['total_data'] += len(data['articles']) + len(data['links'])
                    all_data.append({
                        'page': page_num,
                        'url': url,
                        'data': data
                    })
                    
                    # 定期保存数据
                    if page_num % save_interval == 0:
                        self.save_data(
                            {'pages': all_data[-save_interval:]},
                            f"batch_{page_num//save_interval}"
                        )
                
                # 检查是否还有下一页
                if not self.has_next_page(soup, page_num):
                    logger.info(f"第 {page_num} 页是最后一页")
                    break
                
                # 添加随机延迟
                delay = self.random_delay()
                logger.debug(f"延迟 {delay:.2f} 秒")
                
                page_num += 1
                
                # 防止无限循环（安全限制）
                if page_num > 10000000:
                    logger.warning("已达到最大爬取页数限制（10000000页）")
                    break
                    
            except KeyboardInterrupt:
                logger.info("用户中断爬取")
                break
            except Exception as e:
                logger.error(f"爬取第 {page_num} 页时发生错误: {e}")
                self.stats['errors'] += 1
                page_num += 1
        
        # 保存所有数据
        if all_data:
            self.save_data({'all_data': all_data}, 'final')
        
        self.stats['end_time'] = datetime.now()
        self.print_stats()
    
    def print_stats(self):
        """打印统计信息"""
        duration = self.stats['end_time'] - self.stats['start_time']
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print("\n" + "="*50)
        print("爬取统计信息")
        print("="*50)
        print(f"开始时间: {self.stats['start_time']}")
        print(f"结束时间: {self.stats['end_time']}")
        print(f"总耗时: {int(hours)}小时 {int(minutes)}分钟 {int(seconds)}秒")
        print(f"爬取页数: {self.stats['pages_crawled']}")
        print(f"总数据量: {self.stats['total_data']} 条")
        print(f"错误次数: {self.stats['errors']}")
        print("="*50)


# 使用示例
def example_usage():
    # 示例1：博客网站爬虫
    blog_crawler = InfinitePageCrawler(
        base_url="https://example.com/blog?page={page}",
        delay_range=(1, 2),  # 1-2秒延迟
        max_retries=2
    )
    
    # 重写解析方法（根据实际网站结构调整）
    def custom_parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        for article in soup.find_all('article', class_='post'):
            title = article.find('h2', class_='entry-title')
            content = article.find('div', class_='entry-content')
            date = article.find('time', class_='entry-date')
            
            articles.append({
                'title': title.get_text(strip=True) if title else '',
                'content': content.get_text(strip=True) if content else '',
                'date': date['datetime'] if date and date.has_attr('datetime') else '',
                'url': title.find('a')['href'] if title and title.find('a') else ''
            })
        
        return {
            'articles': articles,
            'page_size': len(html)
        }
    
    # 重写下一页检查方法
    def custom_has_next_page(self, soup, current_page):
        next_button = soup.find('a', class_='next-page')
        return bool(next_button)
    
    # 替换方法
    blog_crawler.parse_page = lambda html: custom_parse(blog_crawler, html)
    blog_crawler.has_next_page = lambda soup, current_page: custom_has_next_page(soup, current_page)
    
    # 开始爬取
    # blog_crawler.crawl(start_page=1)


# 简单用法示例
if __name__ == "__main__":
    # 创建一个简单的演示爬虫
    crawler = InfinitePageCrawler(
        base_url="https://httpbin.org/anything?page={page}",
        delay_range=(0.5, 1.5)
    )
    
    # 简单测试（只爬5页演示）
    print("开始演示爬虫...")
    
    # 模拟爬取几页
    for page in range(1, 6):
        url = crawler.base_url.format(page=page)
        print(f"爬取: {url}")
        
        # 添加延迟
        delay = crawler.random_delay()
        print(f"延迟: {delay:.2f}秒")
        
        # 这里可以添加实际的爬取逻辑
        time.sleep(0.5)
    
    print("演示完成！")


# 针对特定网站的配置示例
def configure_for_specific_site():
    """配置用于特定网站的爬虫"""
    
    # 1. 知乎专栏示例
    zhihu_crawler = InfinitePageCrawler(
        base_url="https://zhuanlan.zhihu.com/api/columns/{专栏名}/articles?limit=10&offset={page}",
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Authorization': 'Bearer your_token_here'  # 如果需要认证
        },
        delay_range=(2, 4)  # 知乎比较敏感，延迟长一些
    )
    
    # 2. 电商网站示例
    ecommerce_crawler = InfinitePageCrawler(
        base_url="https://example.com/products?page={page}",
        delay_range=(1, 2),
        max_retries=5
    )
    
    # 3. 新闻网站示例
    news_crawler = InfinitePageCrawler(
        base_url="https://example.com/news/list_{page}.html",
        delay_range=(0.5, 1),
        max_retries=3
    )
    
    return {
        'zhihu': zhihu_crawler,
        'ecommerce': ecommerce_crawler,
        'news': news_crawler
    }