"""
インスタグラマーのランキングのデータを取得する
"""
import time
import datetime
import urllib
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient

SLEEP_TIME = 5
COLLECTION_NAME = 'insta_ranking'


def main():
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    with requests.Session() as session:
        user_urls = list()
        for i_page_num in range(1, 2):
            response = update_page_num(session, i_page_num)
            time.sleep(SLEEP_TIME)
            user_urls.extend(get_urls(response))
        print("="*80)

        for i_url in user_urls:
            key = extract_key(i_url)

            result = collection.find_one({'key': key})
            if not result:
                response = session.get(i_url)
                time.sleep(SLEEP_TIME)
                result = get_user_info(response, key)
                collection.insert_one(result)


def update_page_num(session: Session, page_num: int) -> None:
    """
    次の一覧ページを表示する。

    Args:
        driver (WebDriver):
        page_num (int): 次のページ番号
    """
    url = f'https://insta.refetter.com/ranking/?p={page_num}'
    return session.get(url)


def get_urls(response: Response) -> list:
    """
    一覧ページから詳細ページのURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    result = list()
    table_elements = soup.find_all('table')
    for i_table in table_elements:
        photo_elements = i_table.find_all(class_='photo')
        urls = [urllib.parse.urljoin(response.url, i.find('a').get('href')) for i in photo_elements]
        print(urls)
        result.extend(urls)
    return result


def  get_user_info(response: Response, key: str) -> dict:
    """
    詳細情報から情報を取得する。

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: アイテムの情報
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    table_data = soup.select_one('#person > section.basic > div > div.basic')
    dt_elements = table_data.find_all('dt')
    keys = [i.text for i in dt_elements]
    dd_elements = table_data.find_all('dd')
    values = [i.text for i in dd_elements]
    result = {k: v for k, v in zip(keys, values)}

    result['key'] = key

    bc_element = soup.find(class_='breadcrumb')
    result['ユーザー名'] = bc_element.find_all('li')[-1].text
    result['ランキングURL'] = response.url
    if len(result) <= 4:    # 消去済み垢はここでストップ
        return result
    a_element = soup.find(class_='fullname').find('a')
    result['インスタURL'] = a_element.get('href')
    result['取得日時'] = datetime.datetime.now().strftime('%Y:%m:%d:%H:%M')

    print(result)
    return result


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
