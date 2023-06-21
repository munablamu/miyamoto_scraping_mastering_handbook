"""
suumoから物件情報を収集する
"""
import time
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

SLEEP_TIME = 5
CSV_NAME = 'output/suumo.csv'
BASE_URL = 'https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&pc=30&smk=&po1=25&po2=99&shkr1=03&shkr2=03&shkr3=03&shkr4=03&rn=0350&ek=035009200&ra=013&cb=0.0&ct=6.0&md=03&et=9999999&mb=0&mt=9999999&cn=9999999&fw2='


def main() -> None:
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = BASE_URL
        driver.get(target_url)

        page_num = 1
        item_urls = list()
        while True:
            time.sleep(SLEEP_TIME)
            urls = get_item_urls(driver)
            item_urls.extend(urls)
            if is_last_page(driver):
                break
            else:
                page_num += 1
                update_page_num(driver, page_num)

        item_infos = list()
        for i_url in item_urls:
            print(i_url)
            time.sleep(SLEEP_TIME)
            driver.get(i_url)
            item_infos.append(get_item_info(driver))

        pd.DataFrame(item_infos).to_csv(CSV_NAME)

    finally:
        driver.quit()


def update_page_num(driver: WebDriver, page_num: int) -> None:
    base_url = BASE_URL
    next_url = base_url + f'&pn={page_num}'
    driver.get(next_url)


def get_item_urls(driver: WebDriver) -> list:
    a_elements = driver.find_elements(By.CLASS_NAME, 'cassetteitem_other-linktext')
    return [i.get_attribute('href') for i in a_elements]


def get_item_info(driver: webdriver) -> dict:
    table_element = driver.find_element(By.CSS_SELECTOR, '.data_table.table_gaiyou')
    df = pd.read_html(table_element.get_attribute('outerHTML'))[0]
    first_df = df.iloc[:, :2] # 3,4列目を無視してしまっている
    keys = [i.replace('  ヒント', '') for i in first_df.iloc[:, 0].tolist()]
    vals = first_df.iloc[:, 1].to_list()
    result = {i_key: i_val for i_key, i_val in zip(keys, vals)}

    result['title'] = driver.find_element(By.TAG_NAME, 'h1').text
    result['price'] = driver.find_element(By.CLASS_NAME, 'property_view_note-emphasis').text
    result['id'] = driver.current_url.split('/')[-2]
    result['url'] = driver.current_url
    print(result)
    return result


def is_last_page(driver: WebDriver) -> bool:
    paging_elements = driver.find_elements(By.CLASS_NAME, 'pagination-parts')
    paging_text = [i.text for i in paging_elements]
    return not '次へ' in paging_text


if __name__ == '__main__':
    main()
