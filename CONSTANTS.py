PINBOT = {"COMMAND_HELP":
              [["Command", "Params", "Description", "Note"],
               ["help", "", "", "My brother! He's dying! Get help!"],
               ["setmax", "[#|max pins]", "Sets the max # of pins before embedding", "Short for ,,config set PIN_THRESHOLD [#]"],
               ["map", "[#from-channel] [#to-channel]", "Saves pins from [from-channel] to [to-channel]", "many-to-one"],
               ["unmap", "[#from-channel]", "Stops saving pins from [from-channel]", ""],
               ["whitelist", "[@|role/member]", "Allows/Disallows role/member to use commands", "Try a mention?"],
               ["setprefix", "[prefix]", "Sets prefix to be [prefix]", ""],
               ["", "", "", ""],
               ["config set", "[name] [value]", "Sets config [name] to be literal_eval([value])", "With great power..."],
               ["config unset", "[name]", "Restores config [name] to default", "...comes great responsibility"],
               ["config reset", "", "Restores config to default", "In case of emergency, break glass"],
               ["config print", "", "Prints current config", "Secret settings pending documentation..."],
               ["", "", "", ""],
               ["pinall", "", "Processes pins in channel until reaching threshold", ""],

               ]}
