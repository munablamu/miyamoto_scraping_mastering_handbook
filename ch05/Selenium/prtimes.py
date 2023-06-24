"""
PRTIMESのデータを取得する
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
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

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        if not os.path.exists(ARTICLE_DATA_DIR):
            os.makedirs(ARTICLE_DATA_DIR)

        page_urls = list()
        for i_pagenum in range(1, 6):
            time.sleep(10)
            base_url = f'https://prtimes.jp/main/html/index/pagenum/{i_pagenum}'
            driver.get(base_url)
            article_urls = [i.get_attribute('href') for i in driver.find_elements(By.CLASS_NAME, 'list-article__link')]
            page_urls.extend(article_urls)

        page_urls = page_urls[:10] # スクレイピング量を削減

        for i_url in page_urls:
            key = os.path.splitext(i_url.split('/')[-1])[0]

            row_result = collection.find_one({'key': key})
            if not row_result:
                row_result = dict()
                driver.get(i_url)
                time.sleep(5)

                row_result['key'] = key
                row_result['url'] = i_url
                row_result['title'] = driver.find_element(By.CLASS_NAME, 'release--title').text
                row_result['company'] = driver.find_element(By.CLASS_NAME, 'company-name').text
                row_result['datetime'] = driver.find_element(By.TAG_NAME, 'time').text
                row_result['abstract'] = driver.find_element(By.CLASS_NAME, 'r-head').text

                collection.insert_one(row_result)
                article_path = os.path.join(ARTICLE_DATA_DIR, f'{row_result["key"]}.txt')
                with open(article_path, 'w') as f:
                    main_text = driver.find_element(By.CLASS_NAME, 'rich-text').text
                    f.write(main_text)

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
