from pytba import api as tba

import pyfav.pyfav as pyfav

tba.set_api_key("Austin Zhang", "1072bot ", "1.0")

team = tba.team_get("254")
# print(pyfav.get_favicon_url(r'https://webappsca.pcrsoft.com/Clue/SC-Assignments-End-Date-(No-Range)/18593'))
print(team)
