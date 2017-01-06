import re

CHANNELNAME_CHANNELID_DICT = {
    "overwatch-discussion"   : "109672661671505920",
    "modchat"                : "106091034852794368",
    "server-log"             : "152757147288076297",
    "voice-channel-output"   : "200185170249252865",
    "moderation-notes"       : "188949683589218304",
    "pc-lfg"                 : "182420486582435840",
    "esports-discussion"     : "233904315247362048",
    "content-creation"       : "95324409270636544",
    "support"                : "241964387609477120",
    "competitive-recruitment": "170983565146849280",
    "tournament-announcement": "184770081333444608",
    "trustedchat"            : "170185225526181890",
    "general-discussion"     : "94882524378968064",
    "lf-scrim"               : "177136656846028801",
    "console-lfg"            : "185665683009306625",
    "fanart"                 : "168567769573490688",
    "competitive-discussion" : "107255001163788288",
    "lore-discussion"        : "180471683759472640",
    "announcements"          : "95632031966310400",
    "spam-channel"           : "209609220084072450",
    "jukebox"                : "176236425384034304",
    "rules-and-info"         : "174457179850539009",
    "warning-log"            : "170179130694828032",
    "bot-log"                : "147153976687591424",
    "nadir_audit_log"        : "240320691868663809",
    "alerts"                 : "252976184344838144",
}

CHANNELID_CHANNELNAME_DICT = dict([v, k] for k, v in CHANNELNAME_CHANNELID_DICT.items())

ROLENAME_ID_DICT = {
    "REDDIT_MODERATOR_ROLE"    : "94887153133162496",
    "BLIZZARD_ROLE"            : "106536617967116288",
    "MUTED_ROLE"               : "110595961490792448",
    "MVP_ROLE"                 : "117291830810247170",
    "OMNIC_ROLE"               : "138132942542077952",
    "TRUSTED_ROLE"             : "169728613216813056",
    "ADMINISTRATOR_ROLE"       : "172949857164722176",
    "MODERATOR_ROLE"           : "172950000412655616",
    "DISCORD_STAFF_ROLE"       : "185217304533925888",
    "PSEUDO_ADMINISTRATOR_ROLE": "188858581276164096",
    "FOUNDER_ROLE"             : "197364237952221184",
    "REDDIT_OVERWATCH_ROLE"    : "204083728182411264",
    "VETERAN_ROLE"             : "216302320189833226",
    "OVERWATCH_AGENT_ROLE"     : "227935626954014720",
    "ESPORTS_SUB_ROLE"         : "230937138852659201",
    "BLIZZARD_SUB_ROLE"        : "231198164210810880",
    "DISCORD_SUB_ROLE"         : "231199148647383040",
    "DJ_ROLE"                  : "231852994780594176",
}



OVERWATCH_SERVER_ID = "94882524378968064"



MERCY_ID = "236341193842098177"
ZENITH_ID = "129706966460137472"
NADIR_AUDIT_LOG_ID = "240320691868663809"

VOICE_LINES = (
    "Did someone call a doctor?",
    "Right beside you.",
    "I've got you.",
    "Where does it hurt?",
    "Patching you up.",
    "Let's get you back out there.",
    "Heilstrahl aktiviert.",
    "Healing stream engaged.",
    "I'm taking care of you.",
    "Ich kümmere mich um dich.",
    "Mercy im Bereitschaftsdienst.",
    "You're coming with me.",
    "Powered up.",
    "Schaden verstärkt.",
    "Ich bin da.",
    "I'm here.",
    "Right beside you.",
    "Support has arrived.",
    "Mercy on call.",
    "I'll be watching over you.",
    "A speedy recovery.",
    "Back to square one.",
    "Now, where am I needed?",
    "Back in the fight.",
    "Valkyrie online.",
    "Die Wunder der modernen Medizin.",
    "The wonders of modern medicine!",
    "A clean bill of health.",
    "Good as new.",
    "Immer unterbricht mich jemand bei der Arbeit.")
LFG_REGEX = re.compile(
    (r"(lf(G|\d))|(\d\d\d\d)|(plat|gold|silver|diamond)|(^LF(((NA)|(EU))|(\s?\d)))|((NA|EU) (LF(g|\d)*))|"
     "(http(s?)://discord.gg/)|(xbox)|(ps4)"), re.IGNORECASE)
LINK_REGEX = re.compile(r"(http(s?)://discord.gg/(\w+))", re.IGNORECASE)

HOTS_REGEX = re.compile(r"(heroes of the storm)|(storm)|(heros)|(hots)|(heroes)|(genji)|(oni)",
                        re.IGNORECASE)