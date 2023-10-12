import numpy

import scipy.ndimage

from cells.utility import check_intercept
from matplotlib import pyplot

def get_feature_mask(image_gray, filter_threshold):
    """
    Get all of the features within a given image

    Returns a 2d numpy array with each location that is part of a feature
    labeled with the index for that mass

    :return:
    """

    # Filter all pixels below the filter threshold from the image
    image_filtered = image_gray.copy()
    image_filtered[image_gray < filter_threshold] = 0

    # Convert the image to binary
    image_binary = image_filtered.copy()
    image_binary[image_filtered > 0] = 1

    # Label masses within the image
    binary_full = scipy.ndimage.generate_binary_structure(2, 2)
    feature_mask, image_num_objects = scipy.ndimage.label(image_binary, structure=binary_full)

    return feature_mask


def get_segments_mask(features, perimeter_path):
    if isinstance(features, dict):
        raise Exception("Requires a features mask.")

    segments_mask = numpy.zeros(features.shape)

    p_array = numpy.array(perimeter_path)
    intercept_feature_idxs = numpy.unique(features[p_array[:, 0], p_array[:, 1]].ravel())

    for idx in numpy.unique(intercept_feature_idxs):
        if idx == 0:
            continue

        feature_mass = features.copy()
        feature_mass[feature_mass != idx] = 0
        feature_mass[feature_mass > 0] = 1

        segments_mask[feature_mass > 0] = idx

    return segments_mask


def refine_segments(image_processed, segments_mask, perimeter, filter_threshold=15):
    """
    Determine if the feature should be broken into smaller pieces

    """
    image_filtered = image_processed.copy()
    image_filtered[image_processed < filter_threshold] = 0

    next_label = numpy.max(segments_mask)

    is_done = False
    while not is_done:
        is_done = True
        segments_mask_temp = segments_mask.copy()

        for idx_f in numpy.unique(segments_mask):
            idx = int(idx_f)
            if idx == 0:
                continue

            current_mass = numpy.zeros(segments_mask.shape)
            current_mass[segments_mask == idx_f] = image_processed[segments_mask == idx_f]
            if (numpy.count_nonzero(current_mass)) < 10:
                continue

            for iteration in range(0, 5):
                m_mass = current_mass.copy()
                m_mass[m_mass == 0] = 255
                current_mass[numpy.unravel_index(numpy.argmin(m_mass), image_processed.shape)] = 0

            # Label masses within the image
            binary_full = scipy.ndimage.generate_binary_structure(2, 2)
            cm_feature_mask, image_num_objects = scipy.ndimage.label(current_mass, structure=binary_full)

            if image_num_objects > 1:
                segments_mask_temp[segments_mask_temp == idx_f] = 0

                for n_v in range(1, image_num_objects + 1):
                    segments_mask_temp[cm_feature_mask == n_v] = next_label
                    next_label += 1
                is_done = False

        segments_mask = segments_mask_temp.copy()

    return segments_mask