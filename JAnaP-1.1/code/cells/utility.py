import numpy

from scipy.ndimage.interpolation import rotate
from scipy.spatial import ConvexHull

def check_intercept(mass_1, mass_2):
    """
    Check whether two masses intercept with each other
    :param mass_1:
    :param mass_2:
    :return:
    """

    for e_m1 in mass_1:
        r1, c1 = e_m1
        for e_m2 in mass_2:
            r2, c2 = e_m2
            if r1 == r2 and c1 == c2:
                return True

    return False

def intersect_2d(arr1, arr2):
    arr1_view = arr1.view([('',numpy.int16)]*arr1.shape[1])
    arr2_view = arr2.view([('',numpy.int16)]*arr2.shape[1])
    intersected = numpy.intersect1d(arr1_view, arr2_view)
    return intersected.reshape(-1, 2)


def poly_area_2d(pts):
    lines = numpy.hstack([pts,numpy.roll(pts,-1,axis=0)])
    area = 0.5*abs(sum(x1*y2-x2*y1 for x1,y1,x2,y2 in lines))
    return area

def shoelace_area(points):
    n = len(points) # of corners
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    area = abs(area) / 2.0
    return area


def find_minimum_bounding_rectangle(mass):
    """
    Find the smallest bounding rectangle for a set of points.
    Returns a set of points representing the corners of the bounding box.

    :param
    :rval: an nx2 matrix of coordinates
    """
    # Convert mass to points: an nx2 matrix of coordinates
    points = numpy.transpose(numpy.nonzero(mass))

    pi2 = numpy.pi / 2.

    # get the convex hull for the points
    hull_points = points[ConvexHull(points).vertices]

    # calculate edge angles
    edges = numpy.zeros((len(hull_points) - 1, 2))
    edges = hull_points[1:] - hull_points[:-1]

    angles = numpy.zeros((len(edges)))
    angles = numpy.arctan2(edges[:, 1], edges[:, 0])

    angles = numpy.abs(numpy.mod(angles, pi2))
    angles = numpy.unique(angles)

    # find rotation matrices
    rotations = numpy.vstack([
        numpy.cos(angles),
        numpy.cos(angles - pi2),
        numpy.cos(angles + pi2),
        numpy.cos(angles)]).T

    rotations = rotations.reshape((-1, 2, 2))

    # apply rotations to the hull
    rot_points = numpy.dot(rotations, hull_points.T)

    # find the bounding points
    min_x = numpy.nanmin(rot_points[:, 0], axis=1)
    max_x = numpy.nanmax(rot_points[:, 0], axis=1)
    min_y = numpy.nanmin(rot_points[:, 1], axis=1)
    max_y = numpy.nanmax(rot_points[:, 1], axis=1)

    # find the box with the best area
    areas = (max_x - min_x) * (max_y - min_y)
    best_idx = numpy.argmin(areas)

    # return the best box
    x1 = max_x[best_idx]
    x2 = min_x[best_idx]
    y1 = max_y[best_idx]
    y2 = min_y[best_idx]
    r = rotations[best_idx]

    rval = numpy.zeros((4, 2))
    rval[0] = numpy.dot([x1, y2], r)
    rval[1] = numpy.dot([x2, y2], r)
    rval[2] = numpy.dot([x2, y1], r)
    rval[3] = numpy.dot([x1, y1], r)

    return rval
