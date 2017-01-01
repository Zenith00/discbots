import re
import copy

def regex_test(reg_str, string):
    reg = re.compile(reg_str)
    match = reg.search(string)
    return match

def multi_regex(reg_list, string):
    for reg in reg_list:
        if regex_test(reg, string):
            return True
    return False

async def generate_widths(list_of_rows):

    widths = [max(map(len, col)) for col in zip(*list_of_rows)]
    return widths


async def multi_column(list_of_list_of_rows, left_just):
    list_of_widths = []
    for list_of_rows in list_of_list_of_rows:
        list_of_widths.append(await generate_widths(list_of_rows))

    final_widths = [max(widths) for widths in zip(*list_of_widths)]
    output = []
    for list_of_rows in list_of_list_of_rows:
        output.append(await format_list_to_widths(list_of_rows, final_widths, left_just))
    return output

async def multi_block(list_of_rows, left_just):
    test_list = []
    final_list = []
    for row in list_of_rows:
        old_list = copy.deepcopy(test_list)
        test_list.append(row)
        text = await pretty_column(test_list, left_just)
        if (len(text)) > 1000:
            final_list.append(old_list)
            test_list = []

    final_list.append(test_list)
    return await multi_column(final_list, left_just)

async def pretty_column(list_of_rows, left_just):
    """
    :type list_of_rows: list
    :type left_just: bool
    """
    widths = await generate_widths(list_of_rows)
    output = await format_list_to_widths(list_of_rows, widths, left_just)
    # print(output)

    text = re.sub(r'\s+$', '', output, 0, re.M)
    text = text.strip()
    return text


async def format_list_to_widths(list_of_rows, widths, left_just):
    output = ""
    if left_just:
        for row in list_of_rows:
            output += ("  ".join((val.ljust(width) for val, width in zip(row, widths)))) + "\n"
    else:
        for row in list_of_rows:
            output += ("  ".join((val.rjust(width) for val, width in zip(row, widths)))) + "\n"
    return output