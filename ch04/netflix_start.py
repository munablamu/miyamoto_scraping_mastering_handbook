"""
Netflix配信予定作品の情報を取得する
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdrover.chrome.webdriber import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 10
COLLECTION_NAME = 'netflix_start'


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
        target_url = 'https://www.net-frx.com/p/netflix-coming-soon.html'

        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        result = get_info(driver)

        collection.insert_many(result)

    finally:
        driver.quit()


def get_info(driver: WebDriver) -> list[dict]:
    """
    作品情報のリストを返す

    Args:
        driver (WebDriver):

    Returns:
        list[dict]: 辞書型の作品情報のリスト
    """
    results = list()
    day_elements = driver.find_elements(By.CLASS_NAME, 'date-cc')
    for i_day in day_elements:
        date = i_day.find_element(By.CLASS_NAME, 'newtoto2').text
        content_elements = i_day.find_elements(By.CSS_SELECTOR, 'div.mark89 > div')
        for i_content in content_elements:
            content_result = dict()
            content_result['date'] = date
            title_element = i_content.find_element(By.CLASS_NAME, 'sche-npp-txt')
            content_result['title'] = title_element.text
            content_result['url'] = title_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
            content_result['season'] = i_content.find_element(By.CLASS_NAME, 'sche-npp-seas').text
            content_result['genre'] = i_content.find_element(By.CLASS_NAME, 'sche-npp-gen').text
            results.append(content_result)
    return results


if __name__ == '__main__':
    main()
