import re

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from syuwa.items import EBook


class EBookCrawlSpider(CrawlSpider):
    name = 'ebook_crawl'
    allowed_domains = ['www.shuwasystem.co.jp']
    start_urls = ['https://www.shuwasystem.co.jp/search/index.php?search_genre=13273']

    rules = (
        Rule(LinkExtractor(allow=r'index\.php\?page=.+$'), follow=True),
        Rule(LinkExtractor(allow=r'/book/\d+.html$'), callback='parse_article')
    )


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
