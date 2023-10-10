import os
import glob
import base64
import json 
import time
import shutil

from controllers import app
from controllers import configuration
from controllers.shared import get_project, get_waypoint_tasks, get_project_name

from flask import render_template
from flask import session
from flask import request
from flask import redirect
from flask import jsonify
from flask import send_from_directory

from PIL import Image


def getWaypointTasks(project):
    # TODO: DEP
    return get_waypoint_tasks(project)


@app.route("/projects/<project_hash>/tasks")
def getTasks(project_hash):
    import cli.project
    
    project = get_project(project_hash)
    waypoint_tasks, waypoint_tasks_data = getWaypointTasks(project)

    project_name = get_project_name(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project_name
    }

    status_filter_parameter = request.args.get('status')

    if status_filter_parameter is not None:
        if status_filter_parameter in ["all", "open", "in-progress", "complete"]:
            session["tasks_status_filter"] = status_filter_parameter
    
    if "tasks_status_filter" in session:
        status_filter = session["tasks_status_filter"]
    else:
        status_filter = "all"

    if status_filter != "all":
        filtered_task_list = []
        for waypoint_task in waypoint_tasks:
            if waypoint_task.get("status") == status_filter:
                filtered_task_list.append(waypoint_task)
        waypoint_tasks = filtered_task_list

    return render_template('tasks/tasks.html', project=project_dto, 
                           tasks=waypoint_tasks, 
                           tasks_status_metrics=waypoint_tasks_data, 
                           status_filter=status_filter)



def getCachedImage(project, image_name):
    cache_root = os.path.join(app.static_folder, "tmp")
    image_cache = os.path.join(cache_root, "images")

    if not os.path.isdir(cache_root):
        os.makedirs(cache_root)
    if not os.path.isdir(image_cache):
        os.makedirs(image_cache)
    

    image_file = os.path.join(project.get_input_image_directory(), image_name)
    cache_image_name = image_name + ".png"

    cache_image_file = os.path.join(image_cache, cache_image_name)

    if not os.path.isfile(cache_image_file):
        image = Image.open(image_file)
        output_image = image.convert("RGB")
        output_image.save(image_cache + os.sep + cache_image_name, "PNG")

    image_relative_url = "/static/tmp/images/" + cache_image_name
    return image_relative_url


def getCachedWaypointImage(project, image_name):
    import cv2
    import cells.waypoints.seeding

    cache_root = os.path.join(app.static_folder, "tmp")
    image_cache = os.path.join(cache_root, "images")

    if not os.path.isdir(cache_root):
        os.makedirs(cache_root)
    if not os.path.isdir(image_cache):
        os.makedirs(image_cache)

    input_waypoints_directory = project.get_artifacts_directory("waypoints")

    working_file_name = image_name + ".tsv-working"
    working_file = os.path.join(input_waypoints_directory, working_file_name)

    if not os.path.isfile(working_file):
        return getCachedImage(project, image_name)
    
    image_file = os.path.join(project.get_input_image_directory(), image_name)
    task_image_name = "task-wp-" + image_name + ".png"

    working_temp_image_name = "temp-" + image_name
    working_temp_file = os.path.join(image_cache, working_temp_image_name)

    image = cv2.imread(image_file)

    image_waypoints = cells.waypoints.seeding.load_waypoints(working_file)

    for waypoints_row in image_waypoints:
        waypoints = waypoints_row.get("waypoints")

        for idx in range(0, len(waypoints)):
            r, c = waypoints[idx]

            r_next, c_next = waypoints[(idx+1) % len(waypoints)]
            x, y = c, r
            x_next, y_next = c_next, r_next

            cv2.line(image, (x, y), (x_next, y_next), (244, 238, 66), 1)

    cv2.imwrite(working_temp_file, image)

    image = Image.open(working_temp_file)
    output_image = image.convert("RGB")
    output_image.save(image_cache + os.sep + task_image_name, "PNG")

    image_relative_url = "/static/tmp/images/" + task_image_name
    # Cache bust
    image_relative_url = image_relative_url + "?cachev=" + str(time.time())
    return image_relative_url

def getCachedWaypointImage_v2(input_image, image_waypoints, image_key_name):
    import cv2

    cache_root = os.path.join(app.static_folder, "tmp")
    image_cache = os.path.join(cache_root, "images")

    if not os.path.isdir(cache_root):
        os.makedirs(cache_root)
    if not os.path.isdir(image_cache):
        os.makedirs(image_cache)

    task_image_name = "task-wp-" + image_key_name + ".png"

    working_temp_image_name = "temp-" + image_key_name
    working_temp_file = os.path.join(image_cache, working_temp_image_name)

    image = input_image.copy()

    for waypoints_row in image_waypoints:
        waypoints = waypoints_row.get("waypoints")

        for idx in range(0, len(waypoints)):
            r, c = waypoints[idx]

            r_next, c_next = waypoints[(idx+1) % len(waypoints)]
            x, y = c, r
            x_next, y_next = c_next, r_next

            cv2.line(image, (x, y), (x_next, y_next), (244, 238, 66), 1)

    cv2.imwrite(working_temp_file, image)
    
    image = Image.open(working_temp_file)
    output_image = image.convert("RGB")
    output_image.save(image_cache + os.sep + task_image_name, "PNG")

    image_relative_url = "/static/tmp/images/" + task_image_name
    # Cache bust
    image_relative_url = image_relative_url + "?cachev=" + str(time.time())
    return image_relative_url

@app.route("/projects/tasks/waypoints/pathfinder", methods=['POST'])
def postGetPath():
    import cv2
    import numpy
    from skimage import graph
    
    import cells.images.filter

    project_hash = request.form['project_hash']
    project = get_project(project_hash)

    task_hash = request.form['task_hash']
    task_hash_decoded = base64.urlsafe_b64decode(task_hash.encode("ascii"))
    task_type = task_hash_decoded.split("::")[0]
    task_key = task_hash_decoded.split("::")[1]
    
    image_name = task_key
    image_file = os.path.join(project.get_input_image_directory(), image_name)
    
    point_1_x = int(request.form['point_1_x'])
    point_1_y = int(request.form['point_1_y'])
    point_2_x = int(request.form['point_2_x'])
    point_2_y = int(request.form['point_2_y'])

    start_r, start_c = point_1_y, point_1_x
    end_r, end_c = point_2_y, point_2_x

    start_point = point_1_y, point_1_x
    end_point = point_2_y, point_2_x


    input_image = cv2.imread(image_file)
    
    cost_image = cells.images.filter.generate_cost_image_perimeter(input_image)
    # image_intensity = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    #cost_image = image_intensity.copy()
    #cost_image = (numpy.max(cost_image) - cost_image)
    
    print start_point, end_point

    path_segment, cost = graph.route_through_array(cost_image, start_point, end_point)
    
    path = []
    x_y_path = []
    
    for e in path_segment:
        path.append(e)
        x_y_path.append([e[1], e[0]])

    return jsonify(x_y_path)

def postTask(project_hash, task_hash):
    import cells.waypoints.seeding
    import cells.images

    if request.form["task_action"] == "save":
        project = get_project(project_hash)

        input_waypoints_directory = project.get_artifacts_directory("waypoints")

        task_hash_decoded = base64.urlsafe_b64decode(task_hash.encode("ascii"))
        task_type = task_hash_decoded.split("::")[0]
        image_name = task_hash_decoded.split("::")[1]

        working_file_name = image_name + ".tsv-working"
        working_file = os.path.join(input_waypoints_directory, working_file_name)

        waypoints = []
        waypoints_raw = json.loads(request.form["waypoints"])

        for point in waypoints_raw:
            waypoints.append([point.get("y"), point.get("x")])

        cells.waypoints.seeding.append_waypoints(working_file, waypoints, created_from=image_name)
    elif request.form["task_action"] == "done":
        project = get_project(project_hash)

        input_waypoints_directory = project.get_artifacts_directory("waypoints")

        task_hash_decoded = base64.urlsafe_b64decode(task_hash.encode("ascii"))
        task_type = task_hash_decoded.split("::")[0]
        image_name = task_hash_decoded.split("::")[1]

        working_file_name = image_name + ".tsv-working"
        working_file = os.path.join(input_waypoints_directory, working_file_name)

        finished_file = working_file.replace(".tsv-working", ".tsv")
        
        if not os.path.isfile(working_file):
            raise Exception("Tried to save a working file that didn't exist.")
        
        if os.path.isfile(finished_file):
            raise Exception("Tried to overwrite a finished waypoints file.")

        shutil.move(working_file, finished_file)
    elif request.form["task_action"] == "reopen":
        project = get_project(project_hash)

        input_waypoints_directory = project.get_artifacts_directory("waypoints")

        task_hash_decoded = base64.urlsafe_b64decode(task_hash.encode("ascii"))
        task_type = task_hash_decoded.split("::")[0]
        image_name = task_hash_decoded.split("::")[1]

        working_file_name = image_name + ".tsv-working"
        working_file = os.path.join(input_waypoints_directory, working_file_name)

        finished_file = working_file.replace(".tsv-working", ".tsv")
        
        if not os.path.isfile(finished_file):
            raise Exception("Tried to save a finished file that didn't exist.")
        
        if os.path.isfile(working_file):
            raise Exception("Tried to overwrite an existing working waypoints file.")

        shutil.move(finished_file, working_file)
    elif request.form["task_action"] == "delete":
        project = get_project(project_hash)

        input_waypoints_directory = project.get_artifacts_directory("waypoints")

        task_hash_decoded = base64.urlsafe_b64decode(task_hash.encode("ascii"))
        task_type = task_hash_decoded.split("::")[0]
        image_name = task_hash_decoded.split("::")[1]

        working_file_name = image_name + ".tsv-working"
        working_file = os.path.join(input_waypoints_directory, working_file_name)

        wp_row_raw = request.form["wp_row"]

        if wp_row_raw is not None:
            wp_row = int(wp_row_raw)

            if wp_row > 0:
                cells.waypoints.seeding.delete_waypoints(working_file, wp_row)

        
    return redirect("/projects/" + project_hash + "/tasks/" + task_hash)

@app.route("/projects/<project_hash>/tasks/<task_hash>", methods=['GET', 'POST'])
def getTask(project_hash, task_hash):
    if request.method == 'POST':
        return postTask(project_hash, task_hash)
    else:
        import cells.waypoints.seeding
        import cli.project
        import cv2

        project = get_project(project_hash)
        # waypoint_tasks, waypoint_tasks_data = getWaypointTasks(project)

        project_header = {
            "hash": project_hash
        }

        task_hash_decoded = base64.urlsafe_b64decode(task_hash.encode("ascii"))
        task_type = task_hash_decoded.split("::")[0]
        task_key = task_hash_decoded.split("::")[1]
        
        image_name = task_key

        # Load Image Data
        image_file = os.path.join(project.get_input_image_directory(), image_name)
        input_image = cv2.imread(image_file)
        height, width, channels = input_image.shape

        input_waypoints_directory = project.get_artifacts_directory("waypoints")
        working_file_name = image_name + ".tsv-working"
        working_file = os.path.join(input_waypoints_directory, working_file_name)
        completed_file_name = image_name + ".tsv"
        completed_file = os.path.join(input_waypoints_directory, completed_file_name)
        
        task_status = "open"

        if os.path.isfile(working_file):
            task_status = "in-progress"
        elif os.path.isfile(completed_file):
            task_status = "complete"

        # Load waypoints
        if task_status == "complete":
            image_waypoints = cells.waypoints.seeding.load_waypoints(completed_file)
        elif task_status == "in-progress":
            image_waypoints = cells.waypoints.seeding.load_waypoints(working_file)
        else:
            image_waypoints = []

        row = 1
        for waypoints_row in image_waypoints:
            waypoints_row["row"] = row
            row += 1

        # Get png versions of images
        working_image_wp_url = getCachedWaypointImage_v2(input_image, image_waypoints, image_name)
        working_image_url = getCachedImage(project, image_name)

        view_type_parameter = request.args.get('vt')

        if view_type_parameter == "review":
            view_type = "review"
        else:
            view_type = "waypoints"


        task_data = {
            "hash": task_hash,
            "status": task_status,
            "image_name": task_key,
            "image_width": height,
            "image_height": width,
            "image_wp_url": working_image_wp_url,
            "image_url": working_image_url
        }
        
        return render_template('tasks/task.html', project=project_header, 
                            task=task_data, image_url=working_image_url,
                            image_waypoints=image_waypoints,
                            view_type=view_type)


def postWaypoints():
    pass

def postImageDone():
    pass