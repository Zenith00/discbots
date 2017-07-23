import contextlib
import json

import StringIO
import regex as re
import copy
import urllib.request
from datetime import datetime, timedelta
import dateparser
import traceback
# from pyshorteners import Shortener
import math
import textwrap

import requests
import sys

def regex_test(reg_str, string):
    reg = re.compile(reg_str, re.IGNORECASE)
    match = reg.search(string)
    return match

def is_int(string):
    try:
        int(string)
        return True
    except:
        return False

def parse_bool(string) -> bool:
    """
    :type string: str
    """
    if any(substring in string for substring in ["yes", "y", "true", "+", "on"]):
        return True
    return False

def multi_regex(reg_list, string):
    for reg in reg_list:
        if regex_test(reg, string):
            return True
    return False

def format_rows(list_of_rows):
    widths = generate_widths(list_of_rows=list_of_rows)
    list_of_blocks = []
    block = ""
    for row in list_of_rows:
        new_item = format_row_to_widths(row, widths).rstrip()
        if len(block) + len(new_item) > 2000:
            list_of_blocks.append(block.rstrip())
            block = ""
        if len(new_item.rstrip()) > 2000:
            lines = textwrap.wrap(new_item.rstrip(), 2000, break_long_words=False)
            list_of_blocks.extend(lines)
            new_item = ""
        block += "\n" + new_item.rstrip()
        # print(block)
    list_of_blocks.append(block.rstrip())
    # print(list_of_blocks)
    return list_of_blocks

def generate_widths(list_of_rows):
    widths = [max(map(len, col)) for col in zip(*list_of_rows)]
    return widths

def multi_column(list_of_list_of_rows, left_just):
    list_of_widths = []
    for list_of_rows in list_of_list_of_rows:
        list_of_widths.append(generate_widths(list_of_rows))

    final_widths = [max(widths) for widths in zip(*list_of_widths)]
    output = []
    for list_of_rows in list_of_list_of_rows:
        output.append(format_list_to_widths(list_of_rows, final_widths, left_just))
    return output

def multi_block(list_of_rows, left_just):
    test_list = []
    final_list = []

    for row in list_of_rows:

        old_list = copy.deepcopy(test_list)
        test_list.append(row)
        text = pretty_column(test_list, left_just)
        if (len(text)) > 500:
            final_list.append(old_list)
            test_list = [row]
    final_list.append(test_list)
    return multi_column(final_list, left_just)

def format_timedelta(timedelta):
    seconds = timedelta.total_seconds()
    print(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if seconds < 1: seconds = 0

    locals_ = locals()
    magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude)
                      for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])
    magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude if int(locals_[magnitude]) > 1 else magnitude[:-1])
                      for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])
    eta_str = ", ".join(magnitudes_str)
    return eta_str

# round to seconds
# duration = duration + timedelta(microseconds=499999)
# duration = duration // 1000000 * 1000000

def round_timedelta(delta) -> timedelta:
    delta = delta + timedelta(microseconds=499999)
    delta = delta // 1000000 * 1000000
    return delta

def pretty_column(list_of_rows, left_just):
    """
    :type list_of_rows: list
    :type left_just: bool
    """
    widths = generate_widths(list_of_rows)
    output = format_list_to_widths(list_of_rows, widths, left_just)
    # print(output)

    text = re.sub(r'\s+$', '', output, 0, re.M)
    text = text.strip()
    return text

def format_list_to_widths(list_of_rows, widths, left_just):
    output = ""
    if left_just:
        for row in list_of_rows:
            output += ("  ".join((val.ljust(width) for val, width in zip(row, widths)))).rstrip() + "\n"
    else:
        for row in list_of_rows:
            output += ("  ".join((val.rjust(width) for val, width in zip(row, widths)))).rstrip() + "\n"
    return output

def format_row_to_widths(row, widths):
    return "  ".join((val.ljust(width) for val, width in zip(row, widths)))

# def shorten_link(link) -> str:
#     return Shortener('Tinyurl').short(link)

# print(regex_test("Kappa", "Κappa"))

def reverse_dict(input_dict) -> dict:
    return dict((v, k) for k, v in input_dict.items())
async def parse_time_to_end(time_string):
    print(time_string)
    try:
        end = await parse_date("in " + time_string)
        delt = end - datetime.now()
        delt = round_timedelta(delt)
        readable = format_timedelta(delt)
        return {"end": end, "duration": delt, "readable": readable}
    except:
        print(traceback.format_exc())
        return None

def round_time(dt=None, round_to=60):
    import datetime
    if dt == None: dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds + round_to / 2) // round_to * round_to
    return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)

def parse_date(date_text):
    res = dateparser.parse(date_text)
    return res

def get_ordinal(number):
    ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n // 10) % 10 != 1) * (n % 10 < 4) * n % 10::4])
    return ordinal(number)
async def get_redirected_url(url):
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    request = opener.open(url)
    return request.url

def strip_markdown(markdowned_str):
    from bs4 import BeautifulSoup
    from markdown import markdown

    html = markdown(markdowned_str)
    return ''.join(BeautifulSoup(html).findAll(text=True))

def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]

def remove_none(obj):
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)((remove_none(k), remove_none(v))
                         for k, v in obj.items() if k is not None and v is not None)
    else:
        return obj

def hastebin(text):
    print(text)
    url = r"https://hastebin.com/documents/"
    blocks = textwrap.wrap(text, 400000, break_long_words=False, replace_whitespace=False, drop_whitespace=False)
    results = [requests.post(url, text) for text in blocks]
    print(results)
    return ["https://hastebin.com/" + json.loads(response.text)["key"] for response in results]

def dict2rows(in_dict):
    return [(k, str(v)) for k, v in in_dict.items()]

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old
