import pymongo

mongo_client_static = pymongo.MongoClient("mongodb://nadir.space:27017")


print(mongo_client_static.database_names())