import matplotlib.pyplot as plt
import numpy as np

#
# num_lines =

# f = open('text.txt')
# for word in f.read().split():
#     print(word)

all_values = []
num_bands = -1;
with open('band1001.out', 'r') as file:
    for line in file:
        energy_arr = line.split()[5::2]
        # print energy_arr
        if num_bands == -1:
            num_bands = len(energy_arr)
            all_values = [[] for _ in range(num_bands)]
            # print all_values
        for index, energy in enumerate(energy_arr):
            all_values[index].append(energy)
print(all_values)
for band in all_values:
    plt.plot(band)
plt.axis([1, len(all_values[0]), -2, 5])
plt.show()
