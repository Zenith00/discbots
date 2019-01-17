PINBOT = {}
PINBOT["TOKEN"] = ""
PINBOT["ACK_TYPE"] = "react"
PINBOT["PREFIX"] = ",,"
PINBOT["ROLE_BY_CONFIG"] = False
PINBOT["CHANNEL_TO_ID"] = {
    "spoilers"                                                                                : 525155168224804870,
    "wake the fuck up biiiiiiitch"                                                            : 535289118389960704,
    "official-winx-fanclub-channel"                                                           : 527959148105695233,
    "art"                                                                                     : 504361029631737867,
    "pins-testing"                                                                            : 535542019393716225,
    "announcements"                                                                           : 504490198663692309,
    "mario-party-winners"                                                                     : 531969354200252416,
    "vc-text-channel-for-poor-people-without-mic"                                             : 529052318230904873,
    "smash-night"                                                                             : 530419819112038410,
    "minecraft-thnask"                                                                        : 526522335751176192,
    "rules"                                                                                   : 504490253118078977,
    "actual-spoilers"                                                                         : 527284112822763530,
    "ginger"                                                                                  : 504361491982712842,
    "spiderman"                                                                               : 534806059101978642,
    "i-hate-you-netflicx"                                                                     : 531628925730947082,
    "official winx fanclub viewing channel"                                                   : 527959214933540865,
    "bots"                                                                                    : 528720754179702828,
    "gayming-general"                                                                         : 504361051710554142,
    "music"                                                                                   : 528720913907187742,
    "music"                                                                                   : 504361014616129546,
    "palutenas-temple-rp-channel"                                                             : 535533610992926721,
    "discord e sleepover uwuuuu"                                                              : 535449777085874219,
    "avril lavigne karaoke only"                                                              : 504787570350358551,
    "bot-cmds"                                                                                : 528720843002347523,
    "waiting-for-new-animal-crossing-support-group"                                           : 527856905771679744,
    "discussion"                                                                              : 504360688529965056,
    "hewwo"                                                                                   : 504360794025230358,
    "dangerous-at-work-its-lewd-sometimes"                                                    : 525787112453439498,
    "moderator tingz"                                                                         : 530430570191257600,
    "overwatch-hheheh"                                                                        : 526542655405162496,
    "quotes"                                                                                  : 530494499835740161,
    "cock-is-one-of-my-favourite-tastes-not-only-that-but-the-balls-smell-amazing-it-makes-me": 530430658766700549,
    "welcome"                                                                                 : 504360893769842700,
    "wtf"                                                                                     : 530430819869917205,
    "actual-rules-pls-read-haha-yes"                                                          : 530421642745348108,
    "irl"                                                                                     : 504361193138552853,
    "winx club"                                                                               : 527959960483659796,
    "content"                                                                                 : 504361112192417813,
    "gaming and media stuff"                                                                  : 530419673024692224,
}
PINBOT["PINMAP"] = {
    "hewwo": "pins-testing",
    "pins-testing":"pins-testing"
}
PINBOT["DEFAULT_OUT"] = "inplace"
PINBOT["PINMAP"] = {PINBOT["CHANNEL_TO_ID"][k]: PINBOT["CHANNEL_TO_ID"][v] for k, v in PINBOT["PINMAP"].items()}
PINBOT["PIN_THRESHOLD"] = 35
PINBOT["EMBED_COLOR_CALC"] = True
