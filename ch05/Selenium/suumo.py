"""
suumoから物件情報を収集する
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 5
COLLECTION_NAME = 'suumo'
BASE_URL = 'https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&pc=30&smk=&po1=25&po2=99&shkr1=03&shkr2=03&shkr3=03&shkr4=03&rn=0350&ek=035009200&ra=013&cb=0.0&ct=6.0&md=03&et=9999999&mb=0&mt=9999999&cn=9999999&fw2='


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = BASE_URL
        driver.get(target_url)

        page_num = 1
        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(driver)
            item_urls.extend(urls)
            if is_last_page(driver):
                break
            else:
                page_num += 1
                update_page_num(driver, page_num)

        # スクレイピング量の削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                time.sleep(SLEEP_TIME)
                driver.get(i_url)
                collection.insert_one(get_item_info(driver, key))

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, page_num: int) -> None:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次のページ番号
    """
    base_url = BASE_URL
    next_url = base_url + f'&pn={page_num}'
    driver.get(next_url)


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    a_elements = driver.find_elements(By.CLASS_NAME, 'cassetteitem_other-linktext')
    return [i.get_attribute('href') for i in a_elements]


def get_item_info(driver: webdriver, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (webdriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    table_element = driver.find_element(By.CSS_SELECTOR, '.data_table.table_gaiyou')
    df = pd.read_html(table_element.get_attribute('outerHTML'))[0]
    first_df = df.iloc[:, :2] # 3,4列目を無視してしまっている
    keys = [i.replace('  ヒント', '') for i in first_df.iloc[:, 0].tolist()]
    vals = first_df.iloc[:, 1].to_list()
    result = {i_key: i_val for i_key, i_val in zip(keys, vals)}

    result['title'] = driver.find_element(By.TAG_NAME, 'h1').text
    result['price'] = driver.find_element(By.CLASS_NAME, 'property_view_note-emphasis').text
    result['key'] = key
    result['url'] = driver.current_url
    print(result)
    return result


def is_last_page(driver: WebDriver) -> bool:
    """
    一覧ページの最後のページかどうか確認する。

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    paging_elements = driver.find_elements(By.CLASS_NAME, 'pagination-parts')
    paging_text = [i.text for i in paging_elements]
    return not '次へ' in paging_text


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
