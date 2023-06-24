"""
秀和システムのデータを取得する
"""

import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME  = 1
COLLECTION_NAME = 'syuwa'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())

        page_num = 1
        item_urls = list()
        while True:
            update_page_num(driver, page_num)
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(driver)
            print(urls)
            item_urls.extend(urls)
            if is_last_page(driver):
                break
            page_num += 1

        for url in item_urls:
            key = extract_key(url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                driver.get(url)
                time.sleep(SLEEP_TIME)
                item_info = get_item_info(driver, key)
                collection.insert_one(item_info)

            print(item_info)

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, page_num: int) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次ページの番号
    """
    base_url = 'https://www.shuwasystem.co.jp/search/index.php?search_genre=13273&c=1'
    page_option = f'&page={page_num}'
    next_url = base_url + page_option
    driver.get(next_url)


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    bookwrap_element = driver.find_element(By.CLASS_NAME, 'bookWrap')
    ttl_elements = bookwrap_element.find_elements(By.CLASS_NAME, 'ttl')
    a_elements = [i.find_element(By.TAG_NAME, 'a') for i in ttl_elements]
    return [i.get_attribute('href') for i in a_elements]


def get_item_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): アイテムのキー(ISBN)

    Returns:
        dict: アイテムの情報
    """
    result = dict()
    result['key'] = key
    result['title'] = driver.find_element(By.CLASS_NAME, 'titleWrap').text
    result['price'] = driver.find_element(By.XPATH, '//*[@id="main"]/div[3]/div[2]/table/tbody/tr[6]/td').text
    result['author'] = driver.find_element(By.CSS_SELECTOR, '#main > div.detail > div.right > table > tbody > tr:nth-child(1) > td > a').text
    result['describe'] = driver.find_element(By.ID, 'bookSample').text
    return result


def is_last_page(driver: WebDriver) -> bool:
    """
    一覧ページの最後のページかどうかを確認する

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    pagingWrap_element = driver.find_element(By.CLASS_NAME, 'pagingWrap')
    paging_text = pagingWrap_element.find_element(By.CLASS_NAME, 'right').text
    return not '次' in paging_text


def extract_key(url: str) -> str:
    """
    URLからキー(URLの末尾のISBN)を抜き出す

    Args:
        url (str): 対象URL

    Returns:
        str: キー(ISBN)
    """
    m = re.search(r'/([^/]+).html$', url)
    return m.group(1)


if __name__ == '__main__':
    main()
