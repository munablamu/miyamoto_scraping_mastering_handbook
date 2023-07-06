import re

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from syuwa.items import EBook
from syuwa.utils import MongoMixin


class EBookCrawlSpider(CrawlSpider, MongoMixin):
    name = 'ebook_crawl'
    allowed_domains = ['www.shuwasystem.co.jp']
    start_urls = ['https://www.shuwasystem.co.jp/search/index.php?search_genre=13273']

    rules = (
        Rule(LinkExtractor(restrict_css='.pagingWrap .right .next'), follow=True),
        Rule(LinkExtractor(allow=r'/book/\d+.html$'),
                           callback='parse_article',
                           process_request='process_request_before_parse_article')
    )


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.setup_mongo(
            mongodb_uri=crawler.settings.get('MONGODB_URI'),
            mongodb_database=crawler.settings.get('MONGODB_DATABASE'),
            mongodb_collection=cls.name
        )
        return spider


    def process_request_before_parse_article(self, request, response):
        key = self._extract_key(request.url)
        if not self.collection.find_one({'key': key}):
            return request
        else:
            self.logger.info(f'URL {request.url} already processed, skipping')


    def parse_article(self, response):
        item = EBook()
        item['key'] = self._extract_key(response.url)
        item['title'] = response.css('.titleWrap .titleType1::text').get().strip()
        item['price'] = int(response.css('.right > table th:contains("定価") + td::text').get().replace('円', ''))
        item['author'] = response.css('.right > table th:contains("著者") + td > a::text').get()
        item['describe'] = response.css('#bookSample::text').get().strip()
        yield item


    def _extract_key(self, url: str) -> str:
        m = re.search(r'/([^/]+).html', url)
        return m.group(1)
