"""
メルカリのデータを取得する
TODO: bot認定されている？
"""
import time
import datetime
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient
from fake_useragent import UserAgent

SLEEP_TIME = 3
COLLECTION_NAME = 'merucari'


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
        target_url = 'https://jp.mercari.com/search?keyword=novation&t1_category_id=1328&status=on_sale&category_id=79'
        response = session.get(target_url, headers=headers)
        time.sleep(5)

        page_num = 0
        item_urls = list()
        while True:
            urls = get_item_urls(response)
            print(response.text)
            print(len(urls))
            time.sleep(SLEEP_TIME)
            if len(urls) < 1: # 最終ページ
                break
            else:
                item_urls.extend(urls)
                page_num += 1
                response = update_page_num(session, headers, target_url, page_num)

        #スクレイピング量削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)
            print(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                response = session.get(i_url, headers=headers)
                time.sleep(5)
                item_info = get_item_info(response, key)
                collection.insert_one(item_info)


def update_page_num(session: Session, headers: dict, target_url: str, page_num: int) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
        target_url (str): 基底のURL
        page_num (int): 次ページの番号
    """
    page_option = f'&page_token=v1%3A{page_num}'
    return session.get(target_url + page_option, headers=headers)


def get_item_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    a_tag_elements = soup.find_all('a')
    if len(a_tag_elements) == 0:
        return list()
    hrefs = [i.get('href') for i in a_tag_elements]
    item_urls = [i for i in hrefs if 'item' in i]
    return item_urls


def get_item_info(response: Response, key: str) -> dict:
    """
    詳細情報からアイテムの情報を取得する

    Args:
        driver (WebDriver):
        key (str): アイテムのキー

    Returns:
        dict: アイテムの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    result = dict()
    result['key'] = key
    result['datetime'] = datetime.datetime.now().strftime('%y/%m/%d %H:%M:%S')
    result['description'] = soup.select_one('pre').text
    result['title'] = soup.find('h1').text
    price_section_element = soup.select('.sc-da871d51-8.jOzGgE')
    result['price'] = price_section_element.text.replace('¥', '')
    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    return url.split('/')[-1]


if __name__ == '__main__':
    main()
