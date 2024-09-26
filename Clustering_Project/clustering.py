import numpy as np
import matplotlib.pyplot as plt
import random

# ==========================================================


class Point:
    def __init__(self, coordinates):
        self.coordinates = coordinates

    coordinates = np.array([0, 0, 0])
    cluster_index = 0


# ===========================================================


class Cluster:
    def __init__(self, points_list, representative_v):
        self.points_list = points_list
        self.representative_v = representative_v

    def remove_point(self, point):
        self.points_list.remove(point)

    def add_point(self, point):
        self.points_list.append(point)

    def update_representative_v(self):
        if len(self.points_list) == 0:
            return
        else:
            sum_p = np.array([0.0, 0.0, 0.0])
            for point in self.points_list:
                sum_p += point.coordinates
            self.representative_v = sum_p / len(self.points_list)
            return

    def calculate_ObjFun(self):
        if len(self.points_list) == 0:
            return 0
        sum_p = 0
        for point in self.points_list:
            sum_p += np.linalg.norm(point.coordinates - self.representative_v) ** 2
        return sum_p / len(self.points_list)

    points_list = []
    representative_v = np.array([0, 0, 0])


# ===========================================================
def standardztn(points):
    sum_p = np.array([0.0, 0.0, 0.0])
    for point in points:
        sum_p += point.coordinates
    norm_avg = sum_p / len(points)

    norm_max = 0
    for point in points:
        point.coordinates -= norm_avg
        norm_p = np.linalg.norm(point.coordinates)
        if norm_p > norm_max:
            norm_max = norm_p

    for point in points:
        point.coordinates /= norm_max

    return points, norm_avg, norm_max


# ===========================================================
def calculate_ObjFun(clusters):
    clust_obj = 0
    for cluster in clusters:
        cluster.update_representative_v()
        clust_obj += cluster.calculate_ObjFun()
    return clust_obj


# ===========================================================


def plot_points(points, plt, ax):
    xdata = []
    ydata = []
    zdata = []
    for point in points:
        xdata.append(point.coordinates[0])
        ydata.append(point.coordinates[1])
        zdata.append(point.coordinates[2])
    ax.scatter3D(xdata, ydata, zdata)
    return


# ===========================================================


def gerenate_random_vectors(x_max, y_max, z_max, radius, min_groups, max_groups):
    groups_num = random.randint(min_groups, max_groups)
    points = []

    for i in range(0, groups_num):
        point_c = np.array(
            [
                random.uniform(0, x_max),
                random.uniform(0, y_max),
                random.uniform(0, z_max),
            ]
        )
        point_num = random.randint(20, 80)

        for j in range(0, point_num):
            point = Point(
                point_c
                + np.array(
                    [
                        random.uniform(-radius, radius),
                        random.uniform(-radius, radius),
                        random.uniform(-radius, radius),
                    ]
                )
            )
            points.append(point)

    print(
        "Random Vector Function Complete. {} numbers of points was created in {} groups.".format(
            len(points), groups_num
        )
    )
    return points


# ===========================================================


def find_closest_cluster(point, clusters):
    cluster_index = 0
    dist_min = 10**6

    for cluster in clusters:
        dist_to_cluster = np.linalg.norm(point.coordinates - cluster.representative_v)
        if dist_to_cluster < dist_min:
            cluster_index = clusters.index(cluster)
            dist_min = dist_to_cluster

    if cluster_index == point.cluster_index:
        return clusters
    else:
        clusters[point.cluster_index].remove_point(point)
        point.cluster_index = cluster_index
        clusters[cluster_index].add_point(point)
        return clusters


# ===========================================================


def vector_partitioning(points, clusters):

    for point in points:
        clusters = find_closest_cluster(point, clusters)

    return points, clusters


# ===========================================================


def forgy_method_init(points, k):
    random_index = random.sample(range(0, len(points)), k)
    random_index.sort()
    clusters = [Cluster([], points[random_index[i]].coordinates) for i in range(0, k)]
    clusters[0].points_list = points.copy()
    return clusters


# ===========================================================
def random_part_init(points, k):
    clusters = [Cluster([], np.array([0, 0, 0])) for i in range(0, k)]
    for point in points:
        cluster_index = random.randint(0, k - 1)
        clusters[cluster_index].add_point(point)
        point.cluster_index = cluster_index

    for cluster in clusters:
        cluster.update_representative_v()

    return clusters


# ===========================================================
def k_pp_init(points, k):
    rep_vs = []
    random_index = random.sample(range(0, len(points)), 1)
    rep_vs.append(points[random_index[0]].coordinates)

    for i in range(1, k):
        random_index = random.sample(range(0, len(points)), 30)
        dist_max = 0
        for index in random_index:
            dist = 0
            for rep_v in rep_vs:
                dist += np.linalg.norm(rep_v - points[index].coordinates)
            if dist > dist_max:
                max_index = index
                dist_max = dist
        rep_vs.append(points[max_index].coordinates)

    clusters = [Cluster([], rep_vs[i]) for i in range(0, k)]
    clusters[0].points_list = points.copy()

    return clusters


# ===========================================================
def corelation_init(points, k):
    rep_vs = []
    random_index = random.sample(range(0, len(points)), 1)
    rep_vs.append(points[random_index[0]].coordinates)

    for i in range(1, k):
        random_index = random.sample(range(0, len(points)), 100)
        corel_max = 0
        for index in random_index:
            corel = 0
            point_dm = points[index].coordinates - np.average(points[index].coordinates)
            point_dm_norm = np.linalg.norm(point_dm)
            for rep_v in rep_vs:
                rep_v_dm = rep_v - np.average(rep_v)
                rep_v_dm_norm = np.linalg.norm(rep_v_dm)
                corel += abs(
                    np.dot(point_dm, rep_v_dm) / (point_dm_norm * rep_v_dm_norm)
                )
            if corel > corel_max:
                max_index = index
                corel_max = corel
        rep_vs.append(points[max_index].coordinates)

    clusters = [Cluster([], rep_vs[i]) for i in range(0, k)]
    clusters[0].points_list = points.copy()

    return clusters


# ===========================================================


def clustering(points, k, selection):
    if selection == 1:
        clusters = forgy_method_init(points, k)
    elif selection == 2:
        clusters = random_part_init(points, k)
    elif selection == 3:
        clusters = k_pp_init(points, k)
    elif selection == 4:
        clusters = corelation_init(points, k)

    clust_obj_temp = calculate_ObjFun(clusters)
    clust_obj = 0

    count = 0
    while abs(clust_obj - clust_obj_temp) > 0.0001 and count < 1000:
        clust_obj_temp = clust_obj
        count += 1
        points, clusters = vector_partitioning(points, clusters)

        for cluster in clusters:
            cluster.update_representative_v()

        clust_obj = calculate_ObjFun(clusters)

    return clusters


# ===========================================================
def clustering_k(points, k_init, k_max, max_tries):

    points, norm_avg, norm_max = standardztn(points)

    ks = []
    clust_obj_values = []
    set_of_clusters = []
    init_type = []
    clust_obj = 10**6
    selections = [1, 2, 3, 4]

    for selection in selections:
        for itir in range(0, max_tries):
            k = k_init
            count = 0
            while count < k_max + k_init:
                for point in points:
                    point.cluster_index = 0
                clusters = clustering(points, k, selection)
                clust_obj_temp = clust_obj
                clust_obj = calculate_ObjFun(clusters)
                set_of_clusters.append(clusters)
                ks.append(k)
                clust_obj_values.append(clust_obj)
                init_type.append(selection)
                k += 1
                count += 1

    index_min = clust_obj_values.index(min(clust_obj_values))

    k_opt = ks[index_min]
    cluster_opt = set_of_clusters[index_min]
    selection_opt = init_type[index_min]

    for cluster in cluster_opt:
        for point in cluster.points_list:
            point.coordinates = norm_max * point.coordinates + norm_avg

    return cluster_opt, k_opt, selection_opt


# ===========================================================


x_max = 15
y_max = 15
z_max = 15
radius = 2.5
min_groups = 6
max_groups = 12
k = 2

k_init = 5
k_max = 10
max_tries = 3

set_of_points = []
set_of_clusters = []
ks = []
inits = []


points = gerenate_random_vectors(x_max, y_max, z_max, radius, min_groups, max_groups)

clusters, k, init = clustering_k(points, k_init, k_max, max_tries)

set_of_points.append(points)
set_of_clusters.append(clusters)
ks.append(k)
inits.append(init)


fig = plt.figure()

ax = plt.axes(projection="3d")
for cluster in clusters:
    plot_points(cluster.points_list, plt, ax)

ax.set_aspect("equal", adjustable="box")

plt.show()
