"""
ライブドアニュースを取得
"""
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 10
FILE_DIR = 'output'
COLLECTION_NAME = 'livedoor'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        if not os.path.exists(FILE_DIR):
            os.makedirs(FILE_DIR)

        target_url = 'https://news.livedoor.com/'
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        article_urls = list()

        urls = get_news_url(driver)
        # データ量を減らす
        urls = urls[:4]
        article_urls.extend(urls)
        article_urls = set([i.replace('topics', 'article') for i in article_urls])

        results = list()
        for i_url in article_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                item_info = get_data(driver, key)
                collection.insert_one(item_info)

    finally:
        driver.quit()


def get_data(driver: WebDriver, key: str) -> dict:
    """
    詳細ページから記事の情報を取得する。

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: 記事の詳細
    """
    result = dict()
    result['url'] = driver.current_url
    result['key'] = key
    result['title'] = driver.find_element(By.CLASS_NAME, 'articleTtl').text
    result['date'] = driver.find_element(By.CLASS_NAME, 'articleDate').text
    result['vender'] = driver.find_element(By.CLASS_NAME, 'articleVender').text
    result['file_name'] = f'livedoor_{result["key"]}.txt'

    article_text = str()
    while True:
        i_article_text = driver.find_element(By.CLASS_NAME, 'articleBody').text
        article_text = article_text + '\n' + i_article_text

        pager_elements = driver.find_elements(By.CLASS_NAME, 'next')
        if pager_elements:
            next_li_element = pager_elements[0].find_elements(By.CLASS_NAME, 'next')
            if next_li_element:
                next_url = next_li_element.find_element(By.TAG_NAME, 'a').click()
                time.sleep(SLEEP_TIME)
            else:
                break
        else:
            break

    file_path = os.path.join(FILE_DIR, result['file_name'])
    with open(file_path, 'w') as f:
        f.write(article_text)

    return result


def get_news_url(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    a_elements = driver.find_elements(By.CLASS_NAME, 'rewrite_ab')
    return [i.get_attribute('href') for i in a_elements]


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
