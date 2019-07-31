PINBOT = {"COMMAND_HELP":
              [["Command", "Params", "Description", "Note"],
               ["help", "", "", "My brother! He's dying! Get help!"],
               ["setup", "", "", "Help with setting up & Common problems"],

               ["setmax", "[#|max pins]", "Sets the max # of pins before embedding", "Short for ,,config set PIN_THRESHOLD [#]"],
               ["map", "[#from-channel] [#to-channel]", "Saves pins from [#from] to [#to]", "many-to-one"],
               ["unmap", "[#from-channel]", "Stops saving pins from [from-channel]", ""],
               ["whitelist", "[@|role/member]", "Allow/Forbid role/member using commands", "Try a mention?"],
               ["setprefix", "[prefix]", "Sets prefix to [prefix]", ""],
               ["", "", "", ""],
               ["config set", "[name] [value]", "Sets config [name] to be literal_eval([value])", "With great power..."],
               ["config unset", "[name]", "Restores config [name] to default", "...comes great responsibility"],
               ["config reset", "", "Restores all config to default", "In case of emergency, break glass"],
               ["config print", "", "Prints current config", "Secret settings pending documentation..."],
               ["", "", "", ""],
               ["pinall", "", "Processes pins in channel until reaching threshold", ""],

               ]}
