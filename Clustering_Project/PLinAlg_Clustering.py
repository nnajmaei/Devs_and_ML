import numpy as np
import matplotlib.pyplot as plt

v1 = np.array([2, 5, 1])
v2 = np.array([0, 2, 2])
v3 = np.array([3, 4, 5])
xlim = [-1, 1]
k = 3


data = np.zeros((198, 3))
segm_size = int(np.floor(data.shape[0] / k))

for i in range(k):
    p_c = np.array(
        [np.random.uniform(0, 10), np.random.uniform(0, 10), np.random.uniform(0, 10)]
    )
    for j in range(i * segm_size, (i + 1) * segm_size):
        data[j, :] = p_c + np.array(
            [
                np.random.uniform(-1, 1),
                np.random.uniform(-1, 1),
                np.random.uniform(-1, 1),
            ]
        )


"""
scalars = np.random.uniform(low=xlim[0],high=xlim[1],size=data.shape)

for i in range(len(scalars)):
    data[i,:]=scalars[i,0]*v1+scalars[i,1]*v2+scalars[i,2]*v3
"""

fig = plt.figure()
ax = plt.axes(projection="3d")

ax.scatter3D(data[:, 0], data[:, 1], data[:, 2])
plt.show()


print(f"The shape of data set is {data.shape}\n")

# randomizing the centroids
ridx = np.random.choice(range(len(data)), (k), replace=False)
print(f"The shape of ridx set is {ridx.shape}\n")

centroids = data[ridx, :]
centroids_temp = np.zeros(centroids.shape)

print(np.sum(abs(centroids - centroids_temp)) < 0.000001)

print(f"The shape of centroids set is {centroids.shape}")
print(f"The random centroids are:\n{centroids}\n")

while np.sum(abs(centroids - centroids_temp)) > 0.000001:
    # calculating distance to centroids
    centroids_temp = centroids.copy()
    dists = np.zeros((data.shape[0], k))

    # use of broadcasting to calculate distance to the centoirds
    for ci in range(k):
        dists[:, ci] = np.sum((data - centroids[ci, :]) ** 2, axis=1)

    # finding the closests centroid
    groupidx = np.argmin(dists, axis=1)

    for ki in range(k):
        centroids[ki, :] = [
            np.mean(data[groupidx == ki, 0]),
            np.mean(data[groupidx == ki, 1]),
            np.mean(data[groupidx == ki, 2]),
        ]

print(f"The shape of dists set is {dists.shape}")
print(f"The shape of groupidx set is {groupidx.shape}")
print(f"{groupidx}\n")
print(f"The finalized centroids are:\n{centroids}\n")

fig = plt.figure()
ax = plt.axes(projection="3d")

ax.scatter3D(centroids[:, 0], centroids[:, 1], centroids[:, 2], marker="^")
for ki in range(k):
    ax.scatter3D(
        data[groupidx == ki, 0],
        data[groupidx == ki, 1],
        data[groupidx == ki, 2],
        marker="o",
    )
plt.show()
