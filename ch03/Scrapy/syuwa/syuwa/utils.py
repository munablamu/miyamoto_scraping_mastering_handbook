from pymongo import MongoClient


class MongoMixin:
    def setup_mongo(self, mongodb_uri, mongodb_database, mongodb_collection):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[mongodb_database]
        self.collection = self.db[mongodb_collection]
        self.collection.create_index('key', unique=True)

    def close_mongo(self):
        self.client.close()
