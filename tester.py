from pymongo import MongoClient
import TOKENS
import pickle
import utils.utils_text
import bson
mongo_client = MongoClient(
    "mongodb://{usn}:{pwd}@nadir.space".format(
        usn=TOKENS.MONGO_USN, pwd=TOKENS.MONGO_PASS))

overwatch_db = mongo_client.overwatch
print("asdf")
pipeline = [
    {"$group":
         {"_id"  : "$message_id",
          "dups" :
              {"$addToSet": "$_id"},
          "count":
              {"$sum": 1}}},
    {"$match":
         {"count":
              {"$gt": 1}}}]

duplicates = []
count = 0

for doc in overwatch_db.message_log.aggregate(pipeline, allowDiskUse=True):
    for objectid in doc["dups"][1:]:
        duplicates.append(str(objectid))
    if count % 5000 == 0:
        print(doc)
        print(count)
    count += 1
print(len(duplicates))
duplicates = utils.utils_text.split_list(duplicates, 100000)


for sublist in duplicates:
    sublist2 = [bson.objectid.ObjectId(dup_id) for dup_id in sublist]
    count = 0
    if count % 5000 == 0:
        print(count)
    # res = overwatch_db.message_log.delete_one({"_id":bson.objectid.ObjectId(dup_id)})
    res = overwatch_db.message_log.delete_many({"_id": {"$in": sublist2}})
    print(res.deleted_count)
    count+=1


# pickle.dump(duplicates, open("dups.p", "wb"))
#
#
# duplicates = pickle.load(open("dups.p", "rb"))
#
# print(len(duplicates))
# duplicates = utils.utils_text.split_list(duplicates, 1000)
# count = 0
# for sublist in duplicates:
#     print(sublist)
#     print("Parsing chunk {} of 547".format(count))
#     print("Sublist size: {}".format(len(sublist)))
#     res = overwatch_db.message_log.delete_many({"_id": {"$in": sublist}})
#     print("Removed " + res.deleted_count)
#     count += 1
#     print(res.deleted_count)


# overwatch_db.message_log.delete_many({"_id": {"$in": duplicates}})
