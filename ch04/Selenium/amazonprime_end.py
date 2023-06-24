"""
Amazonプライムビデオ配信終了予定の情報を取得する
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 5
COLLECTION_NAME = 'amazonprime_end'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    if COLLECTION_NAME in client.scraping.list_collection_names():
        client.scraping[COLLECTION_NAME].drop()
    collection = client.scraping[COLLECTION_NAME]

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = 'https://animephilia.net/amazon-prime-video-expiring-calendar/'
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        results = list()
        for i in range(3):
            results.extend(get_info(driver))
            calender_update(driver)
            time.sleep(SLEEP_TIME)

        collection.insert_many(results)
        print(results)

    finally:
        driver.quit()


def scroll_to_see_element(driver: WebDriver, by: str, value: str) -> None:
    """
    要素が見える位置まで画面をスクロールする。

    Args:
        driver (WebDriver):
        by (str): By.CLASS_NAMEなど
        value (str): 値
    """
    element = driver.find_element(by, value)
    driver.execute_script("arguments[0].scrollIntoView();", element)


def calender_update(driver: WebDriver) -> None:
    """
    翌週のカレンダーを表示する。

    Args:
        driver (WebDriver):
    """
    scroll_to_see_element(driver, By.CLASS_NAME, 'next')
    driver.find_element(By.CLASS_NAME, 'next').click()


def get_info(driver: WebDriver) -> list[dict]:
    """
    作品情報のリストを返す。

    Args:
        driver (WebDriver):

    Returns:
        list: 辞書型の作品情報のリスト
    """
    results = list()
    day_elements = driver.find_elements(By.CLASS_NAME, 'day-column')

    for i_day in day_elements:
        day_data = i_day.get_attribute('data-date')
        content_elements = i_day.find_elements(By.CSS_SELECTOR, '.event.upcoming')

        for i_content in content_elements:
            content_result = dict()
            content_result['day'] = day_data
            a_element = i_content.find_element(By.CLASS_NAME, 'content-title')
            content_result['title'] = a_element.text
            content_result['url'] = a_element.get_attribute('href')
            results.append(content_result)

    return results


if __name__ == '__main__':
    main()
