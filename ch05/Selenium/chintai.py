"""
物件情報CHINTAIのデータを取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 5
COLLECTION_NAME = 'chintai'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        base_url = 'https://www.chintai.net/list/?o=10&pageNoDisp=20%E4%BB%B6&o=10&rt=51&prefkey=tokyo&ue=000004864&urlType=dynamic&cf=0&ct=60&k=1&m=0&m=2&jk=0&jl=0&sf=0&st=0&j=&h=99&b=1&b=2&b=3&jks='
        driver.get(base_url)
        time.sleep(SLEEP_TIME)

        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(driver)
            print(urls)
            item_urls.extend(urls)

            if is_last_page(driver):
                break
            else:
                update_page(driver)

        item_urls = item_urls[:10] # データ量を減らす

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                driver.get(i_url)
                time.sleep(SLEEP_TIME)
                item_info = get_item_info(driver, key)
                collection.insert_one(item_info)

    finally:
        driver.quit()


def update_page(driver: WebDriver) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
    """
    pager_element = driver.find_element(By.CLASS_NAME, 'list_pager')
    nextbutton_element = pager_element.find_element(By.CLASS_NAME, 'next')
    a_element = nextbutton_element.find_element(By.TAG_NAME, 'a')
    driver.get(a_element.get_attribute('href'))


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    property_elements = driver.find_elements(By.CSS_SELECTOR, '.js-detailLinkUrl.js_favorite_check_box.gtm_aw_data')
    a_elements = [i.find_element(By.CSS_SELECTOR, '.js_bukken_info_area.ga_bukken_cassette') for i in property_elements]
    return [i.get_attribute('href') for i in a_elements]


def get_item_info(driver: WebDriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する。

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    result = dict()
    result['url'] = driver.current_url
    result['key'] = key
    result['title'] = driver.find_element(By.TAG_NAME, 'h2').text.replace('の賃貸物件詳細', '')
    result['price'] = driver.find_element(By.CLASS_NAME, 'rent').text
    result['access'] = driver.find_element(By.CLASS_NAME, 'mod_necessaryTime').text
    return result


def is_last_page(driver: WebDriver) -> bool:
    """
    一覧ページの最後のページかどうかを確認する。

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    paging_text = driver.find_element(By.CLASS_NAME, 'list_pager').text
    return not '次' in paging_text


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
