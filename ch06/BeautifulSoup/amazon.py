"""
Amazon商品情報を取得する
"""
import time
import urllib
import requests
from requests.models import Response
from bs4 import BeautifulSoup
from pymongo import MongoClient
from fake_useragent import UserAgent

COLLECTION_NAME = 'amazon'
SLEEP_TIME = 3


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
        target_url = 'https://www.amazon.co.jp/s?k=novation'
        response = session.get(target_url, headers=headers)
        time.sleep(SLEEP_TIME)

        page_num = 1
        item_urls = list()
        while True:
            urls = get_item_urls(response)
            if len(urls) == 0:
                break
            time.sleep(SLEEP_TIME)
            item_urls.extend(urls)
            page_num += 1
            response = session.get(target_url + f'&page={page_num}', headers=headers)

        # スクレイピング料を削減
        item_urls = item_urls[:10]

        for i_url in item_urls:
            key = extract_key(i_url)

            item_info = collection.find_one({'key': key})
            if not item_info:
                response = session.get(i_url, headers=headers)
                time.sleep(SLEEP_TIME)
                item_info = get_item_info(response, key)
                print(item_info)
                collection.insert_one(item_info)


def get_item_urls(response: Response) -> list:
    """
    一覧ページからURLを取得する。

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    all_item_elements = soup.select('.sg-col-4-of-12.s-result-item.s-asin.sg-col-4-of-16.sg-col.s-widget-spacing-small.sg-col-4-of-20')
    removed_item_elements = [i for i in all_item_elements
                             if len(i.select('.a-row.a-spacing-micro')) == 0]
    a_tag_elements = [i.find('a') for i in removed_item_elements]
    hrefs = [urllib.parse.urljoin(response.url, i.get('href')) for i in a_tag_elements]
    item_urls = list(set(hrefs))
    return item_urls


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

    try:
        result = dict()
        result['site'] = 'Amazon'
        result['url'] = response.url
        result['key'] = key

        title_element = soup.find(id='title')
        result['title'] = title_element.text.strip()

        price_element = soup.find(class_='a-price-whole')
        result['price'] = price_element.text

        stock_element = soup.find(id='availability')
        result['is_stock'] = 'In Stock' in stock_element.text

        description_element = soup.find(id='feature-bullets')
        result['description'] = description_element.text

    except:
        print(f'詳細な情報を取得できませんでした:{response.url}')

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
