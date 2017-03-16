import random
def rand1000():
    global called
    rand1000.called = True
    global num2
    num2 = random.randrange(0, 1000)
    print("rand1000 ", num2)
    print("-----")
rand1000()
if rand1000.called:
    global maxguess
    maxguess = 7
    print(maxguess)