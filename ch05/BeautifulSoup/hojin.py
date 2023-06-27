"""
全国法人リストから会社情報を取得
"""
import time
import urllib
import pandas as pd
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient

SLEEP_TIME = 3
COLLECTION_NAME = 'hojin'
BASE_URL = 'https://houjin.jp/search?keyword=%E3%82%BD%E3%83%8B%E3%83%83%E3%82%AF&pref_id='


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    with requests.Session() as session:
        target_url = BASE_URL
        response = session.get(target_url)
        time.sleep(SLEEP_TIME)

        page_num = 1
        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(response)

            if len(urls) == 0:
                break
            else:
                item_urls.extend(urls)
                page_num += 1
                response = update_page_num(session, page_num)

        item_urls = item_urls[:5] # データ量を減らす

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                time.sleep(SLEEP_TIME)
                response = session.get(i_url)
                item_info = get_item_info(response, key)
                collection.insert_one(item_info)


def update_page_num(session: Session, page_num: int) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次のページ番号
    """
    base_url = BASE_URL
    next_url = base_url + f'&page={page_num}'
    return session.get(next_url)


def get_item_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    cop_item_elements = soup.find_all(class_='c-corp-item')
    return [urllib.parse.urljoin(response.url, i.find('a').get('href')) for i in cop_item_elements]


def get_item_info(response: Response, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する。

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    corp_info_table_element = soup.find(class_='corp-info-table')
    corp_info_html = str(corp_info_table_element)
    corp_info_df = pd.read_html(corp_info_html)[0]
    keys = corp_info_df.iloc[:, 0].tolist()
    vals = corp_info_df.iloc[:, 1].tolist()
    corp_info = {i_key: i_val for i_key, i_val in zip(keys, vals)}
    corp_info['key'] = key
    return corp_info


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
