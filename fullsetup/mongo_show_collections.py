from pymongo import MongoClient

client = MongoClient("mongodb://root:example@172.20.0.19")
dbs = client.list_database_names()

for db in dbs:
	mydb=client[str(db)]
	collections=mydb.list_collection_names()
	print( db, "has the folllwing collections", collections)
