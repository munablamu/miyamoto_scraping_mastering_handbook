"""
Youtuberのランキングのデータを取得する
"""
import time
import re
import urllib
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient
from fake_useragent import UserAgent

SLEEP_TIME = 3
COLLECTION_NAME = 'youtube_ranking'


def main():
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    ua = UserAgent()
    headers = {'User-Agent': str(ua.chrome)}

    with requests.Session() as session:
        urls = list()
        for i_page in range(1, 3):
            response = update_page(session, headers, i_page)
            time.sleep(SLEEP_TIME)
            urls.extend(get_urls(response))

        for i_url in urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                response = session.get(i_url, headers=headers)
                time.sleep(SLEEP_TIME)
                item_info = get_info(response, key)
                collection.insert_one(item_info)


def update_page(session: Session, headers: dict, page_num: int) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次ページの番号
    """
    url = f'https://youtube-ranking.userlocal.jp/?page={page_num}'
    return session.get(url, headers=headers)


def get_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    table_element = soup.find('tbody')
    tr_elements = table_element.find_all('tr')
    return [urllib.parse.urljoin(response.url, i.find('a').get('href')) for i in tr_elements]


def get_info(response: Response, key: str) -> dict:
    """
    詳細ページからyoutuberの情報を取得する。

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: youtuberの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    result = dict()
    result['key'] = key
    result['name'] = normalize_spaces(soup.find('h6').text)
    result['rank_url'] = response.url
    result['youtube_url'] = soup.select_one('h6 > a').get('href')
    result['start_date'] = soup.select_one('div.card-body.pt-0 > div').text.replace('〜', '')
    result['describe'] = soup.select_one('div.card-body.pt-0 > p').text
    result['subscriber_count'] = normalize_spaces(soup.select_one('div.card-body.px-3.py-5 > div.d-inline-block').text)
    result['views'] = normalize_spaces(soup.select_one('div.card.mt-2 > div > div.d-inline-block').text)
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


def normalize_spaces(s: str) -> str:
    """
    連続する空白を1つのスペースに置き換え、前後の空白を削除した新しい文字列を取得する

    Args:
        s (str): 元の文字列

    Returns:
        str: 加工後の文字列
    """
    return re.sub(r'\s+', ' ', s).strip()


if __name__ == '__main__':
    main()
