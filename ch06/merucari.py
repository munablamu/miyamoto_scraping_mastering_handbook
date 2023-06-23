"""
メルカリのデータを取得する
"""
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 3
COLLECTION_NAME = 'merucari'


def main():
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = 'https://jp.mercari.com/search?keyword=novation&t1_category_id=1328&status=on_sale&category_id=79'
        driver.get(target_url)
        time.sleep(5)

        page_num = 0
        item_urls = list()
        while True:
            urls = get_item_urls(driver)
            time.sleep(SLEEP_TIME)
            if len(urls) < 1: # 最終ページ
                break
            else:
                item_urls.extend(urls)
                page_num += 1
                update_page_num(driver, target_url, page_num)

        #スクレイピング量削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)
            print(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                driver.get(i_url)
                time.sleep(5)
                item_info = get_item_info(driver, key)
                collection.insert_one(item_info)

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, target_url: str, page_num: int) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        target_url (str): 基底のURL
        page_num (int): 次ページの番号
    """
    page_option = f'&page_token=v1%3A{page_num}'
    driver.get(target_url + page_option)


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    a_tag_elements = driver.find_elements(By.TAG_NAME, 'a')
    if len(a_tag_elements) == 0:
        return list()
    hrefs = [i.get_attribute('href') for i in a_tag_elements]
    item_urls = [i for i in hrefs if 'item' in i]
    return item_urls


def get_item_info(driver: WebDriver, key: str) -> dict:
    """
    詳細情報からアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    result = dict()
    driver.save_screenshot('output/screen.png')
    result['key'] = key
    result['datetime'] = datetime.datetime.now().strftime('%y/%m/%d %H:%M:%S')
    result['description'] = driver.find_element(By.CSS_SELECTOR, 'pre').text
    result['title'] = driver.find_element(By.TAG_NAME, 'h1').text
    price_section_element = driver.find_element(By.CSS_SELECTOR, '.sc-da871d51-8.jOzGgE')
    result['price'] = price_section_element.text.replace('¥', '')
    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    return url.split('/')[-1]


if __name__ == '__main__':
    main()
