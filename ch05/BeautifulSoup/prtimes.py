"""
PRTIMESのデータを取得する
"""
import os
import time
import urllib
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

ARTICLE_DATA_DIR = 'output'
COLLECTION_NAME = 'prtimes'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    with requests.Session() as session:
        if not os.path.exists(ARTICLE_DATA_DIR):
            os.makedirs(ARTICLE_DATA_DIR)

        page_urls = list()
        for i_pagenum in range(1, 6):
            time.sleep(10)
            base_url = f'https://prtimes.jp/main/html/index/pagenum/{i_pagenum}'
            response = session.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            article_urls = [urllib.parse.urljoin(response.url, i.get('href')) for i in soup.find_all(class_='list-article__link')]
            page_urls.extend(article_urls)

        page_urls = page_urls[:10] # スクレイピング量を削減

        for i_url in page_urls:
            key = os.path.splitext(i_url.split('/')[-1])[0]

            row_result = collection.find_one({'key': key})
            if not row_result:
                row_result = dict()
                response = session.get(i_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                time.sleep(5)

                row_result['key'] = key
                row_result['url'] = i_url
                row_result['title'] = soup.find(class_='release--title').text.strip()
                row_result['company'] = soup.find(class_='company-name').text.strip()
                row_result['datetime'] = soup.find('time').text
                row_result['abstract'] = soup.find(class_='r-head').text.strip()

                collection.insert_one(row_result)
                article_path = os.path.join(ARTICLE_DATA_DIR, f'{row_result["key"]}.txt')
                with open(article_path, 'w') as f:
                    main_text = soup.find(class_='rich-text').text
                    f.write(main_text)


if __name__ == '__main__':
    main()
