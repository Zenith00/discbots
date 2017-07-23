from collections import defaultdict

nested_dict = lambda: defaultdict(nested_dict)

config = nested_dict()


config["prefix"]["command"] = "%%"
config["prefix"]["tag"] = ",,"

config["query"]["user"]["embed"]["output"] = "inplace"
config["query"]["user"]["embed"]["color_average_bar"] = True  # Fancy average color bar, disable to increase performance
config["query"]["user"]["dump"]["output"] = "inplace"
config["query"]["roles"]["list"]["output"] = "relay"
config["query"]["roles"]["members"]["delimiter"] = "\n"  # Ex: , . | \n
config["query"]["roles"]["members"]["output"] = "relay"
config["query"]["emoji"]["output"] = "inplace"
config["query"]["user"]["dump"] = "relay"

config["find"]["current"]["output"] = "inplace"
config["find"]["history"]["output"] = "inplace"
config["find"]["bans"]["output"] = "inplace"

config["logs"]["output"] = "relay"

config["autoupdate"] = False
config["perspective"] = True
config["imgur"] = True
config["remote_mongo"] = True

