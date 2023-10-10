
from skimage import graph

def get_perimeter(image_cost, waypoints):
    path = []

    for idx in range(0, len(waypoints)):
        start_point = waypoints[idx]
        end_point = waypoints[(idx + 1) % len(waypoints)]

        path_segment, cost = graph.route_through_array(image_cost, start_point, end_point)
        for e in path_segment:
            path.append(e)

    return path