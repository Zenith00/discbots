from datetime import datetime, timedelta
import time

saved_time = datetime.now()
time.sleep(5)
print((datetime.now() - saved_time).total_seconds())


#  import sys
# numbers = input().split(" ")
# print(numbers[-1].join(numbers[:-1]) + " = " + str(int(numbers[0]) + sum([int(x) for x in numbers[1:-1]]) if numbers[-1] == "+" else int(numbers[0]) - sum([int(x) for x in numbers[1:-1]])))
