import asyncio
import pickle
import textwrap

import discord
from fuzzywuzzy import process

import utils_text
from TOKENS import *
from utils_text import multi_block

# logging.basicConfig(level=logging.INFO)

poke_path = "C:\\Users\\Austin\\Desktop\\Programming\\Disc\\pokedraft\\"
with open(poke_path + "list.pickle", 'rb') as fp:
    poke_dict = pickle.load(fp)
    print(poke_dict)

client = discord.Client()
user_queue = asyncio.Queue()
registered = []
locked = []


@client.event
async def on_message(message_in):
    global user_queue
    global locked
    if message_in.content.startswith(".."):
        command = message_in.content.replace("..", "")
        command_list = command.split(" ")
        if command_list[0] == "draft":
            if message_in.author.id not in registered and message_in.author.id not in locked:
                await client.send_message(message_in.author, "You have registered for the draft in {ordinal} place. "
                                                             "Please wait.".format(
                                                                ordinal=utils_text.get_ordinal(user_queue.qsize() + 2)))
                await user_queue.put(message_in.author)
                locked.append(message_in.author.id)
            else:
                await client.send_message(message_in.author, "You are already in the queue.")
        pass


@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)


async def process_queue(member_queue):
    """
    :type member_queue: Queue
    """
    await client.wait_until_ready()
    while not client.is_closed:
        member = await member_queue.get()
        await draft(member)
        await save_pickle("list.pickle", poke_dict)


async def draft(member):
    global poke_dict
    await client.send_message(member, "Beginning draft...")
    drafted_pokemon = [pokemon for pokemon in poke_dict.keys() if poke_dict[pokemon]]
    undrafted_pokemon = [pokemon for pokemon in poke_dict.keys() if not poke_dict[pokemon]]
    print(undrafted_pokemon)
    await client.send_message(member, "List of already drafted pokemon:")
    await send(member, "\n".join(drafted_pokemon), "text")
    await client.send_message(member, "Please select a pokemon")

    def select_check(msg):
        result_pokemon = process.extractOne(msg.content, undrafted_pokemon)
        if not msg.channel.is_private:
            return False
        if result_pokemon[1] > 90:
            print(result_pokemon)
            return True
        else:
            def send_msg():
                yield from client.send_message(msg.channel if msg.channel else msg.author,
                                               "Did not recognize the pokemon. Please check your spelling and try "
                                               "again.")

            discord.compat.create_task(send_msg(), loop=client.loop)
            return False

    selection_msg = await client.wait_for_message(timeout=30, author=member, check=select_check)
    if not selection_msg:
        await client.send_message(member, "You have timed out. Please rejoin the draft in the main server with ..draft")
        return

    selected_mon = process.extractOne(selection_msg.content, undrafted_pokemon)[0]
    await client.send_message(member, "You have selected {mon}.".format(mon=selected_mon))
    result = await confirm(member, member)
    if result:
        poke_dict[selected_mon] = str(member.id)
    else:
        await client.send_message(member, "You have timed out. Please restart")
        print("Stacking up")
        await draft(member)
        print("Stacking down")
    registered.append(member.id)
    return


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


async def save_pickle(filename, item):
    with open(poke_path + filename, 'wb') as pickled_filed:
        pickle.dump(item, pickled_filed)


async def confirm(member, target, private_message=True):
    await client.send_message(target, "Are you sure? (yes/no)")

    def confirm_check(confirm_msg):
        if private_message:
            if confirm_msg.channel.is_private:
                return True
        else:
            if target != confirm_msg.channel:
                return False
        return confirm_msg.content in ["yes", "y", "true", "+", "on", "no", "n", "false", "-", "off"]

    msg = await client.wait_for_message(timeout=15, author=member, check=confirm_check)
    if not msg:
        return None
    return utils_text.parse_bool(msg.content)


client.loop.create_task(process_queue(user_queue))
client.run(TEST2_AUTH, bot=True)
