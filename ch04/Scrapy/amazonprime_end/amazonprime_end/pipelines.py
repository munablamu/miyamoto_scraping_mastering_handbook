# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from jsonschema import validate
from pymongo import MongoClient

from amazonprime_end.spiders.amazonprime_end import extract_key

class ValidationPipeline:
    """
    Itemを検証するPipeline。
    """
    schema = {
        'type': 'object',
        'properties': {
            'key': {
                'type': 'string'
            },
            'day': {
                'type': 'string'
            },
            'title': {
                'type': 'string'
            },
            'url': {
                'type': 'string'
            }
        },
        'required': ['key', 'day', 'title', 'url']
    }


    def process_item(self, item, spider):
        validate(dict(item), self.schema)
        return item


class MongoPipeline:
    """
    ItemをMongoDBに保存するPipeline。
    """
    def open_spider(self, spider):
        """
        Spiderの開始時にMongoDBに接続する。

        Args:
            spider (_type_): _description_
        """
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['scraping']
        self.db[spider.name].drop()
        self.collection = self.db[spider.name]
        self.collection.create_index('key', unique=True)


    def close_spider(self, spider):
        """
        Spiderの終了時にMongoDBへの接続を切断する。

        Args:
            spider (_type_): _description_
        """
        self.client.close()


    def process_item(self, item, spider):
        """
        Itemをコレクションに追加する。

        Args:
            item (_type_): _description_
            spider (_type_): _description_
        """
        self.collection.insert_one(dict(item))
        return item
