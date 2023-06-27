"""
食べログの飲食店データを取得する
"""
import re
import time
import math
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient

SLEEP_TIME = 4
COLLECTION_NAME = 'tabelog'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    with requests.Session() as session:
        base_url = 'https://tabelog.com/tokyo/rstLst/?vs=1&sa=%E6%9D%B1%E4%BA%AC%E9%83%BD&sk=%25E5%2588%2580%25E5%2589%258A%25E9%25BA%25BA&lid=top_navi1&vac_net=&svd=20220822&svt=1900&svps=2&hfc=1&Cat=RC&LstCat=RC03&LstCatD=RC0304&LstCatSD=RC030402&cat_sk=%E5%88%80%E5%89%8A%E9%BA%BA'
        response = session.get(base_url)
        time.sleep(SLEEP_TIME)

        page_num = get_pagenum(response)

        store_urls = list()
        for _ in range(page_num-1):
            urls = get_store_url(response)
            store_urls.extend(urls)
            response = get_next(session, response)
            time.sleep(SLEEP_TIME)

        store_urls = store_urls[:5] # データ量を減らす
        for i_url in store_urls:
            key = extract_key(i_url)

            store_info = collection.find_one({'key': key})
            if not store_info:
                store_info = get_store_info(session, i_url, key)
                collection.insert_one(store_info)

            print(store_info)


def get_next(session: Session, response: Response) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver): _description_
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    pagenation_element = soup.find_all(class_='c-pagination__item')[-1]
    next_url = pagenation_element.find('a').get('href')
    return session.get(next_url)


def get_pagenum(response: Response) -> int:
    """
    一覧ページのページ数をカウントする。

    Args:
        driver (WebDriver):

    Returns:
        int:
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    count_elements = soup.find_all(class_='c-page-count__num')
    paging_num = int(count_elements[1].text)
    total_num = int(count_elements[2].text)
    return math.ceil(total_num / paging_num)


def get_store_url(response: Response) -> list:
    """
    一覧ページからURLのリストを得る。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページURLのリスト
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    store_elements = soup.select('.list-rst__wrap.js-open-new-window')
    store_elements = [i.find('h3') for i in store_elements]
    store_elements = [i.find('a') for i in store_elements]
    return [i.get('href') for i in store_elements]


def get_store_info(session: Session, url: str, key: str) -> dict:
    """
    詳細ページから店の情報を取得する。

    Args:
        driver (WebDriver):
        url (str): 詳細ページのURL
        key (str): 店の固有キー

    Returns:
        dict: 店の情報
    """
    map_url = url + 'dtlmap/'
    response = session.get(map_url)
    time.sleep(SLEEP_TIME)
    soup = BeautifulSoup(response.text, 'html.parser')
    table_element = soup.select_one('.c-table.c-table--form.rstinfo-table__table')
    th_texts = [i.text for i in table_element.find_all('th')]
    td_texts = [i.text for i in table_element.find_all('td')]
    result = {normalize_spaces(key): normalize_spaces(value) for key, value in zip(th_texts, td_texts)}
    result['key'] = key
    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す。

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    m = re.search(r'/([^/]+)/$', url)
    return m.group(1)


def normalize_spaces(s: str) -> str:
    """
    連即する空白を１つのスペースに置き換え、前後の空白を削除した新シ文字列を返す。

    Args:
        s (str): もとの文字列

    Returns:
        str: 加工後の文字列
    """
    return re.sub(r'\s+', ' ', s).strip()


if __name__ == '__main__':
    main()
