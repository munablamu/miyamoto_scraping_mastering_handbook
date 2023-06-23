"""
connpassのデータを取得する
"""
import pandas as pd
import requests
import json
from pymongo import MongoClient
from fake_useragent import UserAgent

COLLECTION_NAME = 'connpass'


def get_events(keyword, ym):
    client = MongoClient('localhost', 27017)
    if COLLECTION_NAME in client.scraping.list_collection_names():
        client.scraping[COLLECTION_NAME].drop()
    collection = client.scraping[COLLECTION_NAME]

    base_url = 'https://connpass.com/api/v1/event/?'
    keyword_query = f'keyword={keyword}'
    ym_query = f'ym={ym}'
    query = base_url + '&'.join([keyword_query, ym_query])

    # User-Agentを偽装する
    ua = UserAgent()
    headers = {'User-Agent': str(ua.chrome)}

    event_json = json.loads(requests.get(query, headers=headers).text)['events']
    df = pd.DataFrame(event_json)
    df = df.loc[:, ['event_id', 'title', 'catch', 'started_at', 'event_url']]
    event_dict = df.to_dict('records')

    collection.insert_many(event_dict)


if __name__ == '__main__':
    KEYWORD = 'Python'
    YM = 202207
    get_events(KEYWORD, YM)
