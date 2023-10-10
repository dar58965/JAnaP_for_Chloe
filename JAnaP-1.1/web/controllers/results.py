import os
import datetime
import csv
import json
import dateutil.parser

from controllers import app
from controllers import configuration

from controllers.shared import get_project

from flask import render_template
from flask import session
from flask import request
from flask import redirect
from flask import jsonify
from flask import g
from flask import send_file

@app.route("/projects/<project_hash>/results/generate/<output_type>",
           methods=['GET', 'POST'])
def generate_data_file(project_hash, output_type):
    project = get_project(project_hash)

    entity_map = project.get_chain().get_entity_map()

    output_directory = project.get_output_directory()

    with open(os.path.join(output_directory, "do-" + output_type), "w") as f:
        f.write(".")

    return redirect("/projects/" + project_hash + "/results")


@app.route("/projects/<project_hash>/results/download/<output_type>/<filename>",
           methods=['GET', 'POST'])
def download_data_file(project_hash, output_type, filename):
    project = get_project(project_hash)

    entity_map = project.get_chain().get_entity_map()

    output_directory = project.get_output_directory(output_type)

    output_file = os.path.join(output_directory, filename)

    return send_file(output_file, as_attachment=True)






@app.route("/projects/<project_hash>/results/junction-perimeter-data-file-filtered", methods=['GET', 'POST'])
def generate_perimeter_detail_data_file_filtered(project_hash):
    project = get_project(project_hash)

    entity_map = project.get_chain().get_entity_map()

    output_directory = project.get_output_directory("cell-data")
    output_file_key = ("path_data_filtered_export-%s.csv" %
                       str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))

    output_file = os.path.join(output_directory, output_file_key)

    variant = project.get_variant()
    dimensions = project.get_dimensions()
    dimension_ordered_keys = dimensions.keys()

    output_rows = []

    output_row = ["File Name"]

    if variant.get("name") is not None:
        output_row.append(variant.get("name"))

    for dimension_name in dimension_ordered_keys:
        output_row.append(dimension_name)

    output_row.extend(["Cell Id"])

    output_row.extend(["r", "c", "Point Intensity"])

    output_row.extend(["norm_vec_r", "norm_vec_c"])

    output_row.extend(["filter_threshold"])

    output_row.extend(["width_threshold", "junction_average_intensity",
                       "parametric_point_1", "parametric_point_2"])

    output_row.extend(["nn_entropy"])

    output_rows.append(output_row)

    artifact_j_detail_directory = project.get_artifacts_directory("junction-detail")


    for entity_map_row in entity_map:
        detail_file_key = entity_map_row["cell_id"] + ".json"
        detail_file = os.path.join(artifact_j_detail_directory, detail_file_key)

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

            #output_row.extend([entity_map_row["cell_id"],
            #                   entity_map_row["cell_number"], ])

            output_row.extend([detail_row.get("r", ""),
                               detail_row.get("c", "")])

            output_row.extend([detail_row.get("point_intensity", "")])

            output_row.extend([detail_row.get("norm_vec_r", ""),
                               detail_row.get("norm_vec_c", "")])

            output_row.extend([detail_row.get("filter_threshold", "")])

            output_row.extend([detail_row.get("width_threshold", ""),
                               detail_row.get("junction_average_intensity", ""),
                               detail_row.get("parametric_point_1", ""),
                               detail_row.get("parametric_point_2", "")])

            output_row.extend([detail_row.get("nn_entropy", "")])

            output_rows.append(output_row)

    with open(output_file, 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        for output_row in output_rows:
            csv_writer.writerow(output_row)

    return send_file(output_file, as_attachment=True)





@app.route("/projects/<project_hash>/results/cell-data-file", methods=['GET', 'POST'])
def generateCellDataFile(project_hash):
    project = get_project(project_hash)

    entity_map = project.get_chain().get_entity_map()

    output_directory = project.get_output_directory("cell-data")
    output_file_key = ("cell_data_export-%s.csv" %
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

    output_row.extend(["Image Mean Intensity",
                       "Image Max Intensity",
                       "Image Min Intensity"])

    output_row.extend(["Perimeter (Count)",
                       "Perimeter (Calc)",
                       "Perimeter (um)"])

    output_row.extend(["Area", "Area (um^2)"])

    output_row.extend(["Solidity",
                       "Circularity",
                       "Convex Area",
                       "Aspect Ratio"])

    output_row.extend(["Perim. Mean Intensity",
                       "Perim. Max Intensity",
                       "Perim. Min Intensity"])

    output_row.extend(["Coverage (%)",
                       "Linear (%)",
                       "Punct (%)",
                       "Perp (%)",
                       "Punct. + Perp (%)"])

    output_row.extend(["Hull Aspect Ratio (a/b)",
                       "Hull Aspect Ratio (< 1)"])

    output_rows.append(output_row)

    shapes_artifact_directory = project.get_artifacts_directory("shape-factors")
    image_data_artifact_directory = \
        project.get_artifacts_directory("image-data")
    hullar_artifact_directory = project.get_artifacts_directory("hull-ar")

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
            output_row.extend([image_data.get("mean_intensity", ""),
                               image_data.get("max_intensity", ""),
                               image_data.get("min_intensity", "")])
        else:
            # Image Data (w, h)
            output_row.extend(["", ""])
            # Image Data (Intensity)
            output_row.extend(["", "", ""])

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
                               shape_data.get("aspect_ratio", "")])
        else:
            # Perimeter
            output_row.extend(["", "", ""])
            # Area
            output_row.extend(["", ""])
            # Others
            output_row.extend(["", "", "", ""])

        # Perimeter Intensity Data
        output_row.extend(["", "", ""])
        
        classify_artifact_directory = project.get_artifacts_directory("class-edge")
        classify_file_key = entity_map_row["cell_id"] + ".json"
        classify_file = os.path.join(classify_artifact_directory, classify_file_key)
        if os.path.isfile(classify_file):
            with open(classify_file, "r") as f:
                classify_data = json.load(f)

            output_row.extend([classify_data.get("percent_coverage", ""),
                               classify_data.get("percent_linear", ""),
                               classify_data.get("percent_punctate", ""),
                               classify_data.get("percent_perpendicular", ""),
                               classify_data.get("percent_punct_perp", "")])
        else:
            output_row.extend(["", "", "", "", ""])

        ## Shape Factors - Hull AR
        shape_file_key = entity_map_row["cell_id"] + ".json"
        hullar_file = os.path.join(hullar_artifact_directory,
                                   shape_file_key)
        if os.path.isfile(hullar_file):
            with open(hullar_file, "r") as f:
                hullar_data = json.load(f)

            output_row.extend([hullar_data.get("hull_aspect_ratio_ab", ""),
                               hullar_data.get("hull_aspect_ratio", "")])
        else:
            output_row.extend(["", ""])


        output_rows.append(output_row)



    with open(output_file, 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        for output_row in output_rows:
            csv_writer.writerow(output_row)

    #output_rows.append([
    #    "Cell Id",
    #    "File Name",
    #    "Max Perim. Intensity",
    #    "Min Perim. Intensity",
    #    "Avg Perim. Intensity",
    #    "Sttdev Perim. Intensity",
    #    "Threshold",
    #    "Goodness",
    #    "Coverage (%)",
    #    "Linear (%)",
    #    "Punct. + Perp. (%)"
    #])
    return send_file(output_file, as_attachment=True)
    # return Response(output_file, mimetype='text/csv')


@app.route("/projects/<project_hash>/results")
def getResultsIndex(project_hash):

    project = get_project(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project.get_project_name()
    }

    page_data = {
        "title": "",
        "active_nav_tab": "index"
    }

    output_directory = project.get_output_directory()

    output_dto = {
        # "cell-data": {"status": 0},
        #"feature-data": {"status": 0, "files": []},
        #"feature-data-filtered": {"status": 0, "files": []},
        #"path-data": {"status": 0, "files": []},
        #"path-data-filtered": {"status": 0, "files": []},
        "cell-data-v2": {"status": 0, "files": []},
        #"fastclass-data": {"status": 0, "files": []},
	    "fastclass-feature-data-filtered": {"status": 0, "files": []},
        #"fastclass-feature-data": {"status": 0, "files": []},
    }

    for output_entry_name in os.listdir(output_directory):
        for output_key in output_dto.keys():
            if output_entry_name == "do-" + output_key:
                output_dto[output_key]["status"] = 2
            elif output_entry_name == "do-" + output_key + ".lock":
                output_dto[output_key]["status"] = 1

    for output_key in output_dto.keys():
        output_inner_directory = project.get_output_directory(output_key)
        if os.path.isdir(output_inner_directory):
            gen_dates = []
            for filename in os.listdir(output_inner_directory):
                file_parts = filename.split("-")

                if file_parts[0] not in gen_dates and "." not in file_parts[0]:
                    gen_dates.append(file_parts[0])

            if len(gen_dates) > 0:
                latest = sorted(gen_dates)[-1]

                for filename in os.listdir(output_inner_directory):
                    file_parts = filename.split("-")

                    if file_parts[0] == latest:
                        output_dto[output_key]["files"].append(filename)

                output_dto[output_key]["files"].sort()


    return render_template('results/index.html', project=project_dto,
                           page_data=page_data, output=output_dto)
