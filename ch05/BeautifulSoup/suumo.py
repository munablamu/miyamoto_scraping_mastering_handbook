"""
suumoから物件情報を収集する
"""
import time
import urllib
import requests
from requests.sessions import Session
from requests.models import Response
import pandas as pd
from bs4 import BeautifulSoup
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

    with requests.Session() as session:
        target_url = BASE_URL
        response = session.get(target_url)

        page_num = 1
        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(response)
            item_urls.extend(urls)
            if is_last_page(response):
                break
            else:
                page_num += 1
                response = update_page_num(session, page_num)

        # スクレイピング量の削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                time.sleep(SLEEP_TIME)
                response = session.get(i_url)
                collection.insert_one(get_item_info(response, key))


def update_page_num(session: Session, page_num: int) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次のページ番号
    """
    base_url = BASE_URL
    next_url = base_url + f'&pn={page_num}'
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
    a_elements = soup.find_all(class_='cassetteitem_other-linktext')
    return [urllib.parse.urljoin(response.url, i.get('href')) for i in a_elements]


def get_item_info(response: Response, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (webdriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    table_element = soup.select_one('.data_table.table_gaiyou')
    df = pd.read_html(str(table_element))[0]
    first_df = df.iloc[:, :2] # 3,4列目を無視してしまっている
    keys = [i.replace('  ヒント', '') for i in first_df.iloc[:, 0].tolist()]
    vals = first_df.iloc[:, 1].to_list()
    result = {i_key: i_val for i_key, i_val in zip(keys, vals)}

    result['title'] = soup.find('h1').text
    result['price'] = soup.find(class_='property_view_note-emphasis').text
    result['key'] = key
    result['url'] = response.url
    print(result)
    return result


def is_last_page(response: Response) -> bool:
    """
    一覧ページの最後のページかどうか確認する。

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    paging_elements = soup.find_all(class_='pagination-parts')
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
