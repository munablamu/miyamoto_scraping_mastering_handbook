"""
食べログの飲食店データを取得する
"""
import re
import time
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 4
COLLECTION_NAME = 'tabelog'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        base_url = 'https://tabelog.com/tokyo/rstLst/?vs=1&sa=%E6%9D%B1%E4%BA%AC%E9%83%BD&sk=%25E5%2588%2580%25E5%2589%258A%25E9%25BA%25BA&lid=top_navi1&vac_net=&svd=20220822&svt=1900&svps=2&hfc=1&Cat=RC&LstCat=RC03&LstCatD=RC0304&LstCatSD=RC030402&cat_sk=%E5%88%80%E5%89%8A%E9%BA%BA'
        driver.get(base_url)
        time.sleep(SLEEP_TIME)

        page_num = get_pagenum(driver)

        store_urls = list()
        for i in range(page_num-1):
            urls = get_store_url(driver)
            store_urls.extend(urls)
            get_next(driver)
            time.sleep(SLEEP_TIME)

        store_urls = store_urls[:5] # データ量を減らす
        for i_url in store_urls:
            key = extract_key(i_url)

            store_info = collection.find_one({'key': key})
            if not store_info:
                store_info = get_store_info(driver, i_url, key)
                collection.insert_one(store_info)

            print(store_info)

    finally:
        driver.quit()


def get_next(driver: WebDriver) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver): _description_
    """
    pagenation_element = driver.find_elements(By.CLASS_NAME, 'c-pagination__item')[-1]
    pagenation_element.find_element(By.TAG_NAME, 'a').click()


def get_pagenum(driver: WebDriver) -> int:
    """
    一覧ページのページ数をカウントする。

    Args:
        driver (WebDriver):

    Returns:
        int:
    """
    count_elements = driver.find_elements(By.CLASS_NAME, 'c-page-count__num')
    paging_num = int(count_elements[1].text)
    total_num = int(count_elements[2].text)
    return math.ceil(total_num / paging_num)


def get_store_url(driver: WebDriver) -> list:
    """
    一覧ページからURLのリストを得る。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページURLのリスト
    """
    store_elements = driver.find_elements(By.CSS_SELECTOR, '.list-rst__wrap.js-open-new-window')
    store_elements = [i.find_element(By.TAG_NAME, 'h3') for i in store_elements]
    store_elements = [i.find_element(By.TAG_NAME, 'a') for i in store_elements]
    return [i.get_attribute('href') for i in store_elements]


def get_store_info(driver: WebDriver, url: str, key: str) -> dict:
    """
    詳細ページから店の情報を取得する。

    Args:
        driver (WebDriver):
        url (str): 詳細ページのURL
        key (str): 店の固有キー

    Returns:
        dict: 店の情報
    """
    map_url = url + 'dtlmap/'
    driver.get(map_url)
    time.sleep(SLEEP_TIME)
    table_elements = driver.find_element(By.CSS_SELECTOR, '.c-table.c-table--form.rstinfo-table__table')
    th_texts = [i.text for i in table_elements.find_elements(By.TAG_NAME, 'th')]
    td_texts = [i.text for i in table_elements.find_elements(By.TAG_NAME, 'td')]
    result = {key: value for key, value in zip(th_texts, td_texts)}
    result['key'] = key
    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す。

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    m = re.search(r'/([^/]+)/$', url)
    return m.group(1)


if __name__ == '__main__':
    main()
