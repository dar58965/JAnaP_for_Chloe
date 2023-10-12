import os
import math
import numpy

import skimage.draw
import skimage.measure
import scipy.ndimage
import cells.images
import cells.images.filter
import cells.shapes

from matplotlib import pyplot

from cells.utility import check_intercept

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
    

def get_smoothed_paths(path, window_size):
    ma_perimeter = []
    ma_perimeter_float = []
    slmp_perimeter = []

    for idx in range(0, len(path)):
        r, c = path[idx]

        # Moving Average Method
        r_total, c_total = 0, 0

        for ma_idx in range(idx - window_size, idx + window_size):
            ma_idx = ma_idx % len(path)
            w_r, w_c = path[ma_idx]
            r_total, c_total = r_total + w_r, c_total + w_c

        ma_perimeter.append(
            [r_total / (2 * window_size), c_total / (2 * window_size)])
        ma_perimeter_float.append([float(r_total) / (2.0 * window_size),
                                   float(c_total) / (2.0 * window_size)])

        # Straight Line Midpoint Method
        slmp_start_idx = idx - window_size
        slmp_end_idx = (idx + window_size) % len(path)

        slmp_s_r, slmp_s_c = path[slmp_start_idx]
        slmp_e_r, slmp_e_c = path[slmp_end_idx]

        slmp_perimeter.append(
            [(slmp_s_r + slmp_e_r) / 2, (slmp_s_c + slmp_e_c) / 2])

    ma_path = numpy.asarray(ma_perimeter)
    ma_path_float = numpy.asarray(ma_perimeter_float)
    slmp_path = numpy.asarray(slmp_perimeter)

    return ma_path, slmp_path, ma_path_float


def __path_length(x, y):
    n = len(x)
    lv = [math.sqrt((x[i]-x[i-1])**2 + (y[i]-y[i-1])**2) for i in range (1,n)]
    L = sum(lv)
    return L

def __get_path_ar_length(bin_mask, path):
    min_idx, max_idx = None, None

    for p_idx in range(0, len(path)):
        if bin_mask[path[p_idx][0], path[p_idx][1]]:
            if min_idx is None or p_idx < min_idx:
                min_idx = p_idx
            if max_idx is None or p_idx > max_idx:
                max_idx = p_idx

    if min_idx == max_idx:
        path_ar_length = 1
    else:
        max_idx = max_idx + 1 % len(path)
        inner_path = path[min_idx:max_idx, :]
        path_ar_length = __path_length(inner_path[:, 0], inner_path[:, 1])

    return int(path_ar_length)

def __get_ma_path_length(bin_mask, ma_path):
    min_idx, max_idx = None, None

    for p_idx in range(0, len(ma_path)):
        if bin_mask[ma_path[p_idx][0], ma_path[p_idx][1]]:
            if min_idx is None or p_idx < min_idx:
                min_idx = p_idx
            if max_idx is None or p_idx > max_idx:
                max_idx = p_idx

    if min_idx is None or max_idx is None:
        return None

    if min_idx == max_idx:
        ma_ar_length = 1
    else:
        ma_ar_length = math.sqrt(
            (float(ma_path[min_idx][0]) - float(ma_path[max_idx][0])) ** 2 + \
            (float(ma_path[min_idx][1]) - float(ma_path[max_idx][1])) ** 2)

    return int(ma_ar_length)


def __get_slmp_path_length(bin_mask, slmp_path):
    min_idx, max_idx = None, None

    for p_idx in range(0, len(slmp_path)):
        if bin_mask[slmp_path[p_idx][0], slmp_path[p_idx][1]]:
            if min_idx is None or p_idx < min_idx:
                min_idx = p_idx
            if max_idx is None or p_idx > max_idx:
                max_idx = p_idx

    if min_idx is None or max_idx is None:
        return None

    if min_idx == max_idx:
        slmp_ar_length = 1
    else:
        slmp_ar_length = math.sqrt(
            (float(slmp_path[min_idx][0]) - float(slmp_path[max_idx][0])) ** 2 + \
            (float(slmp_path[min_idx][1]) - float(slmp_path[max_idx][1])) ** 2)

    return int(slmp_ar_length)


def get_cell_junction_sums(segment_data):
    coverage_count = 0
    continuous_count = 0
    punct_count = 0
    perp_count = 0
    perimeter_count = 0

    coverage_length = 0.0
    continuous_length = 0.0
    punct_length = 0.0
    perp_length = 0.0
    perimeter_length = 0.0

    for seg in segment_data:
        if seg["classification"] == "Continuous":
            continuous_count += seg["segment_length_px"]
            coverage_count += seg["segment_length_px"]

            continuous_length += seg["path_ar_length"]
            coverage_length += seg["path_ar_length"]
        elif seg["classification"] == "Punctate":
            punct_count += seg["segment_length_px"]
            coverage_count += seg["segment_length_px"]

            punct_length += seg["path_ar_length"]
            coverage_length += seg["path_ar_length"]
        elif seg["classification"] == "Perpendicular":
            perp_count += seg["segment_length_px"]
            coverage_count += seg["segment_length_px"]

            perp_length += seg["path_ar_length"]
            coverage_length += seg["path_ar_length"]
        else:
            pass
        
        perimeter_length += seg["path_ar_length"]
        perimeter_count += seg["segment_length_px"]

    coverage_percent = float(coverage_count) / float(perimeter_length) * 100.0
    continuous_percent = float(continuous_count) / float(perimeter_length) * 100.0
    punct_percent = float(punct_count) / float(perimeter_length) * 100.0
    perp_percent = float(perp_count) / float(perimeter_length) * 100.0
    discontinuous_percent = float(punct_count + perp_count) / float(perimeter_length) * 100.0

    summary_data = {
        "coverage_percent": coverage_percent,
        "continuous_percent": continuous_percent,
        "punct_percent": punct_percent,
        "perp_percent": perp_percent,
        "discontinuous_percent": discontinuous_percent,
        "coverage_count": coverage_count,
        "continuous_count": continuous_count,
        "punct_count": punct_count,
        "perp_count": perp_count, 
        "continuous_length": continuous_length,
        "punctate_length": punct_length,
        "perpendicular_length": perp_length
    }

    return summary_data


def get_cell_junction_data_fast(feature_mask, perimeter, window_size):
    perpendicular_aspect_ratio_threshold = 1.2
    continuous_min_path_length_px = 15

    w, h = feature_mask.shape

    if w == 1024:
            continuous_min_path_length = continuous_min_path_length_px
    elif w == 2048:
            continuous_min_path_length = continuous_min_path_length_px*2
    
    binary_full = scipy.ndimage.generate_binary_structure(2, 2)

    path = numpy.asarray(perimeter)

    path_mask = numpy.zeros(feature_mask.shape)
    path_mask[path[:, 0], path[:, 1]] = 1

    r_cell_min, r_cell_max = numpy.min(path[:, 0]), \
                             numpy.max(path[:, 0])
    c_cell_min, c_cell_max = numpy.min(path[:, 1]), \
                             numpy.max(path[:, 1])

    i_r_max, i_c_max = feature_mask.shape
    frame_r_min, frame_r_max = max([r_cell_min - 25, 0]), min(
        [r_cell_max + 25, i_r_max])
    frame_c_min, frame_c_max = max([c_cell_min - 25, 0]), min(
        [c_cell_max + 25, i_c_max])

    # Stick to only nearby area
    feature_mask_filtered = feature_mask[frame_r_min:frame_r_max,
                                         frame_c_min:frame_c_max]

    path_feature_intersection = numpy.multiply(feature_mask, path_mask)

    feature_path_heatmap_absolute = numpy.zeros(feature_mask.shape)

    feature_objects = {}

    for feature_idx in numpy.unique(feature_mask_filtered):
        feature_idx = int(feature_idx)
        if feature_idx == 0:
            continue
        
        feature_point_arr = []

        for feature_point in numpy.transpose(
                numpy.nonzero(feature_mask == feature_idx)):
            
            feature_point_arr.append(feature_point)

            path_distances = numpy.sqrt(
                numpy.power((path[:, 0] - feature_point[0]), 2) + \
                numpy.power((path[:, 1] - feature_point[1]), 2))
            feature_path_heatmap_absolute[
                feature_point[0], feature_point[1]] = min(path_distances) + 1
        
        feature_objects[feature_idx] = feature_point_arr

    segment_data = []

    p_current_idx = 0

    while p_current_idx < len(perimeter):
        p_start_idx = p_current_idx
        
        r, c = perimeter[p_current_idx]
        current_feature_idx = feature_mask[r, c] 

        feature_idx = current_feature_idx

        while feature_idx == current_feature_idx:
            p_current_idx += 1

            if p_current_idx >= len(perimeter):
                break
            
            r, c = perimeter[p_current_idx]
            feature_idx = feature_mask[r, c] 

        p_end_idx = p_current_idx
        feature_idx = current_feature_idx

        inner_path = path[p_start_idx:p_end_idx+1, :]
        path_ar_length = __path_length(inner_path[:, 0], inner_path[:, 1])
        inner_path_length_px = len(inner_path)

        t_dist_abs = None
        relative_path_aspect_ratio = None
        classification = None
        classification_simple = None

        if feature_idx > 0:
            bin_mask_temp = feature_mask == feature_idx
            bin_mask_temp[path[:, 0], path[:, 1]] = 0
            subfeature_path, path_subfeatures = scipy.ndimage.label(bin_mask_temp,
                                                                structure=binary_full)
            
            if path_subfeatures == 0:
                 t_dist_abs = 0
            elif path_subfeatures == 1:
                t_dist_abs = \
                    numpy.max(feature_path_heatmap_absolute[feature_mask == feature_idx]) - 1
            elif path_subfeatures == 2:
                t_dist_abs = \
                    numpy.max(feature_path_heatmap_absolute[subfeature_path == 1]) + \
                    numpy.max(feature_path_heatmap_absolute[subfeature_path == 2]) - 2
            else:
                t_dist_abs = \
                    numpy.max(feature_path_heatmap_absolute[subfeature_path == 1]) + \
                    numpy.max(feature_path_heatmap_absolute[subfeature_path == 2]) - 2

            relative_path_aspect_ratio = t_dist_abs / path_ar_length

            if path_ar_length >= continuous_min_path_length:
                classification = "Continuous"
                classification_simple = "Continuous"
            elif path_ar_length < continuous_min_path_length and \
                 relative_path_aspect_ratio is not None and \
                            relative_path_aspect_ratio > perpendicular_aspect_ratio_threshold:
                classification = "Perpendicular"
                classification_simple = "Discontinuous"
            else:
                classification = "Punctate"
                classification_simple = "Discontinuous"

        segment_data.append({
            "path_start_idx": p_start_idx,
            "path_end_idx": p_end_idx,
            "feature_idx": int(feature_idx),
            
            "segment_length_px": inner_path_length_px,
            "path_ar_length": path_ar_length,
            "t_dist_abs": t_dist_abs,
            "relative_path_aspect_ratio": relative_path_aspect_ratio,

            "classification": classification,
            "classification_simple": classification_simple,

            "param_perpendicular_aspect_ratio_threshold": perpendicular_aspect_ratio_threshold,
            "param_continuous_min_path_length": continuous_min_path_length,
        })

        # print p_start_idx, p_end_idx, path_ar_length, relative_path_aspect_ratio, classification, classification_simple

    return segment_data, feature_objects


def get_cell_junction_data(feature_mask, perimeter, window_size):
 
    #get_cell_junction_data_fast(feature_mask, perimeter, window_size)
    #exit()

    perpendicular_aspect_ratio_threshold = 1.2
    continuous_min_path_length_px = 15

    w, h = feature_mask.shape

    if w == 1024:
            continuous_min_path_length = continuous_min_path_length_px
    elif w == 2048:
            continuous_min_path_length = continuous_min_path_length_px*2
    
    # Kept from master branch
    linear_min_path_length = 15
    linear_max_normal_distance = 92

    binary_full = scipy.ndimage.generate_binary_structure(2, 2)

    path = numpy.asarray(perimeter)

    path_mask = numpy.zeros(feature_mask.shape)
    path_mask[path[:, 0], path[:, 1]] = 1

    r_cell_min, r_cell_max = numpy.min(path[:, 0]), \
                             numpy.max(path[:, 0])
    c_cell_min, c_cell_max = numpy.min(path[:, 1]), \
                             numpy.max(path[:, 1])


    i_r_max, i_c_max = feature_mask.shape
    frame_r_min, frame_r_max = max([r_cell_min - 25, 0]), min(
        [r_cell_max + 25, i_r_max])
    frame_c_min, frame_c_max = max([c_cell_min - 25, 0]), min(
        [c_cell_max + 25, i_c_max])

    # Stick to only nearby area
    feature_mask_filtered = feature_mask[frame_r_min:frame_r_max,
                                         frame_c_min:frame_c_max]

    ma_path, slmp_path, ma_path_float = get_smoothed_paths(path, window_size)

    ma_path_mask = numpy.zeros(feature_mask.shape)
    ma_path_mask[ma_path[:, 0], ma_path[:, 1]] = 1

    slmp_path_mask = numpy.zeros(feature_mask.shape)
    slmp_path_mask[slmp_path[:, 0], slmp_path[:, 1]] = 1

    path_feature_intersection = numpy.multiply(feature_mask, path_mask)
    ma_feature_intersection = numpy.multiply(feature_mask, ma_path_mask)
    slmp_feature_intersection = numpy.multiply(feature_mask, slmp_path_mask)

    feature_path_heatmap_absolute = numpy.zeros(feature_mask.shape)
    feature_ma_heatmap_absolute = numpy.zeros(feature_mask.shape)
    feature_slmp_heatmap_absolute = numpy.zeros(feature_mask.shape)

    for feature_idx in numpy.unique(feature_mask_filtered):
        feature_idx = int(feature_idx)
        if feature_idx == 0:
            continue

        bin_mask = feature_mask == feature_idx

        for feature_point in numpy.transpose(
                numpy.nonzero(feature_mask == feature_idx)):
            ma_distances = numpy.sqrt(
                numpy.power((ma_path[:, 0] - feature_point[0]), 2) + \
                numpy.power((ma_path[:, 1] - feature_point[1]), 2))
            feature_ma_heatmap_absolute[
                feature_point[0], feature_point[1]] = min(ma_distances) + 1

            slmp_distances = numpy.sqrt(
                numpy.power((slmp_path[:, 0] - feature_point[0]), 2) + \
                numpy.power((slmp_path[:, 1] - feature_point[1]), 2))
            feature_slmp_heatmap_absolute[
                feature_point[0], feature_point[1]] = min(slmp_distances) + 1

            path_distances = numpy.sqrt(
                numpy.power((path[:, 0] - feature_point[0]), 2) + \
                numpy.power((path[:, 1] - feature_point[1]), 2))
            feature_path_heatmap_absolute[
                feature_point[0], feature_point[1]] = min(path_distances) + 1


    feature_data = []

    for feature_idx in numpy.unique(feature_mask_filtered):
        feature_idx = int(feature_idx)
        if feature_idx == 0:
            continue

        path_intersect_points = \
            numpy.nonzero(path_feature_intersection == feature_idx)

        intersects_path = (len(path_intersect_points[0]) > 0)

        bin_mask = feature_mask == feature_idx

        feature_size = numpy.count_nonzero(bin_mask)
        feature_perimeter = skimage.measure.perimeter(bin_mask)

        feature_com = scipy.ndimage.measurements.center_of_mass(bin_mask)
        com_distance = min(
            numpy.sqrt(numpy.power((path[:, 0] - feature_com[0]), 2) + \
                       numpy.power((path[:, 1] - feature_com[1]), 2)))


        path_ar_length = __get_path_ar_length(bin_mask, path)
        ma_ar_length = __get_ma_path_length(bin_mask, ma_path)
        slmp_ar_length = __get_slmp_path_length(bin_mask, slmp_path)

        bin_mask_temp = feature_mask == feature_idx
        bin_mask_temp[ma_path[:, 0], ma_path[:, 1]] = 0
        feature_ma, ma_features = scipy.ndimage.label(bin_mask_temp,
                                                      structure=binary_full)

        bin_mask_temp = feature_mask == feature_idx
        bin_mask_temp[slmp_path[:, 0], slmp_path[:, 1]] = 0
        feature_slmp, slmp_features = scipy.ndimage.label(bin_mask_temp,
                                                          structure=binary_full)

        t_dist_abs_ma = None
        t_dist_abs_slmp = None

        if ma_features == 0:
            t_dist_abs_ma = 0
        elif ma_features == 1:
            t_dist_abs_ma = numpy.max(
                feature_ma_heatmap_absolute[feature_mask == feature_idx]) - 1
        elif ma_features == 2:
            t_dist_abs_ma = numpy.max(
                feature_ma_heatmap_absolute[feature_ma == 1]) + \
                            numpy.max(feature_ma_heatmap_absolute[
                                          feature_ma == 2]) - 2
        else:
            t_dist_abs_ma = numpy.max(
                feature_ma_heatmap_absolute[feature_ma == 1]) + \
                            numpy.max(feature_ma_heatmap_absolute[
                                          feature_ma == 2]) - 2

        if slmp_features == 0:
            t_dist_abs_slmp = 0
        elif slmp_features == 1:
            t_dist_abs_slmp = numpy.max(
                feature_slmp_heatmap_absolute[feature_mask == feature_idx]) - 1
        elif slmp_features == 2:
            t_dist_abs_slmp = numpy.max(
                feature_slmp_heatmap_absolute[feature_slmp == 1]) + \
                              numpy.max(feature_slmp_heatmap_absolute[
                                            feature_slmp == 2]) - 2
        else:
            t_dist_abs_slmp = numpy.max(
                feature_slmp_heatmap_absolute[feature_slmp == 1]) + \
                              numpy.max(feature_slmp_heatmap_absolute[
                                            feature_slmp == 2]) - 2

        classification = None
        classification_simple = None
        absolute_path_aspect_ratio = None
        relative_path_aspect_ratio = None
        normal_distance = None

        if intersects_path:
            relative_path_aspect_ratio = None

            if t_dist_abs_ma != None:
                relative_path_aspect_ratio = t_dist_abs_ma / \
                                             path_ar_length

            normal_distance = numpy.sum(numpy.power(
                feature_ma_heatmap_absolute[feature_mask == feature_idx], 2)) / \
                              path_ar_length

            absolute_path_aspect_ratio = t_dist_abs_ma / \
                                         path_ar_length

            if path_ar_length >= continuous_min_path_length:
                classification = "Continuous"
                classification_simple = "Continuous"
            elif path_ar_length < continuous_min_path_length and \
                 relative_path_aspect_ratio is not None and \
                            relative_path_aspect_ratio > perpendicular_aspect_ratio_threshold:
                classification = "Perpendicular"
                classification_simple = "Discontinuous"
            else:
                classification = "Punctate"
                classification_simple = "Discontinuous"


        feature_data.append({
            "feature_idx": int(feature_idx),
            "intersects_path": intersects_path,
            "feature_pixel_area": feature_size,
            "feature_perimeter_px": feature_perimeter,

            "center_of_mass": feature_com,
            "com_path_distance": com_distance,

            "path_ar_length": path_ar_length,
            "slmp_ar_length": slmp_ar_length,
            "ma_ar_length": ma_ar_length,

            "path_abs_max": numpy.max(
                feature_path_heatmap_absolute[feature_mask == feature_idx]),
            "ma_abs_max": numpy.max(
                feature_ma_heatmap_absolute[feature_mask == feature_idx]),
            "slmp_abs_max": numpy.max(
                feature_slmp_heatmap_absolute[feature_mask == feature_idx]),
            "path_abs_avg": numpy.average(
                feature_path_heatmap_absolute[feature_mask == feature_idx]),
            "ma_abs_avg": numpy.average(
                feature_ma_heatmap_absolute[feature_mask == feature_idx]),
            "slmp_abs_avg": numpy.average(
                feature_slmp_heatmap_absolute[feature_mask == feature_idx]),

            "ma_sum": numpy.sum(
                feature_ma_heatmap_absolute[feature_mask == feature_idx]),
            "slmp_sum": numpy.sum(
                feature_slmp_heatmap_absolute[feature_mask == feature_idx]),
            "ma_sum_square": numpy.sum(numpy.power(
                feature_ma_heatmap_absolute[feature_mask == feature_idx], 2)),
            "slmp_sum_square": numpy.sum(numpy.power(
                feature_slmp_heatmap_absolute[feature_mask == feature_idx], 2)),

            "ma_avg_square": numpy.average(numpy.power(
                feature_ma_heatmap_absolute[feature_mask == feature_idx], 2)),
            "slmp_avg_square": numpy.average(numpy.power(
                feature_slmp_heatmap_absolute[feature_mask == feature_idx], 2)),

            "tip_dist_abs_ma": t_dist_abs_ma,
            "tip_dist_abs_slmp": t_dist_abs_slmp,

            "absolute_path_aspect_ratio": absolute_path_aspect_ratio,
            "relative_path_aspect_ratio": relative_path_aspect_ratio,
            "normal_distance": normal_distance,

            "classification": classification,
            "classification_simple": classification_simple,

            "param_perpendicular_aspect_ratio_threshold": perpendicular_aspect_ratio_threshold,
            #"param_perpendicular_max_ma_path_length": perpendicular_max_ma_path_length,
            #"param_perpendicular_minimum_t_dist": perpendicular_minimum_t_dist,
            "param_continuous_min_path_length": continuous_min_path_length,
            #"param_linear_max_normal_distance": linear_max_normal_distance
        })

    return feature_data

def get_junction_width(image_processed, e, norm_vec, threshold):
    r_norm, c_norm = norm_vec
    r_path, c_path = e

    intensity_sum = 0
    intensity_count = 0

    w, h = image_processed.shape

    for t in range(0, 100):
        r_val = r_path + int(r_norm * t)
        c_val = c_path + int(c_norm * t)

        r_r_val = r_norm * t
        r_c_val = c_norm * t

        if r_val >= h or c_val >= w or \
            r_val < 0 or c_val < 0:
            break

        if image_processed[r_val, c_val] < threshold:
            break
        else:
            intensity_sum += image_processed[r_val, c_val]
            intensity_count += 1

    u_r_val, u_c_val = r_r_val, r_c_val

    for t in range(0, 100):
        r_val = r_path + int(r_norm * -t)
        c_val = c_path + int(c_norm * -t)

        r_r_val = r_norm * -t
        r_c_val = c_norm * -t

        if r_val >= h or c_val >= w or \
            r_val < 0 or c_val < 0:
            break

        if image_processed[r_val, c_val] < threshold:
            break
        else:
            intensity_sum += image_processed[r_val, c_val]
            intensity_count += 1

    if intensity_count > 0:
        intensity_average = float(intensity_sum) / float(intensity_count)
    else:
        intensity_average = 0

    d_r_val, d_c_val = r_r_val, r_c_val

    distance = math.sqrt((d_r_val - u_r_val) ** 2 + (d_c_val - u_c_val) ** 2)

    details = (intensity_average, (r_path + u_r_val, c_path + u_c_val),
               (r_path + d_r_val, c_path + d_c_val))

    return distance, details

def get_path_junction_data(image_processed, perimeter, window_size,
                           filter_threshold):
    path = numpy.asarray(perimeter)

    ma_path, slmp_path, ma_path_float = get_smoothed_paths(path, window_size)

    # 2, 4, 8, 16
    feature_mask = get_feature_mask(image_processed, filter_threshold)

    junction_path_data = []

    last_r_unit, last_c_unit = None, None

    for path_idx in range(0, len(path)):
        dr_sum = 0
        dc_sum = 0

        grad_window_size = window_size
        mag = 0

        while int(mag) == 0:
            for smooth_idx in range(path_idx - grad_window_size, path_idx + grad_window_size):
                dr_sum +=  ma_path[(smooth_idx + 1) % len(path)][0] - \
                           ma_path[smooth_idx % len(path)][0]
                dc_sum += ma_path[(smooth_idx + 1) % len(path)][1] - \
                          ma_path[smooth_idx % len(path)][1]

            mag = math.sqrt(dr_sum ** 2 + dc_sum ** 2)

            grad_window_size += 1

        r_unit, c_unit = dr_sum / mag, dc_sum / mag

        r_norm = c_unit
        c_norm = -1 * r_unit

        distance, det = get_junction_width(image_processed, path[path_idx],
                                           (r_norm, c_norm), filter_threshold)

        distance_2, det_2 = get_junction_width(image_processed, path[path_idx],
                                       (r_norm, c_norm), 2)
        distance_4, det_4 = get_junction_width(image_processed, path[path_idx],
                                        (r_norm, c_norm), 4)
        distance_8, det_8 = get_junction_width(image_processed, path[path_idx],
                                        (r_norm, c_norm), 8)
        distance_16, det_16 = get_junction_width(image_processed, path[path_idx],
                                        (r_norm, c_norm), 16)

        distance_32, det_32 = get_junction_width(image_processed,
                                                   path[path_idx],
                                                   (r_norm, c_norm), 32)

        if last_r_unit is not None:
            entropy = math.sqrt((last_r_unit - r_unit)**2 +
                                (last_c_unit - c_unit)**2)
        else:
            entropy = 0
        last_r_unit, last_c_unit = r_unit, c_unit


        junction_path_data.append({
            "r": path[path_idx][0],
            "c": path[path_idx][1],
            "point_intensity": int(
                image_processed[path[path_idx][0], path[path_idx][1]]),

            "norm_vec_r": r_norm,
            "norm_vec_c": c_norm,

            "filter_threshold": filter_threshold,
            "width_threshold": distance,
            "junction_average_intensity": det[0],
            "parametric_point_1": str(det[1]),
            "parametric_point_2": str(det[2]),

            "width_threshold_2": distance_2,
            "junction_average_intensity_2": det_2[0],
            "parametric_point_1_2": str(det_2[1]),
            "parametric_point_2_2": str(det_2[2]),

            "width_threshold_4": distance_4,
            "junction_average_intensity_4":  det_4[0],
            "parametric_point_1_4": str(det_4[1]),
            "parametric_point_2_4": str(det_4[2]),

            "width_threshold_8": distance_8,
            "junction_average_intensity_8":  det_8[0],
            "parametric_point_1_8": str(det_8[1]),
            "parametric_point_2_8": str(det_8[2]),

            "width_threshold_16": distance_16,
            "junction_average_intensity_16":  det_16[0],
            "parametric_point_1_16": str(det_16[1]),
            "parametric_point_2_16": str(det_16[2]),

            "width_threshold_32": distance_32,
            "junction_average_intensity_32":  det_32[0],
            "parametric_point_1_32": str(det_32[1]),
            "parametric_point_2_32": str(det_32[2]),

            "nn_entropy": entropy
        })

    return junction_path_data