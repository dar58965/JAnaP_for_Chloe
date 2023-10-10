import os
import datetime
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


@app.route("/projects/<project_hash>/compute")
def getComputeOverview(project_hash):
    """
    Filter ->
      Trace ->

        Shapes
        Classification
        Nucleus

    :param project_hash:
    :return:
    """

    project = get_project(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project.get_project_name()
    }

    page_data = {
        "title": "",
        "active_nav_tab": "overview"
    }

    return render_template('compute/overview.html', project=project_dto,
                           page_data=page_data)


@app.route("/projects/<project_hash>/compute/settings")
def getComputeSettings(project_hash):
    """
    Filter ->
      Trace ->

        Shapes
        Classification
        Nucleus

    :param project_hash:
    :return:
    """

    project = get_project(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project.get_project_name()
    }

    page_data = {
        "title": "",
        "active_nav_tab": "settings"
    }

    return render_template('compute/settings.html', project=project_dto,
                           page_data=page_data)


@app.route("/projects/<project_hash>/compute/config", methods=['POST'])
def postComputeConfig(project_hash):
    """ Add/Remove Image """
    pass


@app.route("/projects/<project_hash>/compute/starred")
def getStarredList(project_hash):
    """ List of images in sample set """
    import cells.images
    import cli.operations

    project = get_project(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project.get_project_name()
    }

    starred_images = project.get_starred_images()

    input_image_directory = project.get_input_image_directory()

    project_images = cells.images.get_image_list(input_image_directory)

    page_data = {
        "title": "",
        "active_nav_tab": "starred"
    }

    return render_template('compute/starred.html', project=project_dto,
                           starred_images=starred_images,
                           project_images=project_images, page_data=page_data)



@app.route("/projects/<project_hash>/compute/starred", methods=['POST'])
def postStarredList(project_hash):
    """ Add/Remove Image """

    project = get_project(project_hash)

    # image_filename = request.form["filename"]


    if request.form.get("action") == "add":
        selected_images = request.form.getlist("selected_image")

        for selected_image in selected_images:
            project.add_starred_image(selected_image)

        project.save()
    elif request.form.get("action") == "remove":
        selected_image = request.form.get("selected_image")
        project.remove_starred_image(selected_image)
        project.save()

    return redirect("/projects/" + project_hash + "/compute/starred")


@app.route("/projects/<project_hash>/compute/system")
def getSystemData(project_hash):
    import cli.steps.trace
    import cli.jobs.job

    project = get_project(project_hash)

    project_dto = {
        "hash": project_hash,
        "name": project.get_project_name()
    }

    # Job Configuration
    job_config_dto = []
    job_settings = project.get_job_settings()
    for job_type_name in project.get_chain().job_types:
        job_config_dto.append({
            "job_type_name": job_type_name,
            "is_active": job_settings[job_type_name]["is_active"],
            "limit": job_settings[job_type_name]["limit"],
            "starred_only": job_settings[job_type_name]["starred_only"],
        })

    job_manager = cli.jobs.job.JobManager(project)

    job_headers = job_manager.get_job_headers()
    trace_job_metrics = job_manager.get_job_metrics()

    operation_data = {
        "heartbeat": None,
        "heartbeat_elapsed": None,
    }

    for key in trace_job_metrics.keys():
        operation_data[key] = {
            "done": 0, 
            "total": 0,
            "cpu_time": trace_job_metrics[key]["cpu_time"],
            "avg_time": trace_job_metrics[key]["avg_time"]
        }

    for job_header in job_headers:
        job_type = job_header["job_type"]
        if job_header["status"] == "done":
            operation_data[job_type]["done"] = \
                operation_data[job_type].get("done", 0) + 1

        operation_data[job_type]["total"] = \
            operation_data[job_type].get("total", 0) + 1

    heartbeat_file = os.path.join(project.get_system_directory(), "heartbeat")

    if os.path.isfile(heartbeat_file):
        with open(heartbeat_file, "r") as f:
            heartbeat = f.read()

        operation_data["heartbeat"] = heartbeat

        heartbeat_dt = dateutil.parser.parse(heartbeat)
        hb_elapsed = datetime.datetime.now() - heartbeat_dt
        operation_data["heartbeat_elapsed"] = hb_elapsed.total_seconds()

    page_data = {
        "title": "",
        "active_nav_tab": "system"
    }

    return render_template('compute/system.html', project=project_dto,
                           operation_data=operation_data,
                           job_configs=job_config_dto,
                           page_data=page_data)