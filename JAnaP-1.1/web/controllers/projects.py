import os
import glob
import base64
import json
import time
import shutil
import string

from controllers import app
from controllers import configuration

from controllers.shared import get_project, get_waypoint_tasks, get_project_name

from flask import render_template
from flask import session
from flask import request
from flask import redirect
from flask import jsonify
from flask import make_response


@app.route("/projects")
def getProjects():
    projects = []

    projects_root = configuration.NodeConfiguration.Paths.projects_root
    
    for project_directory_name in os.listdir(projects_root):
        if not os.path.isdir(os.path.join(projects_root, project_directory_name)):
            continue

        hash = project_directory_name
        project_name = get_project_name(hash)
        
        projects.append({
            "hash": hash,
            "name": project_name
        })

    return render_template('projects/list.html', projects=projects)


@app.route("/projects/new", methods=['GET', 'POST'])
def createProject():
    import cli.project

    form_errors = {}
    form_values = {}

    if request.method == 'POST':
        is_valid = True

        project_name = request.form.get("project_name")
        
        valid_characters = string.letters + string.digits + " -_"

        project_name = project_name.strip()
        
        if len(project_name) == 0:
            form_errors["project_name"] = "Project name is required"

        contains_invalid_characters = False

        for char in project_name:
            if char not in valid_characters:
                contains_invalid_characters = True
                is_valid = False
                break

        if contains_invalid_characters:
            form_errors["project_name"] = \
                "Project name contains invalid character(s): Must only " + \
                "contain the following characters: " + valid_characters
        
        project_hash = project_name.replace(" ", "_")
        project_hash = project_hash.lower()

        invalid_project_names = ["new", "hash", "temp"]

        if project_hash in invalid_project_names:
            form_errors["project_name"] = \
                "Project name is reserved, choose a different name"
            is_valid = False
            
        projects_root = configuration.NodeConfiguration.Paths.projects_root

        project_path = os.path.join(projects_root, project_hash)

        if os.path.exists(project_path):
            form_errors["project_name"] = \
                "Project name is already in use, must be unique"
            is_valid = False


        if is_valid:
            projects_root = configuration.NodeConfiguration.Paths.projects_root
            project_directory = os.path.join(projects_root, project_hash)

            # Create project
            project = cli.project.Project.create(project_directory, project_name)

            return redirect("/projects/" + project.get_project_hash())




    return render_template('projects/create.html', form_values=form_values, form_errors=form_errors)

#@app.route("/projects/new", methods=['POST'])
#def postCreate():
#    
#    pass

@app.route("/projects/<project_hash>")
def getProject(project_hash):
    import cells.images
    import cli.operations

    project = get_project(project_hash)

    project_name = get_project_name(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project_name
    }

    input_image_directory = project.get_input_image_directory()

    variant = project.get_variant()
    dimensions = project.get_dimensions()
    
    image_data = cells.images.get_image_collection(input_image_directory, variant, dimensions)

    # Get input image count
    total_images = 0
    stain_image_counts = {}

    for image_data_row in image_data:
        file_name = image_data_row["file_name"]

        image_stain = None
        for test_stain in variant.get("values", []):
            if test_stain in file_name:
                stain_image_counts[test_stain] = stain_image_counts.get(test_stain, 0) + 1
                image_stain = test_stain
                break
        
        if image_stain is None:
            stain_image_counts["None"] = stain_image_counts.get("None", 0) + 1

        total_images = total_images + 1
    
    # Task Data 
    waypoint_tasks, waypoint_tasks_data = get_waypoint_tasks(project)

    # Cell Data
    cell_collection = cli.operations.get_cell_collection(project, image_data)

    project_data_dto = {
        "image_count": total_images,
        "variant_data": stain_image_counts,
        "task_data": waypoint_tasks_data,
        "cell_count": len(cell_collection)
    }

    print project.get_project_hash()

    return render_template('projects/overview.html', project=project_dto, project_data=project_data_dto)


@app.route("/projects/<project_hash>/<width>x<height>/<image_name>.png")
def getSizedImage(project_hash, width, height, image_name):
    import cv2
    width, height = int(width), int(height)
    project = get_project(project_hash)
    input_image_directory = project.get_input_image_directory()

    image_path = os.path.join(input_image_directory, image_name)
    input_image = cv2.imread(image_path)

    resized_image = cv2.resize(input_image, (width, height))

    retval, buffer = cv2.imencode('.png', resized_image)

    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/png'

    return response


@app.route("/projects/<project_hash>/data")
def getProjectDataSummary(project_hash):
    import cells.images
    import cli.operations

    project = get_project(project_hash)

    project_name = get_project_name(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project_name
    }

    input_image_directory = project.get_input_image_directory()

    variant = project.get_variant()

    dimensions = project.get_dimensions()
    
    image_data = cells.images.get_image_collection(input_image_directory, variant, dimensions)

    # Get input image count
    total_images = 0
    variant_counts = {}

    for image_data_row in image_data:
        file_name = image_data_row["file_name"]

        image_stain = None
        for test_stain in variant.get("values", []):
            if test_stain in file_name:
                variant_counts[test_stain] = variant_counts.get(test_stain, 0) + 1
                image_stain = test_stain
                break
        
        if image_stain is None:
            variant_counts["None"] = variant_counts.get("None", 0) + 1

        total_images = total_images + 1

    dimension_counts = {}

    for key, value in dimensions.iteritems():
        dimension_counts[key] = {}

    for image_data_row in image_data:
        for key in dimensions.keys():
            dimension_value = image_data_row.get("dimensions", {}).get(key)
            dimension_counts[key][dimension_value] = \
                dimension_counts[key].get(dimension_value, 0) + 1

    # Get counts for cells
    cell_collection = cli.operations.get_cell_collection(project, image_data)

    cell_variant_counts = {}
    for key in variant_counts.keys():
        cell_variant_counts[key] = 0

    cell_dimension_counts = {}
    for key, value in dimensions.iteritems():
        cell_dimension_counts[key] = {}

    for cell_data_row in cell_collection:
        variant_value = cell_data_row.get("variant")
        cell_variant_counts[variant_value] = cell_variant_counts.get(variant_value, 0) + 1

        for key in dimensions.keys():
            dimension_value = cell_data_row.get("dimensions", {}).get(key)
            cell_dimension_counts[key][dimension_value] = \
                cell_dimension_counts[key].get(dimension_value, 0) + 1


    variant_name = project.get_variant()["name"]

    project_data_dto = {
        "image_count": total_images,
        "variant_name": variant_name,
        "variant_data": variant_counts, 
        "cell_variant_data": cell_variant_counts,

        "dimension_counts": dimension_counts,
        "cell_dimension_counts": cell_dimension_counts
    }

    page_data = {
        "title": "",
        "active_nav_tab": "data"
    }

    return render_template('projects/data.html', project=project_dto, project_data=project_data_dto, page_data=page_data)




@app.route("/projects/<project_hash>/problems")
def getProjectProblems(project_hash):
    import cells.images

    project = get_project(project_hash)

    project_name = get_project_name(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project_name
    }

    problems = []

    input_image_directory = project.get_input_image_directory()

    variant = project.get_variant()
    dimensions = project.get_dimensions()
    
    if variant.get("name") is None or variant.get("name") == "":
        problems.append({
            "level": "info",
            "css": "info",
            "summary": "You have not configured a variant (stain) and values for this project"
        })

    image_data = cells.images.get_image_collection(input_image_directory, variant, dimensions)
    
    # TODO: A variant value is not found in any images
    stain_image_counts = {}

    missing_variant_images = []

    for image_data_row in image_data:
        file_name = image_data_row["file_name"]

        image_stain = None
        for test_stain in variant.get("values", []):
            if test_stain in file_name:
                stain_image_counts[test_stain] = stain_image_counts.get(test_stain, 0) + 1
                image_stain = test_stain
                break

        if image_stain is None:
            missing_variant_images.append(file_name)
    
    for variant_value in variant.get("values", []):
        if stain_image_counts.get(variant_value, 0) == 0:
            problems.append({
                "level": "warning",
                "css": "warning",
                "summary": "The variant/stain '%s' did not match any images." % variant_value
            })

    # Image has no variant
    for missing_variant_image in missing_variant_images:
        problems.append({
            "level": "warning",
            "css": "warning",
            "summary": "Image '%s' does not have a variant." % missing_variant_image
        })

    # Image has missing related variant image(s)
    for image_data_row in image_data:
        file_name = image_data_row["file_name"]

        image_stain = None
        for test_stain in variant.get("values", []):
            if test_stain in file_name:
                stain_image_counts[test_stain] = stain_image_counts.get(test_stain, 0) + 1
                image_stain = test_stain
                break

        missing_variants = []
        if image_stain is not None:
            for variant_value in variant.get("values", []):
                related_file_name = file_name.replace(image_stain, variant_value)
                related_file = os.path.join(input_image_directory, related_file_name)
                if not os.path.isfile(related_file):
                    missing_variants.append(variant_value)
            
        for missing_variant in missing_variants:
            if missing_variant == variant.get("primary_value"):
                problems.append({
                    "level": "error",
                    "css": "danger",
                    "summary": "Missing variant with value '%s' for image '%s'. No output will be generated for this file." % (missing_variant, file_name),
                })
            else:
                problems.append({
                    "level": "warning",
                    "css": "warning",
                    "summary": "Missing variant with value '%s' for image '%s'." % (missing_variant, file_name)
                })

    page_data = {
        "title": "",
        "active_nav_tab": "problems"
    }

    return render_template('projects/problems.html', project=project_dto, 
                           problems=problems, page_data=page_data)


@app.route("/projects/<project_hash>/config")
def getProjectConfiguration(project_hash):
    project = get_project(project_hash)

    project_name = get_project_name(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project_name
    }

    project_configuration_dto = {
        "variant": project.get_variant(),
        "dimensions": project.get_dimensions(),
        "parameters": project.get_parameters(),
        "dep": [
            {
                "name": "Experiment Date",
                "type": "function",
                "data": "parse_date"
            },
            {
                "name": "Experiment Name",
                "type": "mapping",
                "data": [
                    {"tokens": [], "value": ""},
                ]
            }
        ]
    }

    page_data = {
        "title": "",
        "active_nav_tab": "config"
    }

    return render_template('projects/config.html', project=project_dto,
                           configuration=project_configuration_dto,
                           page_data=page_data)


@app.route("/projects/<project_hash>/config/variant", methods=['POST'])
def postProjectConfigurationVariant(project_hash):
    project = get_project(project_hash)

    variant = project.get_variant()
    
    if request.form.get("action") == "save":
        
        if request.form.get("variant_name") != None:
            variant["name"] = request.form["variant_name"]
        
        if request.form.get("variant_primary") != None:
            variant["primary_value"] = request.form["variant_primary"]
        
    elif request.form.get("action") == "add":
        if request.form.get("variant_value") != None:
            if (len(request.form["variant_value"].strip()) > 0):
                variant["values"].append(request.form["variant_value"])

    elif request.form.get("action") == "delete":
        if request.form.get("variant_selected") != None:
            if (len(request.form["variant_selected"].strip()) > 0):
                variant["values"].remove(request.form["variant_selected"])

                if variant["primary_value"] == request.form["variant_selected"]: 
                    variant["primary_value"] = ""


    project.set_variant(variant)

    return redirect("/projects/" + project_hash + "/config")


def parse_numeric(s):
    t_num = float(s)
    try:
        t_num = float(s)
        return t_num
    except:
        return None

@app.route("/projects/<project_hash>/config/parameters", methods=['POST'])
def postProjectConfigurationParameters(project_hash):
    project = get_project(project_hash)

    parameters = project.get_parameters()

    if "add" in request.form.get("action"):
        parameter_key = request.form.get("action").replace("add-", "")

        value_map_name = request.form.get("map_name-" + parameter_key)
        value_map_value = request.form.get("map_value-" + parameter_key)

        parsed_map_value = parse_numeric(value_map_value)

        if parameter_key in parameters.keys() and \
            value_map_name != "" and parsed_map_value is not None:
            parameter_data = parameters[parameter_key]
            parameter_data["value_map"][value_map_name] = parsed_map_value

            project.save_parameter_data(parameter_key, parameter_data)
    elif "delete" in request.form.get("action"):
        parameter_key = request.form.get("action").split("---")[1]
        value_map_name = request.form.get("action").split("---")[2]

        if parameter_key in parameters.keys():
            parameter_data = parameters[parameter_key]
            del parameter_data["value_map"][value_map_name]

            project.save_parameter_data(parameter_key, parameter_data)
    # project.set_variant(variant)

    return redirect("/projects/" + project_hash + "/config")

@app.route("/projects/<project_hash>/config/jobs", methods=['POST'])
def postProjectJobSettings(project_hash):
    project = get_project(project_hash)

    job_settings = project.get_job_settings()

    for job_type_name in project.get_chain().job_types:
        is_active = request.form.get("is_active-" + job_type_name)
        print is_active
        limit = request.form.get("limit-" + job_type_name)
        starred_only = request.form.get("starred_only-" + job_type_name)

        if is_active is None:
            continue

        job_data = job_settings[job_type_name]
        job_data["is_active"] = (True if is_active == "1" else False)
        job_data["limit"] = (None if limit == "0" else int(limit))
        job_data["starred_only"] = (True if starred_only == "1" else False)

        project.save_job_settings(job_type_name, job_data)

    return redirect("/projects/" + project_hash + "/compute/system")

@app.route("/projects/<project_hash>/dimensions", methods=['POST'])
def createProjectConfigurationDimension(project_hash):
    project = get_project(project_hash)
    existing_dimensions = project.get_dimensions()

    dimension_name = request.form.get("dimension_name")
    dimension_type = request.form.get("dimension_type")
    
    if (dimension_name is None or
                dimension_name in existing_dimensions.keys() or
                len(dimension_name) < 4):
        return redirect("/projects/" + project_hash + "/config")
    else:
        project.add_dimension(dimension_name, dimension_type)

        return redirect("/projects/" + project_hash + "/dimensions/" + dimension_name)

@app.route("/projects/<project_hash>/dimensions/<dimension_name>")
def getProjectConfigurationDimension(project_hash, dimension_name):
    project = get_project(project_hash)
    dimensions = project.get_dimensions()
    dimension = dimensions.get(dimension_name)

    project_dto = {
        "hash": project_hash,
        "name": project.get_project_name()
    }

    dimension_dto = {
        "name": dimension_name,
        "type": dimension.get("type"),
        "data": dimension.get("data", [])
    }

    page_data = {
        "title": "",
        "active_nav_tab": "config"
    }

    return render_template('projects/dimension.html', project=project_dto,
                           dimension=dimension_dto,
                           page_data=page_data)

@app.route("/projects/<project_hash>/dimensions/<dimension_name>", methods=['POST'])
def postProjectConfigurationDimension(project_hash, dimension_name):
    project = get_project(project_hash)

    if request.form.get("action") == "save":
        form_data = request.form["data"]
        data = json.loads(form_data)

        project.save_dimension_data(dimension_name, data)

        return redirect(
            "/projects/" + project_hash + "/dimensions/" + dimension_name)
    elif request.form.get("action") == "delete":
        project.delete_dimension(dimension_name)

        return redirect("/projects/" + project_hash + "/config")


