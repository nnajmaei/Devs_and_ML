import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import random


# ===========================================================
class Path:
    def __init__(self, initial_section, obstacles, status, direction):
        self.coordinates = initial_section
        self.obstacles = obstacles
        self.status = False
        self.direction = bool(direction)

    def add_obstacle(self, obstacle):
        self.obstacles.append(obstacle)

    def calculate_distance(self):
        distance = 0
        for i in range(0, len(self.coordinates) - 1):
            distance += np.linalg.norm(self.coordinates[i + 1] - self.coordinates[i])
        return distance

    coordinates = np.array([])
    status = False
    obstacles = []
    direction = bool(0)


# ===========================================================
class Obstacle:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    center = np.array([])
    radius = 0


# ===========================================================
def plot_osbtacles(obstacles, axes):
    for obstacle in obstacles:
        circle = Circle(
            obstacle.center, obstacle.radius, edgecolor="red", facecolor="none"
        )
        axes.add_patch(circle)
        # axes.plot(obstacle.center[0],obstacle.center[1],marker="o",color="red")

    axes.set_aspect("equal", adjustable="box")

    return


# ===========================================================
def calculate_path_distance(path):
    distance = 0
    for i in range(0, len(path.coordinates) - 1):
        distance += np.linalg.norm(path.coordinates[i + 1] - path.coordinates[i])
    return distance


# ===========================================================
def plot_path(paths, start, end, obstacles, axes):
    if type(paths) == type([]):
        for path in paths:
            path_x = [start[0]]
            path_y = [start[1]]
            for point in path.coordinates:
                path_x.append(point[0])
                path_y.append(point[1])
            axes.plot(path_x, path_y, marker=".")
            axes.plot(start[0], start[1], marker="x", color="blue")
            axes.plot(end[0], end[1], marker="x", color="green")
        plot_osbtacles(obstacles, axes)
    else:
        path_x = [start[0]]
        path_y = [start[1]]
        for point in paths.coordinates:
            path_x.append(point[0])
            path_y.append(point[1])
            axes.plot(path_x, path_y, marker="X")
            axes.plot(start[0], start[1], marker="x", color="blue")
            axes.plot(end[0], end[1], marker="x", color="green")
        plot_osbtacles(obstacles, axes)
        # bag_clf = BaggingClassifier(DecisionTreeClassifier(), n_estimators=500, oob_score=True, n_jobs=-1, random_state=42)
    return


# ===========================================================
def create_diagonal_obstacles(
    obstacle_number, start, end, min_size, max_size, obstacles
):
    count = 0
    distance = np.linalg.norm(end - start)
    step = distance / (obstacle_number + 1)
    direction_aligned = (end - start) / np.linalg.norm(end - start)
    diretion_perpendicular = np.array([-direction_aligned[1], direction_aligned[0]])
    diretion_perpendicular /= np.linalg.norm(diretion_perpendicular)

    while count < obstacle_number:

        next_position = (
            start + random.uniform(step * 0.5, step * 1.5) * direction_aligned
        )
        obstacle_center = (
            next_position
            + random.uniform(-step * 0.5, step * 0.5) * diretion_perpendicular
        )

        new_obstacle = Obstacle(obstacle_center, random.uniform(min_size, max_size))

        if np.linalg.norm(start - new_obstacle.center) <= new_obstacle.radius * 1.2:
            continue
        elif np.linalg.norm(start - new_obstacle.center) <= new_obstacle.radius * 1.2:
            continue

        if count == 0:
            obstacles.append(new_obstacle)
            count += 1
            start = start + step * direction_aligned
        else:
            obstacles_intersect = 0
            for obstacle in obstacles:
                if (np.linalg.norm(obstacle.center - new_obstacle.center)) < (
                    new_obstacle.radius + obstacle.radius
                ) * 1.2:
                    obstacles_intersect += 1
            if obstacles_intersect == 0:
                obstacles.append(new_obstacle)
                count += 1
                start = start + step * direction_aligned
            else:
                continue
    return obstacles


# ===========================================================
def create_peripheral_obstacles(
    obstacle_number, start, end, min_size, max_size, obstacles
):
    count = 0
    while count < obstacle_number:
        x = random.uniform(start[0], end[0])
        y = random.uniform(start[1], end[1])
        r = random.uniform(min_size, max_size)
        new_obstacle = Obstacle(np.array([x, y]), r)

        if np.linalg.norm(start - new_obstacle.center) <= new_obstacle.radius * 1.2:
            continue
        elif np.linalg.norm(end - new_obstacle.center) <= new_obstacle.radius * 1.2:
            continue

        obstacles_intersect = 0

        for obstacle in obstacles:
            if (np.linalg.norm(obstacle.center - new_obstacle.center)) < (
                new_obstacle.radius + obstacle.radius
            ) * 1.2:
                obstacles_intersect += 1
        if obstacles_intersect == 0:
            obstacles.append(new_obstacle)
            count += 1
        else:
            continue

    return obstacles


# ===========================================================
def create_random_obstacles(
    diag_obstacle_number,
    periph_obstacle_number,
    start,
    end,
    min_size,
    max_size,
    per_obs_coef,
):
    obstacles = []

    obstacles = create_diagonal_obstacles(
        diag_obstacle_number, start, end, min_size, max_size, obstacles
    )
    obstacles = create_peripheral_obstacles(
        periph_obstacle_number,
        start,
        end,
        min_size * per_obs_coef,
        max_size * per_obs_coef,
        obstacles,
    )

    return obstacles


# ===========================================================
def line_circle_intersection(start, end, obstacle):
    if np.linalg.norm(end - start) == 0:
        return False
    line_segment = (end - start) / np.linalg.norm(end - start)
    displacement = obstacle.center - start

    projection = np.dot(line_segment, displacement) / np.linalg.norm(line_segment)
    closest_point = start + projection * line_segment
    dist_closest_center = np.linalg.norm(closest_point - obstacle.center)
    dist_closest_start = np.linalg.norm(closest_point - start)
    dist_closest_end = np.linalg.norm(closest_point - end)
    dist_start_end = np.linalg.norm(end - start)
    dist_center_end = np.linalg.norm(end - obstacle.center)

    if dist_center_end < obstacle.radius or (
        dist_closest_center < obstacle.radius
        and dist_closest_start + dist_closest_end - dist_start_end < 0.0
    ):
        return True
    else:
        return False


# ===========================================================
def find_tangent(point, obstacle):
    displacement = point - obstacle.center
    distance = np.linalg.norm(displacement)
    angle = np.arctan2(displacement[1], displacement[0])

    tangent_angle1 = angle + np.arccos(obstacle.radius / distance)
    tangent_angle2 = angle - np.arccos(obstacle.radius / distance)

    tangent_position1 = obstacle.center + obstacle.radius * np.array(
        [np.cos(tangent_angle1), np.sin(tangent_angle1)]
    )
    tangent_position2 = obstacle.center + obstacle.radius * np.array(
        [np.cos(tangent_angle2), np.sin(tangent_angle2)]
    )

    return tangent_position1, tangent_position2


# ===========================================================
def choose_direction(tang_1, tang_2, end, direction, selection_type):
    if selection_type == "bidirectional":
        if direction == 0:
            return tang_1, tang_2
        else:
            return tang_2, tang_1
    elif selection_type == "closest_path":
        dist_1 = np.linalg.norm(tang_1 - end)
        dist_2 = np.linalg.norm(tang_2 - end)
        if dist_1 < dist_2:
            return tang_1, tang_2
        else:
            return tang_2, tang_1
    else:
        print("ERROR: selection_type input is invalid.")
        return tang_1, tang_2


# ===========================================================
def calculate_next_step(start, end, step, obstacles, direction):
    next_step = start + step * (end - start) / np.linalg.norm(end - start)

    for obstacle in obstacles:
        if line_circle_intersection(start, next_step, obstacle) == True:
            tang_1, tang_2 = find_tangent(start, obstacle)
            tang_1, tang_2 = choose_direction(
                tang_1, tang_2, end, direction, "bidirectional"
            )
            next_step_1 = start + step * (tang_1 - start) / np.linalg.norm(
                tang_1 - start
            )
            next_step_2 = start + step * (tang_2 - start) / np.linalg.norm(
                tang_2 - start
            )
            return next_step_1, True, [obstacle], next_step_2

    return next_step, False, [], np.array([0, 0])


# ===========================================================
def path_planning(path, paths, start, end, step, obstacles):
    current = start

    while np.linalg.norm(current - end) > step / 2:
        current, encounter, obstacle, next_option = calculate_next_step(
            current, end, step, obstacles, path.direction
        )
        if encounter == True and obstacle not in path.obstacles:
            path.add_obstacle(obstacle)
            new_path_obstacles = path.obstacles.copy()
            alternative_path = np.vstack((path.coordinates, next_option))
            new_path = Path(
                alternative_path, new_path_obstacles, False, not path.direction
            )
            paths.append(new_path)

        path.coordinates = np.vstack((path.coordinates, current))
    path.status = True

    return path, paths


# ===========================================================
def finding_all_routes(start, end, step, obstacles):

    initial_section = np.array([start])
    path = Path(initial_section, [], False, 0)
    paths = [path]

    for path in paths:
        path_planning(path, paths, path.coordinates[-1], end, step, obstacles)

    print("All possible routes calculated. Total routes: {np:d}".format(np=len(paths)))

    return paths


# ===========================================================
def shortest_path(paths):

    distance = []
    for path in paths:
        distance.append(path.calculate_distance())

    index = distance.index(min(distance))
    return paths[index]


# ===========================================================
start = np.array([0, 0])
end = np.array([10, 10])
min_size = 0.5
max_size = 1
per_obs_coef = 0.5
step = 0.5

obstacles = create_random_obstacles(4, 50, start, end, min_size, max_size, per_obs_coef)

paths = finding_all_routes(start, end, step, obstacles)
shortest_p = shortest_path(paths)


figure, axes = plt.subplots()
plot_path(paths, start, end, obstacles, axes)
figure2, axes2 = plt.subplots()
plot_path(shortest_p, start, end, obstacles, axes2)

plt.show()
