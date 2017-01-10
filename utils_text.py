import re
import copy

from pyshorteners import Shortener


def regex_test(reg_str, string):
    reg = re.compile(reg_str, re.IGNORECASE)
    match = reg.search(string)
    return match

def parse_bool(string) -> bool:
    """

    :type string: str
    """
    if any(substring in string for substring in ["yes", "y", "true"]):
        return True
    return False


def multi_regex(reg_list, string):
    for reg in reg_list:
        if regex_test(reg, string):
            return True
    return False

def generate_widths(list_of_rows):

    widths = [max(map(len, col)) for col in zip(*list_of_rows)]
    return widths


def multi_column(list_of_list_of_rows, left_just):
    list_of_widths = []
    for list_of_rows in list_of_list_of_rows:
        list_of_widths.append( generate_widths(list_of_rows))

    final_widths = [max(widths) for widths in zip(*list_of_widths)]
    output = []
    for list_of_rows in list_of_list_of_rows:
        output.append( format_list_to_widths(list_of_rows, final_widths, left_just))
    return output

def multi_block(list_of_rows, left_just):
    test_list = []
    final_list = []
    for row in list_of_rows:
        old_list = copy.deepcopy(test_list)
        test_list.append(row)
        text =  pretty_column(test_list, left_just)
        if (len(text)) > 1000:
            final_list.append(old_list)
            test_list = []

    final_list.append(test_list)
    return  multi_column(final_list, left_just)

def pretty_column(list_of_rows, left_just):
    """
    :type list_of_rows: list
    :type left_just: bool
    """
    widths =  generate_widths(list_of_rows)
    output =  format_list_to_widths(list_of_rows, widths, left_just)
    # print(output)

    text = re.sub(r'\s+$', '', output, 0, re.M)
    text = text.strip()
    return text



def format_list_to_widths(list_of_rows, widths, left_just):
    output = ""
    if left_just:
        for row in list_of_rows:
            output += ("  ".join((val.ljust(width) for val, width in zip(row, widths)))) + "\n"
    else:
        for row in list_of_rows:
            output += ("  ".join((val.rjust(width) for val, width in zip(row, widths)))) + "\n"
    return output


def shorten_link(link) -> str:
    return Shortener('Tinyurl').short(link)