
import os
import glob

from controllers import app
from controllers import configuration

def get_project(hash):
    import cli.project

    # Currently hashes are just the directory names, might want to support 
    # spaces in the future though so I've separated them. They're currently
    # effectively interchangeable. 
    project_directory_name = hash

    projects_root = configuration.NodeConfiguration.Paths.projects_root
    project_directory = os.path.join(projects_root, project_directory_name)

    project = cli.project.Project(project_directory)

    return project


def get_project_name(hash):
    project_name_parts = hash.split("_")
    
    project_name = " ".join([part.capitalize() 
        if (len(part) > 4 or part == project_name_parts[0]) else part
        for part in project_name_parts])

    return project_name


def get_waypoint_tasks(project):
    import cells.waypoints.seeding
    import cells.images

    input_image_directory = project.get_input_image_directory()
    variant = project.get_variant()
    dimensions = project.get_dimensions()

    image_data = cells.images.get_image_collection(input_image_directory, variant, dimensions)

    counter = 0
    for image_data_row in image_data:
        if image_data_row.get("stain") == "TxRed":
            # print image_data_row
            counter += 1
            if counter > 5:
                break
    

    input_waypoints_directory = project.get_artifacts_directory("waypoints")

    waypoint_files = glob.glob(input_waypoints_directory + os.sep + "*")
    waypoint_tasks = cells.waypoints.seeding.get_waypoints_tasks(waypoint_files, image_data)
    
    # Calculate task status data
    waypoint_tasks_data = {}

    tasks_total = 0
    tasks_done = 0
    tasks_wip = 0
    tasks_open = 0
    tasks_progress = 0.0

    tasks_total = len(waypoint_tasks)
    
    for waypoint_task in waypoint_tasks:
        if waypoint_task.get("status") == "open":
            tasks_open = tasks_open + 1
        elif waypoint_task.get("status") == "in-progress":
            tasks_wip = tasks_wip + 1
        elif waypoint_task.get("status") == "complete":
            tasks_done = tasks_done + 1
    
    if tasks_total > 0:
        tasks_progress = round(100.0 * float(tasks_done) / tasks_total, 2)

    
    waypoint_tasks_data["total"] = tasks_total
    waypoint_tasks_data["done"] = tasks_done
    waypoint_tasks_data["wip"] = tasks_wip
    waypoint_tasks_data["open"] = tasks_open
    waypoint_tasks_data["progress"] = tasks_progress

    return waypoint_tasks, waypoint_tasks_data