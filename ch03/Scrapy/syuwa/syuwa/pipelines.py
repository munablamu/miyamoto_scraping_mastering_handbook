# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from jsonschema import validate

from syuwa.utils import MongoMixin


class ValidationPipeline:
    """
    Itemを検証するPipeline。
    """
    schema = {
        'type': 'object',
        'properties': {
            'key': {
                'type': 'string',
                'pattern': r'^\d+$'
            },
            'title': {
                'type': 'string'
            },
            'price': {
                'type': 'integer'
            },
            'author': {
                'type': 'string'
            },
            'describe': {
                'type': 'string'
            }
        },
        'required': ['key', 'title', 'price', 'author']
    }


    def process_item(self, item, spider):
        validate(dict(item), self.schema)
        return item


class MongoPipeline(MongoMixin):
    """
    ItemをMongoDBに保存するPipeline。
    """
    def open_spider(self, spider):
        """
        Spiderの開始時にMongoDBに接続する。

        Args:
            spider (_type_): _description_
        """
        self.setup_mongo(
            'mongodb://localhost:27017',
            'scraping',
            'syuwa'
        )

    def close_spider(self, spider):
        """
        Spiderの終了時にMongoDBへの接続を切断する。

        Args:
            spider (_type_): _description_
        """
        self.close_mongo()


    def process_item(self, item, spider):
        """
        Itemをコレクションに追加する。

        Args:
            item (_type_): _description_
            spider (_type_): _description_
        """
        self.collection.insert_one(dict(item))
        return item
