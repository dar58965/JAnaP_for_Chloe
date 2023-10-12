import cv2
import numpy
import math
import scipy

import scipy.ndimage
import skimage.morphology
import scipy.ndimage

from cells.utility import check_intercept
from cells.utility import find_minimum_bounding_rectangle

LINEAR = 1
PUNCTATE = 2
PERPENDICULAR = 3

classification_enum = {
    LINEAR: "Linear",
    PUNCTATE: "Punctate",
    PERPENDICULAR: "Perpendicular"
}


def get_segment_inner_path(segment_mass, perimeter_path):
    min_path_idx, max_path_idx = None, None

    for e in numpy.transpose(numpy.nonzero(segment_mass)):
        r, c = e

        for e_idx in range(0, len(perimeter_path)):
            r_path, c_path = perimeter_path[e_idx]
            if r_path == r and c_path == c:
                if min_path_idx is None or e_idx < min_path_idx:
                    min_path_idx = e_idx
                if max_path_idx is None or e_idx > max_path_idx:
                    max_path_idx = e_idx

    if min_path_idx is None or max_path_idx is None:
        return None

    inner_path = perimeter_path[min_path_idx:max_path_idx + 1]

    return inner_path


def get_medial_axis_length(segment_mass):
    struct_full = scipy.ndimage.generate_binary_structure(2, 2)

    medial_axis = skimage.morphology.medial_axis(segment_mass)

    medial_axis_endpoints = []

    for e in numpy.transpose(numpy.nonzero(medial_axis)):
        r, c = e

        current_mass = numpy.zeros(segment_mass.shape)
        current_mass[r, c] = 1
        dilated = scipy.ndimage.binary_dilation(current_mass, structure=struct_full)
        dilated[r, c] = 0

        if numpy.sum(medial_axis[dilated == 1]) == 1:
            medial_axis_endpoints.append(e)

    medial_axis_length = 0
    medial_axis_points = None

    for point_1 in medial_axis_endpoints:
        r1, c1 = point_1
        for point_2 in medial_axis_endpoints:
            r2, c2 = point_2
            distance = math.sqrt((c2 - c1) ** 2 + (r2 - r1) ** 2)

            if distance > medial_axis_length:
                medial_axis_length = distance
                medial_axis_points = (point_1, point_2)

    return medial_axis_length


def get_rectangle_axis(segment_mass):
    rectangle_corners = find_minimum_bounding_rectangle(segment_mass)

    r1, c1 = rectangle_corners[0]
    r2, c2 = rectangle_corners[1]
    d1 = math.sqrt((c2 - c1) ** 2 + (r2 - r1) ** 2)

    r1, c1 = rectangle_corners[1]
    r2, c2 = rectangle_corners[2]
    d2 = math.sqrt((c2 - c1) ** 2 + (r2 - r1) ** 2)

    major_rectangle = max([d1, d2])
    minor_rectangle = min([d1, d2])

    return major_rectangle, minor_rectangle


def classify_segments(image_processed, segment_mask, perimeter_path,
                      linear_minimum_length, path_ratio=4.0, aspect_ratio=3.5):
    classifications = {}
    details = []

    for idx in numpy.unique(segment_mask):
        idx = int(idx)

        if idx == 0:
            continue

        segment_mass = segment_mask.copy()
        segment_mass[segment_mass != idx] = 0
        segment_mass[segment_mass > 0] = 1

        inner_path = get_segment_inner_path(segment_mass, perimeter_path)

        if inner_path is None:
            continue

        path_axis_length = len(inner_path)
        medial_axis_length = get_medial_axis_length(segment_mass)
        aspect_ratio_rel_path = float(medial_axis_length) / float(path_axis_length)

        if len(numpy.transpose(numpy.nonzero(segment_mass))) > 3:
            major_rectangle, minor_rectangle = get_rectangle_axis(segment_mass)
            aspect_ratio_rect = float(major_rectangle) / float(minor_rectangle)
        else:
            major_rectangle, minor_rectangle = None, None
            aspect_ratio_rect = 1

        if len(inner_path) > linear_minimum_length:
            # Linear
            classifications[idx] = LINEAR
        else:
            if aspect_ratio_rel_path > path_ratio and aspect_ratio_rect > aspect_ratio:
                # Perpendicular
                classifications[idx] = PERPENDICULAR
            else:
                # Punctate
                classifications[idx] = PUNCTATE

        details.append([idx,
                        len(inner_path),
                        aspect_ratio_rel_path,
                        aspect_ratio_rect,
                        medial_axis_length, path_axis_length,
                        major_rectangle, minor_rectangle])

    return classifications, details