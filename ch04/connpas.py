"""
compassのデータを取得する
"""
import pandas as pd
import requests
import json


def get_events(keyword, ym, output):
    base_url = 'https://connpass.com/api/v1/event/?'
    keyword_query = f'keyword={keyword}'
    ym_query = f'ym={ym}'
    query = base_url + '&'.join([keyword_query, ym_query])

    event_json = json.loads(requests.get(query).text)['events']
    df = pd.DataFrame(event_json)
    df = df.loc[:, ['title', 'catch', 'started_at', 'event_url']]

    df.to_csv(output, index=False)


if __name__ == '__main__':
    KEYWORD = 'Python'
    YM = 202207
    OUTPUT = 'output/connpass.csv'
    get_events(KEYWORD, YM, OUTPUT)
