# import pygame
import math
import random

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# ===========================================================


class Obstacle:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    center = []
    radius = 0


# ===========================================================


def calculate_distance(point_1, point_2):
    distance = math.sqrt(
        (point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2
    )
    return distance


# ===========================================================


def plot_osbtacles(obstacles, axes):
    for obstacle in obstacles:
        circle = Circle(
            (obstacle.center[0], obstacle.center[1]),
            obstacle.radius,
            edgecolor="red",
            facecolor="none",
        )
        axes.add_patch(circle)

    axes.set_aspect("equal", adjustable="box")
    return


# ===========================================================


def plot_path(path, start, finish, obstacles, axes):
    path_x = [start[0]]
    path_y = [start[1]]
    for point in path:
        path_x.append(point[0])
        path_y.append(point[1])
    axes.plot(path_x, path_y, marker="o", color="orange")
    axes.plot(start[0], start[1], marker="x", color="blue")
    axes.plot(finish[0], finish[1], marker="x", color="red")
    plot_osbtacles(obstacles, axes)
    return


# ===========================================================


def find_tangent(point, obstacle):
    x_1 = point[0]
    y_1 = point[1]
    x_2 = obstacle.center[0]
    y_2 = obstacle.center[1]
    distance = calculate_distance(point, obstacle.center)
    radius_1 = math.sqrt(abs(distance**2 - obstacle.radius**2))
    radius_2 = obstacle.radius

    a = (radius_1**2 - radius_2**2 + distance**2) / (2 * distance)
    b = (radius_2**2 - radius_1**2 + distance**2) / (2 * distance)
    height = math.sqrt(radius_1**2 - a**2)

    x_5 = x_1 + (a / distance) * (x_2 - x_1)
    y_5 = y_1 + (a / distance) * (y_2 - y_1)

    tang_x1 = x_5 - height * (y_2 - y_1) / distance
    tang_y1 = y_5 + height * (x_2 - x_1) / distance
    tang_x2 = x_5 + height * (y_2 - y_1) / distance
    tang_y2 = y_5 - height * (x_2 - x_1) / distance

    return [tang_x1, tang_y1], [tang_x2, tang_y2]


# ===========================================================


def choose_direction(tang_1, tang_2, finish):
    dist_1 = calculate_distance(tang_1, finish)
    dist_2 = calculate_distance(tang_2, finish)
    if dist_1 < dist_2:
        return tang_1
    else:
        return tang_2


# ===========================================================


def create_diagonal_obstacles(
    obstacle_number, start, finish, min_size, max_size, obstacles
):
    slope_1 = (finish[1] - start[1]) / (finish[0] - start[0])
    slope_2 = -1 / slope_1
    yintercept_1 = start[1] - slope_1 * start[0]
    dist = calculate_distance(start, finish)
    step = dist / (obstacle_number + 1)
    count = 0

    while count < obstacle_number:
        jump = random.uniform(step * 0.5, step * 1.5)
        next_position, x_1, y_1 = calculate_next_step(start, finish, jump, [])
        yintercept_2 = y_1 - slope_2 * x_1
        jump = random.uniform(-1, 1)
        x_2 = x_1 + jump * 2
        y_2 = slope_2 * x_2 + yintercept_2
        next_position, x_2, y_2 = calculate_next_step([x_1, y_1], [x_2, y_2], jump, [])
        new_obstacle = Obstacle([x_2, y_2], random.uniform(min_size, max_size))

        if calculate_distance(start, new_obstacle.center) <= new_obstacle.radius * 1.1:
            continue
        elif (
            calculate_distance(finish, new_obstacle.center) <= new_obstacle.radius * 1.1
        ):
            continue

        if count == 0:
            obstacles.append(new_obstacle)
            count += 1
            start, x, y = calculate_next_step(start, finish, step, [])
        else:
            obstacles_intersect = 0
            for obstacle in obstacles:
                if (calculate_distance(obstacle.center, new_obstacle.center)) < (
                    new_obstacle.radius + obstacle.radius
                ) * 1.2:
                    obstacles_intersect += 1
            if obstacles_intersect == 0:
                obstacles.append(new_obstacle)
                count += 1
                start, x, y = calculate_next_step(start, finish, step, [])
            else:
                continue

    return obstacles


# ===========================================================


def create_peripheral_obstacles(
    obstacle_number, start, finish, min_size, max_size, obstacles
):
    count = 0
    while count < obstacle_number:
        x = random.uniform(start[0], finish[0])
        y = random.uniform(start[1], finish[1])
        r = random.uniform(min_size, max_size)
        new_obstacle = Obstacle([x, y], r)

        if calculate_distance(start, new_obstacle.center) <= new_obstacle.radius * 1.1:
            continue
        elif (
            calculate_distance(finish, new_obstacle.center) <= new_obstacle.radius * 1.1
        ):
            continue

        obstacles_intersect = 0

        for obstacle in obstacles:
            if (calculate_distance(obstacle.center, new_obstacle.center)) < (
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


def calculate_next_destination(start, finish, step):
    if start[0] == finish[0]:
        if start[1] <= finish[1]:
            next_step = [start[0], start[1] + step]
            next_step_x = next_step[0]
            next_step_y = next_step[1]
        else:
            next_step = [start[0], start[1] - step]
            next_step_x = next_step[0]
            next_step_y = next_step[1]
    else:
        slope = (finish[1] - start[1]) / (finish[0] - start[0])
        y_intercept = start[1] - slope * start[0]
        angle = abs(math.atan(slope))
        if start[0] <= finish[0]:
            next_step_x = start[0] + step * math.cos(angle)
        else:
            next_step_x = start[0] - step * math.cos(angle)

        if start[1] <= finish[1]:
            next_step_y = start[1] + step * math.sin(angle)
        else:
            next_step_y = start[1] - step * math.sin(angle)
        next_step = [next_step_x, next_step_y]
        return next_step, next_step_x, next_step_y


# ===========================================================


def calculate_next_step(start, finish, step, obstacles):

    next_step, next_step_x, next_step_y = calculate_next_destination(
        start, finish, step
    )

    a = (next_step_y - start[1]) / (next_step_x - start[0])
    b = 1
    c = next_step_y - a * next_step_x

    for obstacle in obstacles:
        x_0 = obstacle.center[0]
        y_0 = obstacle.center[1]
        d = abs(a * x_0 + b * y_0 + c) / (math.sqrt(a**2 + b**2))
        x_c = (b * (b * x_0 - a * y_0) - a * c) / (a**2 + b**2)
        y_c = (a * (-b * x_0 + a * y_0) - b * c) / (a**2 + b**2)
        dist_1 = calculate_distance(start, [x_c, y_c])
        dist_2 = calculate_distance(next_step, [x_c, y_c])
        d_3 = calculate_distance(start, next_step)
        if calculate_distance(next_step, obstacle.center) <= obstacle.radius or (
            d < obstacle.radius * 1.5 and abs(dist_1 + dist_2 - d_3) < 0.1
        ):
            tang_1, tang_2 = find_tangent(start, obstacle)
            tang = choose_direction(tang_1, tang_2, finish)
            next_step, next_step_x, next_step_y = calculate_next_destination(
                start, tang, step
            )

    return next_step, next_step_x, next_step_y


# ===========================================================


def path_planning(start, finish, step, obstacles):
    path = []
    path_x = [start[0]]
    path_y = [start[1]]

    current = start
    count = 1

    while calculate_distance(current, finish) > step / 2:
        current, next_step_x, next_step_y = calculate_next_step(
            current, finish, step, obstacles
        )
        path_x.append(next_step_x)
        path_y.append(next_step_y)
        path.append(current)

    return path, path_x, path_y


# ===========================================================

start = [0, 0]
finish = [110, 100]
min_size = 10
max_size = 20
step = min_size / 2
obstacles = []

obstacles = create_diagonal_obstacles(2, start, finish, min_size, max_size, obstacles)
obstacles = create_peripheral_obstacles(
    30, start, finish, min_size / 3, max_size, obstacles
)


path, path_x, path_y = path_planning(start, finish, step, obstacles)

figure, axes = plt.subplots()
plot_path(path, start, finish, obstacles, axes)


plt.show()
