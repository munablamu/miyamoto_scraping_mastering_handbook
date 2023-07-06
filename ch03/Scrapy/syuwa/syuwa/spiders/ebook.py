import re

import scrapy

from syuwa.items import EBook
from syuwa.utils import MongoMixin


class EbookSpider(scrapy.Spider, MongoMixin):
    name = "ebook"
    allowed_domains = ["www.shuwasystem.co.jp"]
    start_urls = ["https://www.shuwasystem.co.jp/search/index.php?search_genre=13273"]


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.setup_mongo(
            mongodb_uri=crawler.settings.get('MONGODB_URI'),
            mongodb_database=crawler.settings.get('MONGODB_DATABASE'),
            mongodb_collection=cls.name
        )
        return spider


    def parse(self, response):
        bookwrap_element = response.css('.bookWrap')
        for ttl_element in bookwrap_element.css('.ttl'):
            url = ttl_element.css('a::attr("href")').get()

            key = self._extract_key(url)
            if not self.collection.find_one({'key': key}):
                yield response.follow(url, self.parse_article)
            else:
                self.logger.info(f'URL {url} already processed, skipping')

        next_url = self._get_next_page_url(response)
        if next_url:
            yield response.follow(next_url, callback=self.parse)


    def parse_article(self, response):
        item = EBook()
        item['key'] = self._extract_key(response.url)
        item['title'] = response.css('.titleWrap .titleType1::text').get().strip()
        item['price'] = int(response.css('.right > table th:contains("定価") + td::text').get().replace('円', ''))
        item['author'] = response.css('.right > table th:contains("著者") + td > a::text').get()
        item['describe'] = response.css('#bookSample::text').get().strip()
        yield item


    def closed(self, reason):
        self.close_mongo()


    def _extract_key(self, url: str) -> str:
        m = re.search(r'/([^/]+).html', url)
        return m.group(1)


    def _is_last_page(self, response) -> bool:
        pagingWrap_element = response.css('.pagingWrap')
        paging_text = pagingWrap_element.css('.right').get()
        return not '次' in paging_text


    def _get_next_page_url(self, response) -> str:
        pagingWrap_element = response.css('.pagingWrap')
        paging_element = pagingWrap_element.css('.right')
        next_url = paging_element.css('.next::attr("href")').get()
        return next_url
