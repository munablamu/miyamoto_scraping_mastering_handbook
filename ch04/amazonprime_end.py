"""
Amazonプライムビデオ配信終了予定の情報を取得する
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

SLEEP_TIME = 5
CSV_NAME = 'output/amazonprime_end.csv'


def main() -> None:
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        target_url = 'https://animephilia.net/amazon-prime-video-expiring-calendar/'
        driver.get(target_url)
        time.sleep(SLEEP_TIME)

        results = list()
        for i in range(3):
            results.extend(get_info(driver))
            calender_update(driver)
            time.sleep(SLEEP_TIME)

        pd.DataFrame(results).to_csv(CSV_NAME, index=False)
        print(pd.DataFrame(results))

    finally:
        driver.quit()


def scroll_to_see_element(driver: WebDriver, by: str, value: str) -> None:
    element = driver.find_element(by, value)
    driver.execute_script("arguments[0].scrollIntoView();", element)


def calender_update(driver: WebDriver) -> None:
    scroll_to_see_element(driver, By.CLASS_NAME, 'next')
    driver.find_element(By.CLASS_NAME, 'next').click()


def get_info(driver: WebDriver) -> list:
    results = list()
    day_elements = driver.find_elements(By.CLASS_NAME, 'day-column')

    for i_day in day_elements:
        day_data = i_day.get_attribute('data-date')
        content_elements = i_day.find_elements(By.CSS_SELECTOR, '.event.upcoming')

        for i_content in content_elements:
            content_result = dict()
            content_result['day'] = day_data
            a_element = i_content.find_element(By.CLASS_NAME, 'content-title')
            content_result['title'] = a_element.text
            content_result['url'] = a_element.get_attribute('href')
            results.append(content_result)

    return results


if __name__ == '__main__':
    main()
