import ast

from utils import utils_file


def set(data, entry):
    """

    :type entry: str
    :type data: str
    """

    if data == "blacklist_str":
        file_path = PATHS["comms"] + "blacklist_str.txt"
    elif data == "art_auths":
        file_path = PATHS["comms"] + "art_credentials.txt"
    elif data == "hots_auths":
        file_path = PATHS["comms"] + "hots_credentials.txt"
    elif data == "lfg_auths":
        file_path = PATHS["comms"] + "lfg_credentials.txt"
    else:
        file_path = PATHS["comms"] + data

    utils_file.append_line(file_path, entry)


def get(data):
    if data == "blacklist_str":
        file_path = PATHS["comms"] + "blacklist_str.txt"
    elif data == "art_auths":
        file_path = PATHS["comms"] + "art_credentials.txt"
    elif data == "hots_auths":
        file_path = PATHS["comms"] + "hots_credentials.txt"
    elif data == "lfg_auths":
        file_path = PATHS["comms"] + "lfg_credentials.txt"
    else:
        file_path = PATHS["comms"] + data
    return utils_file.read_file(file_path)
