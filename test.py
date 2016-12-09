import asyncio

import motor.motor_asyncio
import pymongo

mongo_client = motor.motor_asyncio.AsyncIOMotorClient()

async def main():
    await mongo_client.overwatch.trigger_str.create_index([("string", pymongo.DESCENDING)], unique=True)
    await mongo_client.overwatch.auths.create_index([("userid", pymongo.DESCENDING)], unique=True)

async def asdf():
    tag_list = await mongo_client.overwatch.trigger_str_collection.find(query={}, projection="trigger_str").to_list()

asyncio.get_event_loop().run_until_complete(main())
asyncio.get_event_loop().close()
