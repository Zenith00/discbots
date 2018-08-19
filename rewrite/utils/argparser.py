class Parser():
    def tokenize(self, input_string):
        tokens = []
        token = ""
        escaping = 0
        for a, b in zip(" " + input_string[:-1], input_string):
            print("|" + a+b)
            if a == "\\":
                print("adding escaped token " + b)
                token += b
                print(token)
                continue
            if b == " ":
                tokens.append(token)
                token = ""
                continue
            token += b
        tokens.append(token)
        print(tokens)


parse = Parser()
parse.tokenize(r"abcdef ad ldjawdj ijdlawjdalw \a c \\b")