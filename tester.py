import re
import regex
import constants

import utils.utils_text

content = "https://discord.gg/fRZ8s"
match = re.search(constants.INVITE_REGEX, content)

print(match)