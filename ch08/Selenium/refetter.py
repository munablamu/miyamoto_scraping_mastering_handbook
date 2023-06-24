"""
インスタグラマーのランキングのデータを取得する
"""
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 5
COLLECTION_NAME = 'insta_ranking'


def main():
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        user_urls = list()
        for i_page_num in range(1, 2):
            update_page_num(driver, i_page_num)
            time.sleep(SLEEP_TIME)
            user_urls.extend(get_urls(driver))
        print("="*80)

        for i_url in user_urls:
            key = extract_key(i_url)

            result = collection.find_one({'key': key})
            if not result:
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                result = get_user_info(driver, key)
                collection.insert_one(result)

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, page_num: int) -> None:
    """
    次の一覧ページを表示する。

    Args:
        driver (WebDriver):
        page_num (int): 次のページ番号
    """
    url = f'https://insta.refetter.com/ranking/?p={page_num}'
    driver.get(url)


def get_urls(driver: WebDriver) -> list:
    """
    一覧ページから詳細ページのURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    result = list()
    table_elements = driver.find_elements(By.TAG_NAME, 'table')
    for i_table in table_elements:
        photo_elements = i_table.find_elements(By.CLASS_NAME, 'photo')
        urls = [i.find_element(By.TAG_NAME, 'a').get_attribute('href') for i in photo_elements]
        print(urls)
        result.extend(urls)
    return result


def  get_user_info(driver: WebDriver, key: str) -> dict:
    """
    詳細情報から情報を取得する。

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: アイテムの情報
    """
    table_data = driver.find_element(By.CSS_SELECTOR, '#person > section.basic > div > div.basic')
    dt_elements = table_data.find_elements(By.TAG_NAME, 'dt')
    keys = [i.text for i in dt_elements]
    dd_elements = table_data.find_elements(By.TAG_NAME, 'dd')
    values = [i.text for i in dd_elements]
    result = {k: v for k, v in zip(keys, values)}

    result['key'] = key

    bc_element = driver.find_element(By.CLASS_NAME, 'breadcrumb')
    result['ユーザー名'] = bc_element.find_elements(By.TAG_NAME, 'li')[-1].text
    result['ランキングURL'] = driver.current_url
    if len(result) <= 4:    # 消去済み垢はここでストップ
        return result
    a_element = driver.find_element(By.CLASS_NAME, 'fullname').find_element(By.TAG_NAME, 'a')
    result['インスタURL'] = a_element.get_attribute('href')
    result['取得日時'] = datetime.datetime.now().strftime('%Y:%m:%d:%H:%M')

    print(result)
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
