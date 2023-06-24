"""
yahooニュースのデータを取得する
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient

SLEEP_TIME = 4
COLLECTION_NAME = 'yahoo_news'
FILE_DIR = 'output'


def main() -> None:
    """
    クローラーのメイン処理
    """
    client = MongoClient('localhost', 27017)
    collection = client.scraping[COLLECTION_NAME]
    collection.create_index('key', unique=True)

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())

        if not os.path.exists(FILE_DIR):
            os.makedirs(FILE_DIR)
        target_url = 'https://news.yahoo.co.jp/'
        driver.get(target_url)
        time.sleep(SLEEP_TIME)
        article_urls = get_item_urls(driver)
        # データの量を減らす
        # article_urls = article_urls[:5]

        for i_url in article_urls:
            key = extract_key(i_url)

            result = collection.find_one({'key': key})
            if not result:
                print(i_url)
                driver.get(i_url)
                time.sleep(SLEEP_TIME)

                if 'article' in i_url:
                    result = get_article_info(driver, key)
                elif 'byline' in i_url:
                    result = get_byline_info(driver, key)

                collection.insert_one(result)

    finally:
        driver.quit()


def get_item_urls(driver: WebDriver) -> list:
    """
    一覧ページからURLを取得する

    Args:
        driver (WebDriver):

    Returns:
        list: 詳細ページのURL
    """
    contents_element = driver.find_element(By.ID, 'contentsWrap')
    ul_element = contents_element.find_element(By.TAG_NAME, 'ul')
    urls = [i.get_attribute('href') for i in ul_element.find_elements(By.TAG_NAME, 'a')]

    results = list()
    for i_url in urls:
        driver.get(i_url)
        time.sleep(SLEEP_TIME)
        article_element = driver.find_element(By.ID, 'uamods-pickup')
        a_element = article_element.find_element(By.TAG_NAME, 'a')
        results.append(a_element.get_attribute('href'))

    return ['/'.join(i.split('/')[:5]) for i in results]


def get_article_info(driver: WebDriver, key: str) -> dict:
    """
    URLにarticleが含まれる詳細ページの情報を取得する

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: 記事の情報
    """
    result = dict()
    result['key'] = key
    article_element = driver.find_element(By.TAG_NAME, 'article')
    result['title'] = article_element.find_element(By.TAG_NAME, 'h1').text
    result['post_time'] = article_element.find_element(By.TAG_NAME, 'time').text
    result['file_name'] = f'{result["key"]}.txt'

    content = str()
    while True:
        article_element = driver.find_element(By.CLASS_NAME, 'article_body')
        content = content + '\n' + article_element.text
        element_below_article = driver.execute_script('return arguments[0].nextElementSibling', article_element)
        if '次へ' in element_below_article.text:
            li_element = element_below_article.find_elements(By.TAG_NAME, 'li')[-1]
            if li_element.find_elements(By.TAG_NAME, 'a') and ('次へ' in li_element.text):
                li_element.click()
                time.sleep(SLEEP_TIME)
            else:
                break
        else:
            break

    file_path = os.path.join(FILE_DIR, result['file_name'])
    with open(file_path, 'w') as f:
        f.write(content)

    return result


def get_byline_info(driver: WebDriver, key: str) -> dict:
    """
    URLにbylineが含まれる詳細ページから記事の情報を取得する

    Args:
        driver (WebDriver):
        key (str): キー

    Returns:
        dict: 記事の情報
    """
    result = dict()
    result['key'] = key
    article_element = driver.find_element(By.TAG_NAME, 'article')
    result['title'] = article_element.find_element(By.TAG_NAME, 'h1').text
    result['post_time'] = article_element.find_element(By.TAG_NAME, 'time').time
    result['file_name'] = f'{result["key"]}.txt'

    file_path = os.path.join(FILE_DIR, result['file_name'])
    with open(file_path, 'w') as f:
        f.write(driver.find_element(By.CLASS_NAME, 'articleBody').text)

    return result


def extract_key(url: str) -> str:
    """
    URLからキーを抜き出す

    Args:
        url (str): 対象URL

    Returns:
        str: キー
    """
    return url.split('/')[-1]


if __name__ == '__main__':
    main()
