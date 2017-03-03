import textwrap

import discord
from pytba import api as tba
import TOKENS
from utils import utils_text
from utils.utils_text import *

tba.set_api_key("Austin Zhang", "1072bot ", "1.0")
import pyfav

import logging

logging.basicConfig(level=logging.DEBUG)

client = discord.Client()


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


@client.event
async def on_message(message_in):
    if message_in.author.id == client.user.id:
        return
    await client.send_message(message_in.channel, "Resp")
    print(message_in.content)
    trigger = ",,"
    if not message_in.content.startswith(trigger):
        return
    command_list = message_in.content.replace(trigger, "").split(" ")

    if command_list[0] == "query":
        team_number = command_list[1]
        print("firing query")
        if not utils_text.is_int(team_number):
            pass  # wrong input
        team = tba.team_get(team_number)
        if not team:
            pass  # wrong input
        print("Team got")
        embed = await output_team_embed(team)
        print("embed found")
        await client.send_message(message_in.channel, content=None, embed=embed)
    if command_list[0] == "queryevent":
        event_id = command_list[1]
        print("firing team query")
        event = tba.event_get(event_id)
        embed = await output_event_embed(event)
        await client.send_message(message_in.channel, content=None, embed=embed)
    if command_list[0] == "reboot":
        await client.logout()
    if command_list[0] == "importevent":
        pass


async def output_event_embed(event):
    name = event.info["name"]
    embed = discord.Embed(title="[{event_code}] {name}'s  team  info".format(name=name.replace(" ", "  "),
                                                                             event_code=event.info[
                                                                                 "key"]) + ' ' * 40 + "​​​​​​",
                          type="rich")
    embed.add_field(name="Website", value=event.info["website"], inline=False)
    embed.add_field(name="Start Date", value=event.info["start_date"], inline=True)
    embed.add_field(name="End Date", value=event.info["end_date"], inline=True)
    embed.add_field(name="Week", value=event.info["week"], inline=True)
    embed.add_field(name="Address", value=event.info["venue_address"], inline=False)
    thumb = pyfav.pyfav.get_favicon_url(event.info["website"])
    embed.set_thumbnail(url=thumb)
    return embed


# @fuckit
async def output_team_embed(team_dict):
    nickname = team_dict["nickname"]
    embed = discord.Embed(title="[{number}] {name}  info".format(name=nickname.replace(" ", "  "), number=team_dict[
        "team_number"]) + ' ' * 60 + "​​​​​​", type="rich")


    location = team_dict["locality"] + ", " + team_dict["region"]
    embed.add_field(name="Motto", value=team_dict["motto"], inline=False)
    embed.add_field(name="Website", value=team_dict["website"], inline=False)
    embed.add_field(name="Founding Year", value=team_dict["rookie_year"])
    embed.add_field(name="Location", value=location, inline=False)
    print(team_dict)
    # if team_dict["team_number"] == "1072":
    #     return embed
    thumb = pyfav.pyfav.get_favicon_url(team_dict["website"])
    if thumb:
        embed.set_thumbnail(url=thumb)
    print("embed got")
    print(embed.to_dict())
    return embed


async def get_input(from_user, regex):
    def check(message):
        if regex_test(regex, message.content):
            return True
        return False

    message_in = await client.wait_for_message(author=from_user, check=check)



async def send(destination, text, send_type):
    if isinstance(destination, str):
        destination = await client.get_channel(destination)

    if send_type == "rows":
        message_list = multi_block(text, True)
        for message in message_list:
            await client.send_message(destination, "```" + message + "```")
        return
    if send_type == "list":
        text = str(text)[1:-1]

    text = str(text)
    text = text.replace("\n", "<NL<")
    lines = textwrap.wrap(text, 2000, break_long_words=False)

    for line in lines:
        if len(line) > 2000:
            continue
        line = line.replace("<NL<", "\n")
        await client.send_message(destination, line)


client.run(TOKENS.ROBO_TOKEN, bot=True)
