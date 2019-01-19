PINBOT = {"COMMAND_HELP":
                [["Command", "Params", "Description", "Note"],
                 ["set", "[name] [value]", "Sets config [name] to be [value]", "Dangerous if used on PINMAP, ALLOWED_IDS"],                           ["unset", "[name]", "Restores config [name] to default", "In case of emergency, break glass"],
                 ["whitelist", "[role/member]", "Toggles whitelist of role/member to use commands", "Try a mention"],
                 ["print", "", "Prints current config", ""],
                 ["map", "[from-channel] [to-channel]", "Saves pins from [from-channel] to [to-channel]", "many-to-one"],
                 ["unmap", "[from-channel]", "Stops saving pins from [from-channel]", ""],
                 ]}
