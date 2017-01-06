"""Provide an asynchronous equivalent *to exec*."""

# from . import compat
import discord
import logging

logging.basicConfig(level=logging.INFO)

from pip.utils import logging


# from io import BytesIO, StringIO
# from concurrent.futures import ProcessPoolExecutor
# import pandas as pd

client = discord.Client()

@client.event
async def on_channel_create(channel):
    if channel.server.id == "255438591214223362":
        await client.send_message(client.get_channel("255438591214223362"), "Registered channel creation, \n{}".format(channel.name))


@client.event
async def on_channel_delete(channel):
    if channel.server.id == "255438591214223362":
        await client.send_message(client.get_channel("255438591214223362"),
                                  "Registered channel deletion, \n{}\n{}".format(channel.name, channel.topic))

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


# noinspection PyShadowingNames,PyBroadException,PyBroadException,PyBroadException
@client.event
async def on_message(mess):
    pass


client.run("mfa.IJIfgMg4yJJX3hAmWEKLTT7KvOmBokyWayEw5BrOj6SkVz4RYFxJZK5GXAQe8UbH_CCN9o7thVJFD7H6ErHZ", bot=False)
