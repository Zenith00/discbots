import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

srs = pd.read_pickle("palu.pckl")
srs = pd.to_datetime(srs)
print(list(srs))
plt.rcParams["figure.figsize"] = [15,9]

v = pd.date_range(srs.min(), srs.max(), 50)
v = list(v)
print(v)
q = (srs.max() -srs.min()).total_seconds() // 60 // 60 // 24

f = plt.hist(srs, bins=int(q))


plt.show()

