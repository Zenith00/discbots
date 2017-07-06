from imgurpython import ImgurClient


from simplegist.simplegist import Simplegist
from utils import utils_text, utils_file

from utils.duration_timer import timer
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"


imgur = ImgurClient("5e1b2fcfcf0f36e",
                    "d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)

for image in imgur.get_album_images("KWuZF"):
    print(image.link)