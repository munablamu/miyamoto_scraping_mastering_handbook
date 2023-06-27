"""
Netflix配信終了予定の情報を取得する
"""
import time
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from pymongo import MongoClient

SLEEP_TIME = 2
COLLECTION_NAME = 'netflix_end'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    if COLLECTION_NAME in client.scraping.list_collection_names():
        client.scraping[COLLECTION_NAME].drop()
    collection = client.scraping[COLLECTION_NAME]

    with requests.Session() as session:
        target_url = 'https://www.net-frx.com/p/netflix-expiring.html'
        response = session.get(target_url)
        time.sleep(SLEEP_TIME)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = list()
        month1_elements = soup.select('.data-fd1.goke3 > div')
        result.extend(get_info(month1_elements))

        month2_elements = soup.select('.data-fd2 > div')
        result.extend(get_info(month2_elements))

        collection.insert_many(result)
        print(result)


def get_info(day_elements: ResultSet) -> list[dict]:
    """
    作品情報のリストを返す

    Args:
        day_elements (WebDriver):

    Returns:
        list[dict]: 辞書型の作品情報のリスト
    """
    result = list()

    for i_day in day_elements:
        i_day_class = '.' + '.'.join(i_day.get('class'))
        day = i_day.find('p').text
        genre_elements = i_day.select(f'{i_day_class} > div')
        genre_elements = [i for i in genre_elements if not i.get('class') == 'g-calen-all5']

        for i_genre in genre_elements[:-1]:
            genre_name = i_genre.find(class_='szam1').text
            li_elements = i_genre.find_all('li')

            for i_li in li_elements:
                movie_result = dict()
                movie_result['day'] = day
                movie_result['genre'] = genre_name
                a_element = i_li.select_one('div.firt-top1 > a')
                movie_result['title'] = a_element.text
                movie_result['url'] = a_element.get('href')
                result.append(movie_result)

    return result


if __name__ == '__main__':
    main()
