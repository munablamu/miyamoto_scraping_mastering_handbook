"""
Amazon商品情報を取得する
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

COLLECTION_NAME = 'amazon'
SLEEP_TIME = 3


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = 'https://www.amazon.co.jp/s?k=novation'
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        page_num = 1
        item_urls = list()
        while True:
            urls = get_item_urls(driver)
            if len(urls) == 0:
                break
            time.sleep(SLEEP_TIME)
            item_urls.extend(urls)
            page_num += 1
            driver.get(target_url + f'&page={page_num}')

        # スクレイピング料を削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                item_info = get_item_info(driver, key)
                print(item_info)
                collection.insert_one(item_info)

    except Exception as e:
        print(f'Error: {e}')

    finally:
        driver.save_screenshot('output/last_screen.png')
        driver.quit()


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    all_item_elements = driver.find_elements(By.CSS_SELECTOR, '.sg-col-4-of-12.s-result-item.s-asin.sg-col-4-of-16.sg-col.s-widget-spacing-small.sg-col-4-of-20')
    removed_item_elements = [i for i in all_item_elements
                             if len(i.find_elements(By.CSS_SELECTOR, '.a-row.a-spacing-micro')) == 0]
    a_tag_elements = [i.find_element(By.TAG_NAME, 'a') for i in removed_item_elements]
    hrefs = [i.get_attribute('href') for i in a_tag_elements]
    item_urls = list(set(hrefs))
    return item_urls


def get_item_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する。

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    try:
        result = dict()
        result['site'] = 'Amazon'
        result['url'] = driver.current_url
        result['key'] = key

        title_element = driver.find_element(By.ID, 'title')
        result['title'] = title_element.text

        price_element = driver.find_element(By.CLASS_NAME, 'a-price-whole')
        result['price'] = price_element.text

        stock_element = driver.find_element(By.ID, 'availability')
        result['is_stock'] = 'In Stock' in stock_element.text

        description_element = driver.find_element(By.ID, 'feature-bullets')
        result['description'] = description_element.text

    except:
        print(f'詳細な情報を取得できませんでした:{driver.current_url}')

    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す。

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    return url.split('/')[-2]


if __name__ == '__main__':
    main()
