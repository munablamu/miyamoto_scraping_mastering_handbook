"""
Githubトレンドのデータを取得する
"""
import re
import time
import urllib
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

SLEEP_TIME = 3
COLLECTION_NAME = 'github_ranking'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    if COLLECTION_NAME in client.scraping.list_collection_names():
        client.scraping[COLLECTION_NAME].drop()
    collection = client.scraping[COLLECTION_NAME]

    with requests.Session() as session:
        url = 'https://github.com/trending'
        response = session.get(url)
        time.sleep(SLEEP_TIME)

        soup = BeautifulSoup(response.text, 'html.parser')
        box_row_elements = soup.find_all(class_='Box-row')
        for i_box in box_row_elements:
            row_data = dict()
            row_data['title'] = normalize_spaces(i_box.find('h2').text)
            row_data['url'] = urllib.parse.urljoin(url, i_box.find('h2').find('a').get('href'))
            lang_elements = i_box.select('.d-inline-block.ml-0.mr-3')
            row_data['lang'] = normalize_spaces(lang_elements[0].text) if len(lang_elements) == 1 else None
            row_data['total_star'] = normalize_spaces(i_box.select('.Link--muted.d-inline-block.mr-3')[0].text)
            row_data['fork'] = normalize_spaces(i_box.select('.Link--muted.d-inline-block.mr-3')[1].text)
            row_data['todays_star'] = normalize_spaces(i_box.select_one('.d-inline-block.float-sm-right').text.replace('stars today', ''))
            collection.insert_one(row_data)

            print(row_data)


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
