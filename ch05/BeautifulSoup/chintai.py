"""
物件情報CHINTAIのデータを取得する
"""
import time
import urllib
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient

SLEEP_TIME = 5
COLLECTION_NAME = 'chintai'
BASE_URL = 'https://www.chintai.net/list/?o=10&pageNoDisp=20%E4%BB%B6&o=10&rt=51&prefkey=tokyo&ue=000004864&urlType=dynamic&cf=0&ct=60&k=1&m=0&m=2&jk=0&jl=0&sf=0&st=0&j=&h=99&b=1&b=2&b=3&jks='


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    with requests.Session() as session:
        base_url = BASE_URL
        response = session.get(base_url)
        time.sleep(SLEEP_TIME)

        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(response)
            print(urls)
            item_urls.extend(urls)

            if is_last_page(response):
                break
            else:
                response = update_page(session, response)

        item_urls = item_urls[:10] # データ量を減らす

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                response = session.get(i_url)
                time.sleep(SLEEP_TIME)
                item_info = get_item_info(response, key)
                collection.insert_one(item_info)


def update_page(session: Session, response: Response) -> Response:
    """
    次の一覧ページを表示する。
    直後にtime.sleep()が必要。

    Args:
        driver (WebDriver):
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    pager_element = soup.find(class_='list_pager')
    nextbutton_element = pager_element.find(class_='next')
    a_element = nextbutton_element.find('a')
    return session.get(urllib.parse.urljoin(response.url, a_element.get('href')))


def get_item_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    property_elements = soup.select('.js-detailLinkUrl.js_favorite_check_box.gtm_aw_data')
    a_elements = [i.select_one('.js_bukken_info_area.ga_bukken_cassette') for i in property_elements]
    return [urllib.parse.urljoin(response.url, i.get('href')) for i in a_elements]


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

    result = dict()
    result['url'] = response.url
    result['key'] = key
    result['title'] = soup.find('h2').text.replace('の賃貸物件詳細', '')
    result['price'] = soup.find(class_='rent').text
    result['access'] = soup.find(class_='mod_necessaryTime').text
    return result


def is_last_page(response: Response) -> bool:
    """
    一覧ページの最後のページかどうかを確認する。

    Args:
        driver (WebDriver):

    Returns:
        bool:
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    paging_text = soup.find(class_='list_pager').text
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
