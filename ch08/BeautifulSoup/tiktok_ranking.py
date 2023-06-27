"""
Tiktokerのランキング情報を取得する
"""
import re
import time
import urllib
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient
from fake_useragent import UserAgent

SLEEP_TIME = 4
COLLECTION_NAME = 'tiktok_ranking'


def main() -> None:
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
        for i_page_num in range(1, 21):
            response = update_page_num(session, headers, i_page_num)
            time.sleep(SLEEP_TIME)
            urls.extend(get_item_urls(response))

        urls = urls[:10] # データの量を減らす

        for i_rank, i_url in enumerate(urls, start=1):
            key = extract_key(i_url)

            user_dict = collection.find_one({'key': key})
            if not user_dict:
                print(i_url)
                response = session.get(i_url, headers=headers)
                time.sleep(SLEEP_TIME)
                user_dict = get_item_info(response, key)
                user_dict['ranking'] = i_rank
                collection.insert_one(user_dict)


def update_page_num(session: Session, headers: dict, page_num: int) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次ページの番号
    """
    return session.get(f'https://tiktok-ranking.userlocal.jp/?page={page_num}', headers=headers)


def get_item_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    ranking_element = soup.find(class_='rankers')
    a_elements = ranking_element.find_all(class_='no-decorate')
    return [urllib.parse.urljoin(response.url, i.get('href')) for i in a_elements]


def get_item_info(response: Response, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: アイテムの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    result = dict()
    result['key'] = key
    result['rank_page'] = response.url
    result['name'] = soup.select_one('.show-name.col-12').text
    result['id'] = normalize_spaces(soup.select_one('.col-12.show-id').text)
    result['comment'] = soup.select_one('.col-12.show-description').text
    result['posts_num'] = normalize_spaces(soup.select('.col-7.stats-num')[0].text)
    result['follower_num'] = normalize_spaces(soup.select('.col-7.stats-num')[1].text)
    result['favs'] = normalize_spaces(soup.select('.col-7.stats-num')[3].text)
    result['favs_mean'] = normalize_spaces(soup.select('.col-7.stats-num')[4].text)
    result['favs_rate'] = normalize_spaces(soup.select('.col-7.stats-num')[5].text)
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
    連続する空白を１つのスペースに置き換え、前後の空白を削除した新しい文字列を返す。

    Args:
        s (str): もとの文字列

    Returns:
        str: 加工後の文字列
    """
    return re.sub(r'\s+', ' ', s).strip()

if __name__ == '__main__':
    main()
