import os
homeDir = "C:\\Users\\Austin\\Desktop\\Programming\\"

PATH = {
			"home":homeDir,
			"logs":homeDir + "Logs\\",
			"art":"C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\",
			"comms":homeDir + "Comms\\"
}

with open("paths.txt", "w") as f:
	f.write(str(PATH))
	