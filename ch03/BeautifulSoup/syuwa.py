"""
秀和システムのデータを取得する
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

SLEEP_TIME  = 1
COLLECTION_NAME = 'syuwa'
BASE_URL = 'https://www.shuwasystem.co.jp/search/index.php?search_genre=13273&c=1'


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
        page_num = 1
        item_urls = list()
        while True:
            response = update_page_num(session, headers, page_num)
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(response)
            print(urls)
            item_urls.extend(urls)
            if is_last_page(response):
                break
            page_num += 1

        for url in item_urls:
            key = extract_key(url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                response = session.get(url, headers=headers)
                response.encoding = response.apparent_encoding
                time.sleep(SLEEP_TIME)
                item_info = get_item_info(response, key)
                collection.insert_one(item_info)

            print(item_info)


def update_page_num(session: Session, headers: dict, page_num: int) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        page_num (int): 次ページの番号
    """
    base_url = 'https://www.shuwasystem.co.jp/search/index.php?search_genre=13273&c=1'
    page_option = f'&page={page_num}'
    next_url = base_url + page_option
    return session.get(next_url, headers=headers)


def get_item_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    bookwrap_element = soup.find(class_='bookWrap')
    ttl_elements = bookwrap_element.find_all(class_='ttl')
    a_elements = [i.find('a') for i in ttl_elements]
    return [urllib.parse.urljoin(response.url, i.get('href')) for i in a_elements]


def get_item_info(response: Response, key: str) -> dict:
    """
    詳細ページからアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): アイテムのキー(ISBN)

    Returns:
        dict: アイテムの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    result = dict()
    result['key'] = key
    result['title'] = soup.find(class_='titleWrap').text
    result['price'] = soup.select_one('#main > div.detail > div.right > table > tbody > tr:nth-child(6) > td').text
    result['author'] = soup.select_one('#main > div.detail > div.right > table > tbody > tr:nth-child(1) > td > a').text
    result['describe'] = soup.find(id='bookSample').text
    return result


def is_last_page(response: Response) -> bool:
    """
    一覧ページの最後のページかどうかを確認する

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    pagingWrap_element = soup.find(class_='pagingWrap')
    paging_text = pagingWrap_element.find(class_='right').text
    return not '次' in paging_text


def extract_key(url: str) -> str:
    """
    URLからキー(URLの末尾のISBN)を抜き出す

    Args:
        url (str): 対象URL

    Returns:
        str: キー(ISBN)
    """
    m = re.search(r'/([^/]+).html$', url)
    return m.group(1)


if __name__ == '__main__':
    main()
