"""
Tiktokerのランキング情報を取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 4
COLLECTION_NAME = 'tiktok_ranking'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())

        urls = list()
        for i_page_num in range(1, 21):
            update_page_num(driver, i_page_num)
            time.sleep(SLEEP_TIME)
            urls.extend(get_item_urls(driver))

        urls = urls[:10] # データの量を減らす

        for i_rank, i_url in enumerate(urls, start=1):
            key = extract_key(i_url)

            user_dict = collection.find_one({'key': key})
            if not user_dict:
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                user_dict = get_item_info(driver, key)
                user_dict['ranking'] = i_rank
                collection.insert_one(user_dict)

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
    driver.get(f'https://tiktok-ranking.userlocal.jp/?page={page_num}')


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    ranking_element = driver.find_element(By.CLASS_NAME, 'rankers')
    a_elements = ranking_element.find_elements(By.CLASS_NAME, 'no-decorate')
    return [i.get_attribute('href') for i in a_elements]


def get_item_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: アイテムの情報
    """
    result = dict()
    result['key'] = key
    result['rank_page'] = driver.current_url
    result['name'] = driver.find_element(By.CSS_SELECTOR, '.show-name.col-12').text
    result['id'] = driver.find_element(By.CSS_SELECTOR, '.col-12.show-id').text
    result['comment'] = driver.find_element(By.CSS_SELECTOR, '.col-12.show-description').text
    result['posts_num'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[0].text
    result['follower_num'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[1].text
    result['favs'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[3].text
    result['favs_mean'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[4].text
    result['favs_rate'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[5].text
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
