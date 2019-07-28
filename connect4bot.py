import logging
import discord
import lux
import pprint
import CONSTANTS
import itertools
import CONFIG_DEFAULT
import ast
import numpy as np

pers_d = {}
pers_l = []
pers = None

games = {}

logging.basicConfig(level=logging.INFO)
CONFIG = lux.config.Config(botname="CONNECT4", config_defaults=CONFIG_DEFAULT.CONNECT4).load()


def check_auth(ctx: lux.contexter.Contexter) -> bool:
    return True


client = lux.client.Lux(CONFIG, auth_function=check_auth,
                        activity=discord.Game(name="Connect 4!!!"))


@client.command(authtype="whitelist", name="start")
async def start(ctx: lux.contexter.Contexter):
    print(ctx.called_with)
    if not len(ctx.called_with["args"]):
        return f"Call with `start rowxcolumn number`"
    dims, connect_count = ctx.called_with["args"].split(" ")
    rows, cols = dims.split("x")
    games[ctx.m.channel.id] = {"count": int(connect_count), "boards": [np.zeros([int(rows), int(cols)], dtype=int)], "meta": {}}

    return f"Started a new game in {ctx.m.channel.mention} with {rows} rows, {cols} cols. Connect {connect_count} to win!\n" + format_board(games[ctx.m.channel.id]["boards"][-1])


def get_diags(lst, row, col):

    print(lst)
    print(f"{row}, {col}")
    major = np.diagonal(lst, offset=(col - row))
    minor = np.diagonal(np.rot90(lst), offset=-lst.shape[1] + (col + row) + 1)

    return [major, minor]


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

def any_subseq(seq: np.ndarray, subseq : np.ndarray):
    print(f"wid: {subseq.shape}")
    if seq.shape[0] < subseq.shape[0]:
        return False
    print(rolling_window(seq, subseq.shape[0]))

    for stack in rolling_window(seq, subseq.shape[0]):
        if stack.shape == subseq.shape and (stack == subseq).all():
            print(f"matching {stack} {subseq}")
            return True
    return False

def find_subsequence(seq, subseq):
    target = np.dot(subseq, subseq)
    candidates = np.where(np.correlate(seq,
                                       subseq, mode='valid') == target)[0]
    # some of the candidates entries may be false positives, double check
    check = candidates[:, np.newaxis] + np.arange(len(subseq))
    mask = np.all((np.take(seq, check) == subseq), axis=-1)
    return candidates[mask]


def check_victory(game, row, col):
    board = game["boards"][-1]
    count = game["count"]
    axes = get_diags(board, row, col) + [board[row], board[:, col]]
    print(axes)
    p1 = np.repeat(1, count)
    p2 = np.repeat(2, count)

    if any(any_subseq(ax, p1) for ax in axes):
        return "p1"
    if any(any_subseq(ax, p2) for ax in axes):
        return "p2"


def new_board_with_move(board: np.ndarray, column: int, player):
    new_board = board.copy()
    col = new_board[:, column]
    # print(col)
    okay_placements = np.where(col == 0)[0]
    # print(okay_placements)
    if okay_placements.shape[0] == 0:
        return None, None, None
    row_place = okay_placements[-1]
    new_board[row_place, column] = player
    # print(f" returning {new_board}, {row_place}, {column}")
    return new_board, row_place, column


@client.command(authtype="whitelist", name="undo")
async def undo(ctx: lux.contexter.Contexter):
    if ctx.m.channel.id in games:
        games[ctx.m.channel.id]["boards"] = games[ctx.m.channel.id]["boards"][:-1]
        return f"Rolled board back to \n{format_board(games[ctx.m.channel.id]['boards'][-1])}"
    else:
        return f"No running games in channel :("


@client.command(authtype="whitelist", name="p")
async def place(ctx: lux.contexter.Contexter):
    position = int(ctx.called_with["args"])
    if ctx.m.channel.id in games:
        game = games[ctx.m.channel.id]
        # initialize two players
        print(game["meta"])
        if "p1" not in game["meta"]:
            game["meta"]["p1"] = ctx.m.author.id
            game["meta"]["current"] = "p1"
        else:
            if "p2" not in game["meta"]:
                if ctx.m.author.id != game["meta"]["p1"]:
                    game["meta"]["p2"] = ctx.m.author.id
        # Play
        if game["meta"]["p1"] == ctx.m.author.id:
            if game["meta"]["current"] != "p1":
                return f"It is not your turn :("
            # P1's turn, P1 is author!
            print(f"boards: {game['boards'][-1]} \n position {position}")
            board, row, col = new_board_with_move(game["boards"][-1], position, 1)
            if board is None:
                return "Invalid placement! try again :("
            game["boards"].append(board)
            if check_victory(game=game, row=row, col=col):
                return f"{format_board(board)}\nPlayer 2 <@!{ctx.m.author.id}> winner!!!!!!!!"
            game["meta"]["current"] = "p2"
            return format_board(game["boards"][-1])

        elif game["meta"]["p2"] == ctx.m.author.id:
            if game["meta"]["current"] != "p2":
                return f"It is not your turn :("
            board, row, col = new_board_with_move(game["boards"][-1], position, 2)
            if board is None:
                return "Invalid placement! try again :("
            game["boards"].append(board)
            if check_victory(game=game, row=row, col=col):
                return f"{format_board(board)}\nPlayer 1 <@!{ctx.m.author.id}> winner!!!!!!!!"
            game["meta"]["current"] = "p1"
            return format_board(game["boards"][-1])

        else:
            return f"You are not a player! :("

    else:
        return f"No games running in {ctx.m.channel.mention}! `start` to begin one"


@client.command(authtype="whitelist", name="end")
async def end(ctx: lux.contexter.Contexter):
    del games[ctx.m.channel.id]
    return f"Manually ended the game in {ctx.m.channel.mention}."


num_map = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
piece_map = [":white_circle:", ":red_circle:", ":large_blue_circle:"]


def format_board(arr: np.ndarray):
    rows, cols = arr.shape
    cols_nums = [num_map[x % 10] for x in range(cols)]
    header = f"{''.join(cols_nums)}"
    li = arr.tolist()
    board = "\n".join(["".join(piece_map[x] for x in row) for row in li])

    return f"{header}\n{board}\n{header}"


client.run(CONFIG.TOKEN, bot=True)
