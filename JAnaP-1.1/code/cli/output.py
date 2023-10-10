import datetime
import os
import csv
import json

import cv2

from skimage.morphology import disk, white_tophat

import cells.images
import cells.images.filter
import cells.shapes

from cells.edge import classify, segments, junctions

def __get_summary_statistics(summary_data_directory, entity_map_row):
    summary_file_key = entity_map_row["cell_id"] + ".json"
    summary_file = os.path.join(summary_data_directory, summary_file_key)

    print "summary file"
    if os.path.isfile(summary_file):
        print "summary file opened"
        with open(summary_file, "r") as f:
            summary_data = json.load(f)
    else:
        return ["", "", "", "", ""]

    coverage_percent = summary_data["coverage_percent"]
    continuous_percent = summary_data["continuous_percent"]
    punct_percent = summary_data["punct_percent"]
    perp_percent = summary_data["perp_percent"]
    discontinuous_percent = summary_data["discontinuous_percent"]
    
    return [coverage_percent, continuous_percent, punct_percent, perp_percent, discontinuous_percent]

def generate_cell_data_file(project):
    entity_map = project.get_chain().get_entity_map()

    output_directory = project.get_output_directory("cell-data-v2")    

    output_file_key = ("cell_data_v2_export-%s.csv" %
                       str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))

    output_file = os.path.join(output_directory, output_file_key)

    variant = project.get_variant()
    dimensions = project.get_dimensions()
    dimension_ordered_keys = dimensions.keys()

    output_rows = []

    output_row = ["File Name", "File Root"]

    if variant.get("name") is not None:
        output_row.append(variant.get("name"))

    for dimension_name in dimension_ordered_keys:
        output_row.append(dimension_name)

    output_row.extend(["Cell Id", "Cell Number",])

    output_row.extend(["Image Width", "Image Height"])

    #output_row.extend(["Image Mean Intensity",
    #                   "Image Max Intensity",
    #                   "Image Min Intensity"])

    output_row.extend(["Perimeter (Count)",
                       "Perimeter (Calc)",
                       "Perimeter (um)"])

    output_row.extend(["Area", "Area (um^2)"])

    output_row.extend(["Solidity",
                       "Circularity",
                       "Convex Area"])
    #                   "Convex Area",
    #                   "Aspect Ratio"])

    #output_row.extend(["Perim. Mean Intensity",
    #                   "Perim. Max Intensity",
    #                   "Perim. Min Intensity"])

    #output_row.extend(["Coverage (%)",
    #                   "Continuous (%)",
    #                   "Punct (%)",
    #                   "Perp (%)",
    #                   "Discontinuous (%)"])

    #output_row.extend(["Hull Aspect Ratio (a/b)",
    #                   "Hull Aspect Ratio (< 1)"])

    output_row.extend(["Hull Aspect Ratio (< 1)"])
    output_row.extend(["Angle of Major Axis wrt X-Axis (degrees)"])



    output_row.extend(["Coverage (%)",
                       "Continuous (%)",
                       "Punct (%)",
                       "Perp (%)",
                       "Discontinuous (%)"])


    output_rows.append(output_row)

    shapes_artifact_directory = project.get_artifacts_directory("shape-factors")
    image_data_artifact_directory = \
        project.get_artifacts_directory("image-data")
    hullar_artifact_directory = project.get_artifacts_directory("hull-ar")

    perimeter_data_directory = project.get_artifacts_directory("perimeters")
    artifact_data_directory = project.get_artifacts_directory("junction-class")
    summary_data_directory = project.get_artifacts_directory("fastclass-sum")

    for entity_map_row in entity_map:
        
        output_row = [entity_map_row["file_name"],
                      entity_map_row["file_root"]]

        if variant.get("name") is not None:
            output_row.append(entity_map_row.get("variant"))

        for dimension_name in dimension_ordered_keys:
            output_row.append(
                entity_map_row.get("dimensions", {}).get(dimension_name, ""))

        output_row.extend([entity_map_row["cell_id"],
                           entity_map_row["cell_number"],])

        image_data_key = entity_map_row["file_name"] + ".json"
        image_data_file = os.path.join(image_data_artifact_directory,
                                       image_data_key)


        if os.path.isfile(image_data_file):
            with open(image_data_file, "r") as f:
                image_data = json.load(f)

            # Image Data (w, h)
            output_row.extend([image_data.get("width", ""),
                               image_data.get("height", "")])
            # Image Data (Intensity)
            #output_row.extend([image_data.get("mean_intensity", ""),
            #                   image_data.get("max_intensity", ""),
            #                   image_data.get("min_intensity", "")])
        else:
            # Image Data (w, h)
            output_row.extend(["", ""])
            # Image Data (Intensity)
            # output_row.extend(["", "", ""])

        ## Shape Factors
        shape_file_key = entity_map_row["cell_id"] + ".json"
        shapes_file = os.path.join(shapes_artifact_directory, shape_file_key)

        if os.path.isfile(shapes_file):
            with open(shapes_file, "r") as f:
                shape_data = json.load(f)
            # Perimeter
            output_row.extend([shape_data.get("perimeter_pixels", ""),
                               shape_data.get("perimeter_measured", ""),
                               shape_data.get("perimeter_um", "")])
            # Area
            output_row.extend([shape_data.get("area_measured", ""),
                               shape_data.get("area_um", "")])
            # Others
            output_row.extend([shape_data.get("solidity", ""),
                               shape_data.get("circularity", ""),
                               shape_data.get("convex_area", ""),
                               shape_data.get("hull_aspect_ratio", ""), 
                               shape_data.get("angle", "")])
                               #shape_data.get("aspect_ratio", "")])
        else:
            # Perimeter
            output_row.extend(["", "", ""])
            # Area
            output_row.extend(["", ""])
            # Others
            output_row.extend(["", "", "", ""])
        
        # V2 Fix
        ore = __get_summary_statistics(summary_data_directory, entity_map_row)
        
        output_row.extend(ore)
        
        output_rows.append(output_row)

        print (float(len(output_rows)) / float(len(entity_map)) * 100.0)


    with open(output_file, 'w') as csv_file:
        csv_writer = csv.writer(csv_file, lineterminator="\n")
        for output_row in output_rows:
            csv_writer.writerow(output_row)

def generate_feature_data_file_fastclass(project, filtered=True):
    entity_map = project.get_chain().get_entity_map()
    
    if filtered:
        output_directory = project.get_output_directory("fastclass-feature-data-filtered")
    else:
        output_directory = project.get_output_directory("fastclass-feature-data")

    output_file_prefix = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    
    variant = project.get_variant()
    if variant.get("name") is not None:
        variants = variant.get("values", ["All"])
    else:
        variants = ["All"]

    if len(variants) == 0:
        variants = ["All"]

    dimensions = project.get_dimensions()
    dimension_ordered_keys = dimensions.keys()

    output_header_row = ["File Name"]

    if variant.get("name") is not None:
        output_header_row.append(variant.get("name"))

    for dimension_name in dimension_ordered_keys:
        output_header_row.append(dimension_name)

    output_header_row.extend(["Cell Id"])
    # output_header_row.extend(["Feature Index"])
    # output_header_row.extend(["Param: Min Cont. Path Thres", "Param: Perp. AR Thres"])
    output_header_row.extend(["Path Start Index", "Path End Index"])
    output_header_row.extend(["Segment Length (px)", "Path AR Length"])
    output_header_row.extend(["Abs Tip Distance", "Relative Path AR"])
    output_header_row.extend(["Classification", "Classification Simple"])
    
    
    fc_detail_artifact_directory = project.get_artifacts_directory("fastclass-detail")
    
    for variant_value in variants:
        file_no = 100

        output_rows = []
        output_rows.append(output_header_row)
        
        for entity_map_row in entity_map:
            
            if variant_value != "All" and \
               entity_map_row.get("variant") != variant_value:
                continue

            detail_file_key = entity_map_row["cell_id"] + ".json"
            detail_file = os.path.join(fc_detail_artifact_directory, detail_file_key)

            if os.path.isfile(detail_file):
                with open(detail_file, "r") as f:
                    detail_data = json.load(f)
            else:
                continue

            for detail_row in detail_data:
                if filtered and detail_row.get("classification") is None:
                    continue

                output_row = [entity_map_row["file_name"]]

                if variant.get("name") is not None:
                    output_row.append(entity_map_row.get("variant"))

                for dimension_name in dimension_ordered_keys:
                    output_row.append(
                        entity_map_row.get("dimensions", {}).get(dimension_name,
                                                                 ""))

                output_row.extend([entity_map_row["cell_id"]])

                # output_row.extend([detail_row.get("feature_idx", "")])

                # output_row.extend([detail_row.get("param_continuous_min_path_length", "")])
                # output_row.extend([detail_row.get("param_perpendicular_aspect_ratio_threshold", "")])

                output_row.extend([detail_row.get("path_start_idx", "")])
                output_row.extend([detail_row.get("path_end_idx", "")])

                output_row.extend([detail_row.get("segment_length_px", "")])
                output_row.extend([detail_row.get("path_ar_length", "")])

                output_row.extend([detail_row.get("t_dist_abs", "")])
                output_row.extend([detail_row.get("relative_path_aspect_ratio", "")])

                output_row.extend([detail_row.get("classification", "")])
                output_row.extend([detail_row.get("classification_simple", "")])

                output_rows.append(output_row)

            if len(output_rows) > 800000:
                output_file_key = ("%s-%s-%s.csv" %
                                   (output_file_prefix, variant_value,
                                    str(file_no)))

                output_file = os.path.join(output_directory, output_file_key)

                with open(output_file, 'w') as csv_file:
                    csv_writer = csv.writer(csv_file, lineterminator="\n")
                    for output_row in output_rows:
                        csv_writer.writerow(output_row)

                file_no += 1
                output_rows = []
                output_rows.append(output_header_row)

        if len(output_rows) > 0:
            output_file_key = ("%s-%s-%s.csv" %
                               (output_file_prefix, variant_value,
                                str(file_no)))

            output_file = os.path.join(output_directory, output_file_key)

            with open(output_file, 'w') as csv_file:
                csv_writer = csv.writer(csv_file, lineterminator="\n")
                for output_row in output_rows:
                    csv_writer.writerow(output_row)

            file_no += 1
            output_rows = []
            output_rows.append(output_header_row)
                
            
    
    
def generate_feature_data_file(project, filtered=False):
    entity_map = project.get_chain().get_entity_map()

    if filtered:
        output_directory = project.get_output_directory("feature-data-filtered")
    else:
        output_directory = project.get_output_directory("feature-data")

    output_file_prefix = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    variant = project.get_variant()
    if variant.get("name") is not None:
        variants = variant.get("values", ["All"])
    else:
        variants = ["All"]

    if len(variants) == 0:
        variants = ["All"]

    dimensions = project.get_dimensions()
    dimension_ordered_keys = dimensions.keys()

    output_header_row = ["File Name"]

    if variant.get("name") is not None:
        output_header_row.append(variant.get("name"))

    for dimension_name in dimension_ordered_keys:
        output_header_row.append(dimension_name)

    output_header_row.extend(["Cell Id"])

    # output_header_row.extend(["Feature Index", "Intersects Path"])
    output_header_row.extend(["Intersects Path"])

    output_header_row.extend(["pixel_area", "feature_perimeter"])
    
    output_header_row.extend(["center_of_mass", "center_of_mass"])
    
    # All SLMP remove
    output_header_row.extend(["path_ar_length", "slmp_ar_length", "ma_ar_length"])

    output_header_row.extend(["path_abs_max", "ma_abs_max", "slmp_abs_max"])
    output_header_row.extend(["path_abs_avg", "ma_abs_avg", "slmp_abs_avg"])
    output_header_row.extend(["ma_sum", "slmp_sum"])
    output_header_row.extend(["ma_sum_square", "slmp_sum_square"])
    output_header_row.extend(["ma_avg_square", "slmp_avg_square"])
    output_header_row.extend(["tip_dist_abs_ma", "tip_dist_abs_slmp"])
    output_header_row.extend(
        ["absolute_path_aspect_ratio", "relative_path_aspect_ratio",
         "normal_distance"])

    output_header_row.extend(["classification", "classification_simple"])

    artifact_data_directory = project.get_artifacts_directory("junction-class")

    for variant_value in variants:
        file_no = 100

        output_rows = []
        output_rows.append(output_header_row)

        for entity_map_row in entity_map:
            if variant_value != "All" and \
                            entity_map_row.get("variant") != variant_value:
                continue

            detail_file_key = entity_map_row["cell_id"] + ".json"
            detail_file = os.path.join(artifact_data_directory, detail_file_key)

            if os.path.isfile(detail_file):
                with open(detail_file, "r") as f:
                    detail_data = json.load(f)
            else:
                continue

            for detail_row in detail_data:
                if filtered and detail_row.get("classification") is None:
                    continue

                output_row = [entity_map_row["file_name"]]

                if variant.get("name") is not None:
                    output_row.append(entity_map_row.get("variant"))

                for dimension_name in dimension_ordered_keys:
                    output_row.append(
                        entity_map_row.get("dimensions", {}).get(dimension_name,
                                                                 ""))

                output_row.extend([entity_map_row["cell_id"]])

                # output_row.extend([detail_row.get("feature_idx", "")])
                output_row.extend([detail_row.get("intersects_path", "")])

                output_row.extend([detail_row.get("feature_pixel_area", "")])
                output_row.extend([detail_row.get("feature_perimeter", "")])

                output_row.extend([detail_row.get("center_of_mass", "")])
                output_row.extend([detail_row.get("com_path_distance", "")])

                output_row.extend([detail_row.get("path_ar_length", "")])
                output_row.extend([detail_row.get("slmp_ar_length", "")])
                output_row.extend([detail_row.get("slmp_abs_max", "")])

                output_row.extend([detail_row.get("path_abs_max", "")])
                output_row.extend([detail_row.get("ma_abs_max", "")])
                output_row.extend([detail_row.get("ma_ar_length", "")])

                output_row.extend([detail_row.get("path_abs_avg", "")])
                output_row.extend([detail_row.get("ma_abs_avg", "")])
                output_row.extend([detail_row.get("slmp_abs_avg", "")])

                output_row.extend([detail_row.get("ma_sum", "")])
                output_row.extend([detail_row.get("slmp_sum", "")])

                output_row.extend([detail_row.get("ma_sum_square", "")])
                output_row.extend([detail_row.get("slmp_sum_square", "")])

                output_row.extend([detail_row.get("ma_avg_square", "")])
                output_row.extend([detail_row.get("slmp_avg_square", "")])

                output_row.extend([detail_row.get("tip_dist_abs_ma", "")])
                output_row.extend([detail_row.get("tip_dist_abs_slmp", "")])

                output_row.extend(
                    [detail_row.get("absolute_path_aspect_ratio", "")])
                output_row.extend(
                    [detail_row.get("relative_path_aspect_ratio", "")])
                output_row.extend([detail_row.get("normal_distance", "")])

                output_row.extend([detail_row.get("classification", "")])
                output_row.extend([detail_row.get("classification_simple", "")])

                output_rows.append(output_row)

            if len(output_rows) > 800000:
                output_file_key = ("%s-%s-%s.csv" %
                                   (output_file_prefix, variant_value,
                                    str(file_no)))

                output_file = os.path.join(output_directory, output_file_key)

                with open(output_file, 'w') as csv_file:
                    csv_writer = csv.writer(csv_file, lineterminator="\n")
                    for output_row in output_rows:
                        csv_writer.writerow(output_row)

                file_no += 1
                output_rows = []
                output_rows.append(output_header_row)

        if len(output_rows) > 0:
            output_file_key = ("%s-%s-%s.csv" %
                               (output_file_prefix, variant_value,
                                str(file_no)))

            output_file = os.path.join(output_directory, output_file_key)

            with open(output_file, 'w') as csv_file:
                csv_writer = csv.writer(csv_file, lineterminator="\n")
                for output_row in output_rows:
                    csv_writer.writerow(output_row)

            file_no += 1
            output_rows = []
            output_rows.append(output_header_row)


def generate_path_data_file(project, filtered=False):
    entity_map = project.get_chain().get_entity_map()

    if filtered:
        output_directory = project.get_output_directory("path-data-filtered")
    else:
        output_directory = project.get_output_directory("path-data")

    output_file_prefix = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    variant = project.get_variant()
    if variant.get("name") is not None:
        variants = variant.get("values", ["All"])
    else:
        variants = ["All"]

    if len(variants) == 0:
        variants = ["All"]

    dimensions = project.get_dimensions()
    dimension_ordered_keys = dimensions.keys()

    output_header_row = ["File Name"]

    if variant.get("name") is not None:
        output_header_row.append(variant.get("name"))

    for dimension_name in dimension_ordered_keys:
        output_header_row.append(dimension_name)

    output_header_row.extend(["Cell Id"])

    output_header_row.extend(["r", "c", "Point Intensity"])

    output_header_row.extend(["norm_vec_r", "norm_vec_c"])

    output_header_row.extend(["filter_threshold"])

    output_header_row.extend(["width_threshold", "junction_average_intensity",
                       "parametric_point_1", "parametric_point_2"])

    if not filtered:
        output_header_row.extend(
            ["width_threshold, t=2", "junction_average_intensity, t=2",
             "parametric_point_1, t=2", "parametric_point_2, t=2"])

        output_header_row.extend(
            ["width_threshold, t=4", "junction_average_intensity, t=4",
             "parametric_point_1, t=4", "parametric_point_2, t=4"])

        output_header_row.extend(
            ["width_threshold, t=8", "junction_average_intensity, t=8",
             "parametric_point_1, t=8", "parametric_point_2, t=8"])

        output_header_row.extend(
            ["width_threshold, t=16", "junction_average_intensity, t=16",
             "parametric_point_1, t=16", "parametric_point_2, t=16"])

        output_header_row.extend(
            ["width_threshold, t=32", "junction_average_intensity, t=32",
             "parametric_point_1, t=32", "parametric_point_2, t=32"])

    output_header_row.extend(["nn_entropy"])

    artifact_data_directory = project.get_artifacts_directory("junction-detail")

    for variant_value in variants:
        file_no = 100

        output_rows = []
        output_rows.append(output_header_row)

        for entity_map_row in entity_map:
            if variant_value != "All" and \
                            entity_map_row.get("variant") != variant_value:
                continue

            detail_file_key = entity_map_row["cell_id"] + ".json"
            detail_file = os.path.join(artifact_data_directory, detail_file_key)

            if os.path.isfile(detail_file):
                with open(detail_file, "r") as f:
                    detail_data = json.load(f)
            else:
                continue

            for detail_row in detail_data:
                output_row = [entity_map_row["file_name"]]

                if variant.get("name") is not None:
                    output_row.append(entity_map_row.get("variant"))

                for dimension_name in dimension_ordered_keys:
                    output_row.append(
                        entity_map_row.get("dimensions", {}).get(dimension_name,
                                                                 ""))

                output_row.extend([entity_map_row["cell_id"]])

                # output_row.extend([entity_map_row["cell_id"],
                #                   entity_map_row["cell_number"], ])

                output_row.extend([detail_row.get("r", ""),
                                   detail_row.get("c", "")])

                output_row.extend([detail_row.get("point_intensity", "")])

                output_row.extend([detail_row.get("norm_vec_r", ""),
                                   detail_row.get("norm_vec_c", "")])

                output_row.extend([detail_row.get("filter_threshold", "")])

                output_row.extend([detail_row.get("width_threshold", ""),
                                   detail_row.get("junction_average_intensity",
                                                  ""),
                                   detail_row.get("parametric_point_1", ""),
                                   detail_row.get("parametric_point_2", "")])
                if not filtered:
                    output_row.extend([detail_row.get("width_threshold_2", ""),
                                       detail_row.get(
                                           "junction_average_intensity_2", ""),
                                       detail_row.get("parametric_point_1_2", ""),
                                       detail_row.get("parametric_point_2_2", "")])

                    output_row.extend([detail_row.get("width_threshold_4", ""),
                                       detail_row.get(
                                           "junction_average_intensity_4", ""),
                                       detail_row.get("parametric_point_1_4", ""),
                                       detail_row.get("parametric_point_2_4", "")])

                    output_row.extend([detail_row.get("width_threshold_8", ""),
                                       detail_row.get(
                                           "junction_average_intensity_8", ""),
                                       detail_row.get("parametric_point_1_8", ""),
                                       detail_row.get("parametric_point_2_8", "")])

                    output_row.extend([detail_row.get("width_threshold_16", ""),
                                       detail_row.get(
                                           "junction_average_intensity_16", ""),
                                       detail_row.get("parametric_point_1_16", ""),
                                       detail_row.get("parametric_point_2_16", "")])

                    output_row.extend([detail_row.get("width_threshold_32", ""),
                                       detail_row.get(
                                           "junction_average_intensity_32", ""),
                                       detail_row.get("parametric_point_1_32", ""),
                                       detail_row.get("parametric_point_2_32", "")])

                output_row.extend([detail_row.get("nn_entropy", "")])

                output_rows.append(output_row)

            if len(output_rows) > 800000:
                output_file_key = ("%s-%s-%s.csv" %
                                   (output_file_prefix, variant_value,
                                    str(file_no)))

                output_file = os.path.join(output_directory,
                                           output_file_key)

                with open(output_file, 'w') as csv_file:
                    csv_writer = csv.writer(csv_file, lineterminator="\n")
                    for output_row in output_rows:
                        csv_writer.writerow(output_row)

                file_no += 1
                output_rows = []
                output_rows.append(output_header_row)

        if len(output_rows) > 0:
            output_file_key = ("%s-%s-%s.csv" %
                               (output_file_prefix, variant_value,
                                str(file_no)))

            output_file = os.path.join(output_directory, output_file_key)

            with open(output_file, 'w') as csv_file:
                csv_writer = csv.writer(csv_file, lineterminator="\n")
                for output_row in output_rows:
                    csv_writer.writerow(output_row)

            file_no += 1
            output_rows = []
            output_rows.append(output_header_row)
