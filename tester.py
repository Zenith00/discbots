with open(r"C:\Users\Austin\Downloads\death.txt", "r") as f:
    text = f.read()
    for c in text:
        print(c.encode("unicode_escape"))