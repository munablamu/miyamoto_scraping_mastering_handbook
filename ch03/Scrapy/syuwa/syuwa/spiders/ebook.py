import re

import scrapy

from syuwa.items import EBook


class EbookSpider(scrapy.Spider):
    name = "ebook"
    allowed_domains = ["www.shuwasystem.co.jp"]
    start_urls = ["https://www.shuwasystem.co.jp/search/index.php?search_genre=13273"]


    def parse(self, response):
        bookwrap_element = response.css('.bookWrap')
        for ttl_element in bookwrap_element.css('.ttl'):
            url = ttl_element.css('a::attr("href")').get()
            yield response.follow(url, self.parse_article)

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
