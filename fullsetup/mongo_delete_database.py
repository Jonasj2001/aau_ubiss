from pymongo import MongoClient
group = "aauiot"
client = MongoClient("mongodb://root:example@172.20.0.19")
client.drop_database(group)
