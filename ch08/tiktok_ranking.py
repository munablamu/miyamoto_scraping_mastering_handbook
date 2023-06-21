"""
Tiktokerのランキング情報を取得する
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

SLEEP_TIME = 4
CSV_NAME = 'output/tiktok_ranking.csv'


def main():
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())

        urls = list()
        for i_page_num in range(1, 21):
            update_page_num(driver, i_page_num)
            time.sleep(SLEEP_TIME)
            urls.extend(get_item_urls(driver))

        urls = urls[:10] # データの量を減らす

        result = list()
        for i_rank, i_url in enumerate(urls, start=1):
            driver.get(i_url)
            time.sleep(SLEEP_TIME)
            user_dict = get_item_info(driver)
            user_dict['ranking'] = i_rank
            result.append(user_dict)

        pd.DataFrame(result).to_csv(CSV_NAME, index=False)

    finally:
        driver.quit()


def update_page_num(driver, page_num):
    driver.get(f'https://tiktok-ranking.userlocal.jp/?page={page_num}')


def get_item_urls(driver):
    ranking_element = driver.find_element(By.CLASS_NAME, 'rankers')
    a_elements = ranking_element.find_elements(By.CLASS_NAME, 'no-decorate')
    return [i.get_attribute('href') for i in a_elements]


def get_item_info(driver):
    result = dict()
    result['rank_page'] = driver.current_url
    result['name'] = driver.find_element(By.CSS_SELECTOR, '.show-name.col-12').text
    result['id'] = driver.find_element(By.CSS_SELECTOR, '.col-12.show-id').text
    result['comment'] = driver.find_element(By.CSS_SELECTOR, '.col-12.show-description').text
    result['posts_num'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[0].text
    result['follower_num'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[1].text
    result['favs'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[3].text
    result['favs_mean'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[4].text
    result['favs_rate'] = driver.find_elements(By.CSS_SELECTOR, '.col-7.stats-num')[5].text
    return result


if __name__ == '__main__':
    main()
