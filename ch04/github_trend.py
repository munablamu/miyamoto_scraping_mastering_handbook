"""
Githubトレンドのデータを取得する
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
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

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        url = 'https://github.com/trending'
        driver.get(url)
        time.sleep(SLEEP_TIME)

        box_row_elements = driver.find_elements(By.CLASS_NAME, 'Box-row')
        for i_box in box_row_elements:
            row_data = dict()
            row_data['title'] = i_box.find_element(By.TAG_NAME, 'h2').text
            row_data['url'] = i_box.find_element(By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'a').get_attribute('href')
            lang_elements = i_box.find_elements(By.CSS_SELECTOR, '.d-inline-block.ml-0.mr-3')
            row_data['lang'] = lang_elements[0].text if len(lang_elements) == 1 else None
            row_data['total_star'] = i_box.find_elements(By.CSS_SELECTOR, '.Link--muted.d-inline-block.mr-3')[0].text
            row_data['fork'] = i_box.find_elements(By.CSS_SELECTOR, '.Link--muted.d-inline-block.mr-3')[1].text
            row_data['todays_star'] = i_box.find_element(By.CSS_SELECTOR, '.d-inline-block.float-sm-right').text.replace('stars today', '')
            collection.insert_one(row_data)

            print(row_data)

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
