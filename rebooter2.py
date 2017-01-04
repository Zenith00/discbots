import ast
import time
import subprocess


while True:
    print("REBOOTING")
    p = subprocess.call(["python.exe",r"C:\Users\Austin\Desktop\Programming\Disc\selfbot_secondary.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(5)