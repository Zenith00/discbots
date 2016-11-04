
import urllib
import imgurpython
from imgurpython import ImgurClient
import os
# import win32file
# import win32con
import time, shutil, fileinput
from concurrent.futures import ProcessPoolExecutor
import sys
#FANARTBOT
path = 	"C:\\Users\\Austin\\Dropbox\\Zenith's Fanart\\"
refreshToken = "5c52c0f6a47da6fb599e2835bf228c59c68dd902"
accessToken = "4c80c2924ddeb63d3f1c99d19ae04e01e438b5fb"


		
		
while True:
	print("uploader init")
	#grab first line
	with open(path + "toUpload.txt", "r+") as f:
		f.seek(0)
		fileToUpload = str(f.readline())
		
	if fileToUpload == "":
		time.sleep(5)
		continue
		
	print("File to upload found:")
	print(fileToUpload)
	print()
	#start imgur uploader
	print("IMGUR INIT")
	imgur = ImgurClient("5e1b2fcfcf0f36e","d919f14c31fa97819b1e9c82e2be40aef8bd9682", accessToken, refreshToken)
	print("UPLOADER INSTANCE ONLINE")
	
	#remove first line
	for line_number, line in enumerate(fileinput.input(path + "toUpload.txt", inplace=1)):
		if line_number == 0:
			time.sleep(0)
		else:
			sys.stdout.write(line)
	
	print("UPLOADING FILE")
	#upload file
	fileToUpload = fileToUpload.strip("\n")
	image = imgur.upload_from_path(fileToUpload, config=None, anon=False)
	print(image['link'])
	
	print("WRITING LINK")
	#write link to botdata.txt
	f = open(path + "botdata.txt", "a")
	f.write(image['link'] + "\n")
	f.close()