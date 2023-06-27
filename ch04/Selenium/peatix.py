"""
Peatixイベントの情報を取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 4
COLLECTION_NAME = 'peatix'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get('https://peatix.com/search?q=python&country=JP&l.text=%E3%81%99%E3%81%B9%E3%81%A6%E3%81%AE%E5%A0%B4%E6%89%80&p=1&size=20&v=3.4&tag_ids=&dr=&p=2')
        urls = list()

        while True:
            time.sleep(SLEEP_TIME)
            urls.extend(get_url(driver))
            if check_last(driver):
                break
            page_update(driver)

        for i_url in urls:
            key = extract_key(i_url)

            info = collection.find_one({'key': key})
            if not info:
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                info = get_info(driver, key)
                collection.insert_one(info)

            print(info)

    finally:
        driver.quit()


def page_update(driver: WebDriver) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
    """
    driver.find_element(By.CLASS_NAME, 'next').click()


def check_last(driver: WebDriver) -> bool:
    """
    最後の一覧ページかどうか確認する。

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    button_css = driver.find_element(By.CLASS_NAME, 'next').get_attribute('style')
    return 'display: none' in button_css


def get_url(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    ul_element = driver.find_element(By.CSS_SELECTOR, '.event-list.event-list__medium')
    a_elements = ul_element.find_elements(By.CLASS_NAME, 'event-thumb_link')
    return [i.get_attribute('href') for i in a_elements]


def get_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    result = dict()
    result['key'] = key
    result['url'] = driver.current_url
    print(result['url'])
    result['title'] = driver.find_element(By.CLASS_NAME, 'event-summary__title').text

    event_info_element = driver.find_element(By.CLASS_NAME, 'event-essential')
    time_element = event_info_element.find_element(By.TAG_NAME, 'time')
    result['date'] = time_element.find_elements(By.TAG_NAME, 'p')[0].text
    result['time'] = time_element.find_elements(By.TAG_NAME, 'p')[1].text

    address_elements = event_info_element.find_elements(By.CSS_SELECTOR, 'address')
    result['place'] = address_elements[0].text if len(address_elements) > 0 else 'オンライン'

    ul_elements = event_info_element.find_elements(By.CLASS_NAME, 'event-tickets__list')
    if len(ul_elements) > 0:
        result['ticket'] = '/'.join([i.text for i in ul_elements[0].find_elements(By.TAG_NAME, 'li')])

    result['description'] = driver.find_element(By.CLASS_NAME, 'event-main').text
    result['organize'] = driver.find_element(By.CLASS_NAME, 'pod-thumb__name-link').text

    return result


def extract_key(url: str) -> str:
    """
    URLの末尾からキーを抜き出す

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    return url.split('/')[-1].split('?')[0]


if __name__ == '__main__':
    main()

