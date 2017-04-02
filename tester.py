import re
text = "<@!236341193842098177> <@277692222302846977> <@129706966460137472>"
userid_matches = re.search("(<@!?\d+>)", text)
def escape_user(match):
    mention = match.group(0)
    userid = re.search("\d+", mention)
    userid = userid.group(0)
    return "\\" + mention

    pass
print(re.sub("(<@!?\d+>)", escape_user, text))