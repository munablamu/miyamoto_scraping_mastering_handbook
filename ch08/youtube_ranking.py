"""
Youtuberのランキングのデータを取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 3
COLLECTION_NAME = 'youtube_ranking'


def main():
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        urls = list()
        for i_page in range(1, 3):
            update_page(driver, i_page)
            time.sleep(SLEEP_TIME)
            urls.extend(get_urls(driver))

        results = list()
        for i_url in urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                item_info = get_info(driver, key)
                collection.insert_one(item_info)

    finally:
        driver.quit()


def update_page(driver: WebDriver, page_num: int) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次ページの番号
    """
    url = f'https://youtube-ranking.userlocal.jp/?page={page_num}'
    driver.get(url)


def get_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    table_element = driver.find_element(By.TAG_NAME, 'tbody')
    tr_elements = table_element.find_elements(By.TAG_NAME, 'tr')
    return [i.find_element(By.TAG_NAME, 'a').get_attribute('href') for i in tr_elements]


def get_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからyoutuberの情報を取得する。

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: youtuberの情報
    """
    result = dict()
    result['key'] = key
    result['name'] = driver.find_element(By.TAG_NAME, 'h6').text
    result['rank_url'] = driver.current_url
    result['youtube_url'] = driver.find_element(By.CSS_SELECTOR, 'h6 > a').get_attribute('href')
    result['start_date'] = driver.find_element(By.CSS_SELECTOR, 'div.card-body.pt-0 > div').text
    result['describe'] = driver.find_element(By.CSS_SELECTOR, 'div.card-body.pt-0 > p').text
    result['subscriber_count'] = driver.find_element(By.CSS_SELECTOR, 'div.card-body.px-3.py-5 > div.d-inline-block').text
    result['views'] = driver.find_element(By.CSS_SELECTOR, 'div.card.mt-2 > div > div.d-inline-block').text
    return result


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
