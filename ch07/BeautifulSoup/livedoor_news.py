"""
ライブドアニュースを取得
"""
import os
import time
import requests
from requests.sessions import Session
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient
from fake_useragent import UserAgent

SLEEP_TIME = 10
FILE_DIR = 'output'
COLLECTION_NAME = 'livedoor'


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
        if not os.path.exists(FILE_DIR):
            os.makedirs(FILE_DIR)

        target_url = 'https://news.livedoor.com/'
        response = session.get(target_url, headers=headers)
        time.sleep(SLEEP_TIME)

        article_urls = list()

        urls = get_news_url(response)

        # データ量を減らす
        urls = urls[:4]
        article_urls.extend(urls)
        article_urls = set([i.replace('topics', 'article') for i in article_urls])

        for i_url in article_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                print(i_url)
                response = session.get(i_url, headers=headers)
                time.sleep(SLEEP_TIME)
                item_info = get_data(session, headers, response, key)
                collection.insert_one(item_info)


def get_data(session: Session, headers: dict, response: Response, key: str) -> dict:
    """
    詳細ページから記事の情報を取得する。

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: 記事の詳細
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    result = dict()
    result['url'] = response.url
    result['key'] = key
    result['title'] = soup.find(class_='articleTtl').text
    result['date'] = soup.find(class_='articleDate').text
    result['vender'] = soup.find(class_='articleVender').text
    result['file_name'] = f'livedoor_{result["key"]}.txt'

    article_text = str()
    while True:
        i_article_text = soup.find(class_='articleBody').text
        article_text = article_text + '\n' + i_article_text

        pager_elements = soup.find_all(class_='next')
        if pager_elements:
            next_li_element = pager_elements[0].find_all(class_='next')
            if next_li_element:
                next_url = next_li_element.find('a').get('href')
                response = session.get(next_url, headers=headers)
                time.sleep(SLEEP_TIME)
                soup = BeautifulSoup(response.text, 'html.parser')
            else:
                break
        else:
            break

    file_path = os.path.join(FILE_DIR, result['file_name'])
    with open(file_path, 'w') as f:
        f.write(article_text)

    return result


def get_news_url(response: Response) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    a_elements = soup.find_all(class_='rewrite_ab')
    return [i.get('href') for i in a_elements]


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
