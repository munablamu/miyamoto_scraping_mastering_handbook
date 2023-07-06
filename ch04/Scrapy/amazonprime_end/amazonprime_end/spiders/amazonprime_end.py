import time
import logging
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from amazonprime_end.items import AmazonprimeEndItem

JAVASCRIPT_WAIT_TIME = 1

# seleniumのログ出力を抑える。
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)


class AmazonprimeEndSpider(scrapy.Spider):
    name = "amazonprime_end"
    allowed_domains = ["animephilia.net"]
    start_urls = ["https://animephilia.net/amazon-prime-video-expiring-calendar/"]


    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.driver = webdriver.Chrome(ChromeDriverManager().install())


    def start_requests(self):
        for i_url in self.start_urls:
            yield scrapy.Request(i_url, self.parse)


    def parse(self, response):
        self.driver.get(response.url)

        for _ in range(3):
            day_elements = self.driver.find_elements(By.CLASS_NAME, 'day-column')
            for i_day in day_elements:
                day_data = i_day.get_attribute('data-date')
                content_elements = i_day.find_elements(By.CSS_SELECTOR, '.event.upcoming')

                for i_content in content_elements:
                    item = AmazonprimeEndItem()
                    item['day'] = day_data
                    a_element = i_content.find_element(By.CLASS_NAME, 'content-title')
                    item['title'] = a_element.text
                    item['url'] = a_element.get_attribute('href')
                    item['key'] = extract_key(item['url'])

                    yield item

            self._calender_update()


    def closed(self, reason):
        self.driver.quit()


    def _scroll_to_see_element(self, by: str, value: str) -> None:
        """
        要素が見える位置まで画面をスクロールする。

        Args:
            by (str): By.CLASS_NAMEなど
            value (str): 値
        """
        element = self.driver.find_element(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView();", element)


    def _calender_update(self):
        """
        翌週のカレンダーを表示する。
        """
        self._scroll_to_see_element(By.CLASS_NAME, 'next')
        self.driver.find_element(By.CLASS_NAME, 'next').click()
        time.sleep(JAVASCRIPT_WAIT_TIME)


def extract_key(url):
    url_tail = url.split('/')[-1]
    return url_tail.split('?')[0]
