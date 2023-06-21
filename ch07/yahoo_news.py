"""
yahooニュースのデータを取得する
"""
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

SLEEP_TIME = 4
CSV_NAME = 'output/yahoo_news.csv'
FILE_DIR = 'output'


def main():
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

        result = list()
        for i_url in article_urls:
            print(i_url)
            driver.get(i_url)
            time.sleep(SLEEP_TIME)

            if 'article' in i_url:
                result.append(get_article_info(driver))
            elif 'byline' in i_url:
                result.append(get_byline_info(driver))

        pd.DataFrame(result).to_csv(CSV_NAME, index=False)

    finally:
        driver.quit()


def get_item_urls(driver):
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


def get_article_info(driver):
    result = dict()
    result['id'] = driver.current_url.split('/')[-1]
    article_element = driver.find_element(By.TAG_NAME, 'article')
    result['title'] = article_element.find_element(By.TAG_NAME, 'h1').text
    result['post_time'] = article_element.find_element(By.TAG_NAME, 'time').text
    result['file_name'] = f'{result["id"]}.txt'

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


def get_byline_info(driver):
    result = dict()
    result['id'] = driver.current_url.split('/')[-1]
    article_element = driver.find_element(By.TAG_NAME, 'article')
    result['title'] = article_element.find_element(By.TAG_NAME, 'h1').text
    result['post_time'] = article_element.find_element(By.TAG_NAME, 'time').time
    result['file_name'] = f'{result["id"]}.txt'

    file_path = os.path.join(FILE_DIR, result['file_name'])
    with open(file_path, 'w') as f:
        f.write(driver.find_element(By.CLASS_NAME, 'articleBody').text)

    return result


if __name__ == '__main__':
    main()