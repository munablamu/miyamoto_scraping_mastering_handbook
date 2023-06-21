"""
全国法人リストから会社情報を取得
"""
import time
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

SLEEP_TIME = 3
CSV_NAME = 'output/hojin.csv'
BASE_URL = 'https://houjin.jp/search?keyword=%E3%82%BD%E3%83%8B%E3%83%83%E3%82%AF&pref_id='


def main() -> None:
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = BASE_URL
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        page_num = 1
        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(driver)

            if len(urls) == 0:
                break
            else:
                item_urls.extend(urls)
                page_num += 1
                update_page_num(driver, page_num)

        item_urls = item_urls[:5] # データ量を減らす

        item_infos = list()
        for i_url in item_urls:
            print(i_url)
            time.sleep(SLEEP_TIME)
            driver.get(i_url)
            item_infos.append(get_item_info(driver))

        pd.DataFrame(item_infos).to_csv(CSV_NAME, index=False)

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, page_num: int) -> None:
    base_url = BASE_URL
    next_url = base_url + f'&page={page_num}'
    driver.get(next_url)


def get_item_urls(driver: WebDriver) -> list:
    cop_item_elements = driver.find_elements(By.CLASS_NAME, 'c-corp-item')
    return [i.find_element(By.TAG_NAME, 'a').get_attribute('href') for i in cop_item_elements]


def get_item_info(driver: WebDriver) -> dict:
    corp_info_table_element = driver.find_element(By.CLASS_NAME, 'corp-info-table')
    corp_info_html = corp_info_table_element.get_attribute('outerHTML')
    corp_info_df = pd.read_html(corp_info_html)[0]
    keys = corp_info_df.iloc[:, 0].tolist()
    vals = corp_info_df.iloc[:, 1].tolist()
    corp_info = {i_key: i_val for i_key, i_val in zip(keys, vals)}
    return corp_info


if __name__ == '__main__':
    main()