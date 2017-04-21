import re
import regex
import utils.utils_text

r = utils.utils_text.regex_test("([[:punct:]]|\s)kappa(\s|[[:punct:]])", "kappa")

print(r)