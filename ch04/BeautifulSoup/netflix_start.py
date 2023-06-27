"""
Netflix配信予定作品の情報を取得する
"""
import time
import requests
from bs4 import BeautifulSoup
from requests.models import Response
from pymongo import MongoClient

SLEEP_TIME = 10
COLLECTION_NAME = 'netflix_start'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    if COLLECTION_NAME in client.scraping.list_collection_names():
        client.scraping[COLLECTION_NAME].drop()
    collection = client.scraping[COLLECTION_NAME]

    with requests.Session() as session:
        target_url = 'https://www.net-frx.com/p/netflix-coming-soon.html'

        response = session.get(target_url)
        time.sleep(SLEEP_TIME)

        result = get_info(response)

        collection.insert_many(result)


def get_info(response: Response) -> list[dict]:
    """
    作品情報のリストを返す

    Args:
        driver (WebDriver):

    Returns:
        list[dict]: 辞書型の作品情報のリスト
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    results = list()
    day_elements = soup.find_all(class_='date-cc')
    for i_day in day_elements:
        date = i_day.find(class_='newtoto2').text
        content_elements = i_day.select('div.mark89 > div')
        for i_content in content_elements:
            content_result = dict()
            content_result['date'] = date
            title_element = i_content.find(class_='sche-npp-txt')
            content_result['title'] = title_element.text
            content_result['url'] = title_element.find('a').get('href')
            content_result['season'] = i_content.find(class_='sche-npp-seas').text
            content_result['genre'] = i_content.find(class_='sche-npp-gen').text
            results.append(content_result)
    return results


if __name__ == '__main__':
    main()
