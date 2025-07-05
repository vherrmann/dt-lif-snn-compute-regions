import matplotlib.pyplot as plt
import numpy as np
import glob

X = np.arange(32)

plt.rcParams.update({"font.size": 14})

for file_path in glob.glob("output4096.csv"):
    data = np.loadtxt(file_path, delimiter=",")
    # plt.plot(X, data[:32], label="#Counted Regions")

for i in range(4, 7):
    plt.plot(X, data / X**i, label=f"Regions / T^{i}")

# plt.plot(X, (((X**2 + X + 2) / 2) ** 2), label=f"(T² + T + 2)² / 2²")

plt.title("")
# plt.yscale("log")
plt.xlabel("T")
plt.ylabel("#Regions")
plt.legend(loc="upper left")
# plt.ylim(0, 3)
plt.grid(True)
plt.show()
