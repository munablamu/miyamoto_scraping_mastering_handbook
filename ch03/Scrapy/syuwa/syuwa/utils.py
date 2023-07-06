from pymongo import MongoClient


class MongoMixin:
    def setup_mongo(self, mongo_uri, mongo_db, collection_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_db]
        self.collection = self.db[collection_name]
        self.collection.create_index('key', unique=True)

    def close_mongo(self):
        self.client.close()
