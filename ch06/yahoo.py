"""
yahooショッピングのデータを取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 3
COLLECTION_NAME = 'yahoo'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = 'https://shopping.yahoo.co.jp/search?p=novation+mininova'
        driver.get(target_url)


        display_all_item(driver)
        item_urls = get_item_urls(driver)

        # スクレイピング量を削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                driver.get(i_url)
                time.sleep(5)
                item_info = get_item_info(driver, key)
                collection.insert_one(item_info)

    except Exception as e:
        print(e)
    finally:
        driver.quit()


def display_all_item(driver: WebDriver) -> None:
    """
    ページを下部までスクロールしてすべての商品が表示されるようにする。
    Args:
        driver (WebDriver):
    """
    start_html = driver.page_source
    while True:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(SLEEP_TIME)
        if driver.page_source == start_html:
            break
        else:
            start_html = driver.page_source


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    li_elements = driver.find_elements(By.CLASS_NAME, 'LoopList__item')
    a_elements = [i.find_element(By.TAG_NAME, 'a') for i in li_elements]
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
    result['site'] = 'yahoo'
    result['url'] = driver.current_url
    # id
    result['key'] = key
    # title
    md_element = driver.find_element(By.CLASS_NAME, 'mdItemName')
    result['title'] = md_element.find_element(By.CLASS_NAME, 'elName').text
    # price
    price_number_element = driver.find_element(By.CLASS_NAME, 'elPriceNumber')
    result['price'] = price_number_element.text
    # description
    description_element = driver.find_element(By.CLASS_NAME, 'mdItemDescription')
    result['description'] = description_element.text

    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す。

    Args:
        url (srt): 対象URL

    Returns:
        str: キー
    """
    url_tail = url.split('/')[-2] + '_' + url.split('/')[-1]
    return url_tail.split('?')[0].replace('.html', '')


if __name__ == '__main__':
    main()
