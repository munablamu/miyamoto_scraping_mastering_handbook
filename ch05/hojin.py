"""
全国法人リストから会社情報を取得
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 3
COLLECTION_NAME = 'hojin'
BASE_URL = 'https://houjin.jp/search?keyword=%E3%82%BD%E3%83%8B%E3%83%83%E3%82%AF&pref_id='


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = BASE_URL
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        page_num = 1
        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(driver)

            if len(urls) == 0:
                break
            else:
                item_urls.extend(urls)
                page_num += 1
                update_page_num(driver, page_num)

        item_urls = item_urls[:5] # データ量を減らす

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                time.sleep(SLEEP_TIME)
                driver.get(i_url)
                item_info = get_item_info(driver, key)
                collection.insert_one(item_info)

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, page_num: int) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次のページ番号
    """
    base_url = BASE_URL
    next_url = base_url + f'&page={page_num}'
    driver.get(next_url)


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    cop_item_elements = driver.find_elements(By.CLASS_NAME, 'c-corp-item')
    return [i.find_element(By.TAG_NAME, 'a').get_attribute('href') for i in cop_item_elements]


def get_item_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する。

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    corp_info_table_element = driver.find_element(By.CLASS_NAME, 'corp-info-table')
    corp_info_html = corp_info_table_element.get_attribute('outerHTML')
    corp_info_df = pd.read_html(corp_info_html)[0]
    keys = corp_info_df.iloc[:, 0].tolist()
    vals = corp_info_df.iloc[:, 1].tolist()
    corp_info = {i_key: i_val for i_key, i_val in zip(keys, vals)}
    corp_info['key'] = key
    return corp_info


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す。

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    return url.split('/')[-1]


if __name__ == '__main__':
    main()
