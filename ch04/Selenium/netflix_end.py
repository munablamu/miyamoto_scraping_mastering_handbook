"""
Netflix配信終了予定の情報を取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
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

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = 'https://www.net-frx.com/p/netflix-expiring.html'
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        result = list()
        month1_elements = driver.find_elements(By.CSS_SELECTOR, '.data-fd1.goke3 > div')
        result.extend(get_info(month1_elements))

        month2_elements = driver.find_elements(By.CSS_SELECTOR, '.data-fd2 > div')
        result.extend(get_info(month2_elements))

        collection.insert_many(result)
        print(result)

    finally:
        driver.quit()


def get_info(day_elements: WebDriver) -> list[dict]:
    """
    作品情報のリストを返す

    Args:
        day_elements (WebDriver):

    Returns:
        list[dict]: 辞書型の作品情報のリスト
    """
    result = list()

    for i_day in day_elements:
        i_day_class = '.' + i_day.get_attribute('class').replace(' ', '.')
        day = i_day.find_element(By.TAG_NAME, 'p').get_attribute('textContent')
        genre_elements = i_day.find_elements(By.CSS_SELECTOR, f'{i_day_class} > div')
        genre_elements = [i for i in genre_elements if not i.get_attribute('class') == 'g-calen-all5']

        for i_genre in genre_elements:
            genre_name = i_genre.find_element(By.CLASS_NAME, 'szam1').get_attribute('textContent')
            li_elements = i_genre.find_elements(By.TAG_NAME, 'li')

            for i_li in li_elements:
                movie_result = dict()
                movie_result['day'] = day
                movie_result['genre'] = genre_name
                a_element = i_li.find_element(By.CSS_SELECTOR, 'div.firt-top1 > a')
                movie_result['title'] = a_element.get_attribute('textContent')
                movie_result['url'] = a_element.get_attribute('href')
                result.append(movie_result)

    return result


if __name__ == '__main__':
    main()
