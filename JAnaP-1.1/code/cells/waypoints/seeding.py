# Creating Waypoints
# 
# Waypoints files are managed by their artifact key. The root is the name
# of the image they are associated with. ".tsv" denotes that they are stored
# as tab delimited. A "-working" suffix indicates that the waypointing of
# that cell is still in progress.
#
# Waypoints files start with a header row.
#   Headers:
#     - Created From File
#     - Waypoints [r, c]
#     - Geometric Center
#     - Metadata
# 
# Metadata is an optional key-value (dictionary) column for information about
# who created the waypoints, nodes, algorithms, etc. None of the information
# is used for calculations or anything currently. 
#

import os
import base64
import json

def load_waypoints(waypoints_file):
    with open(waypoints_file, "r") as f:
        waypoint_file_lines = f.readlines()
        
    image_waypoints = []

    for waypoint_row in waypoint_file_lines[1:]:
        waypoint_row = waypoint_row.strip('\r\n')
        waypoint_row_parts = waypoint_row.split("\t")
        
        image_waypoints.append({
            "file_name": waypoint_row_parts[0],
            "waypoints": json.loads(waypoint_row_parts[1]),
            "geometric_center": json.loads(waypoint_row_parts[2])
        })
    
    return image_waypoints

def append_waypoints(waypoints_file, waypoints, created_from=""):
    output_rows = []

    if os.path.isfile(waypoints_file):
        with open(waypoints_file, "r") as f:
            waypoint_file_lines = f.readlines()
        
        for waypoint_row in waypoint_file_lines:
            waypoint_row = waypoint_row.strip()
            waypoint_row_parts = waypoint_row.split("\t")
            if len(waypoint_row_parts) > 1:
                output_rows.append(waypoint_row_parts)

    else:
        output_rows.append([
            "Created From File",
            "Waypoints [r, c]", 
            "Geometric Center",
            "Metadata"
        ])

    r_vals = []
    c_vals = []
    for waypoint in waypoints:
        r, c = waypoint
        r_vals.append(r)
        c_vals.append(c)
    
    geo_r, geo_c = sum(r_vals)/len(r_vals), sum(c_vals)/len(c_vals)

    metadata = {}

    output_rows.append([
        created_from,
        json.dumps(waypoints),
        json.dumps([geo_r, geo_c]),
        json.dumps(metadata)
    ])

    with open(waypoints_file, "w") as f:
        output = "\n".join(["\t".join(output_row) for output_row in output_rows])
        f.write(output)

def delete_waypoints(waypoints_file, delete_row):
    """
    delete_row includes the header
    """

    output_rows = []
    row_number = 0

    if os.path.isfile(waypoints_file):
        with open(waypoints_file, "r") as f:
            waypoint_file_lines = f.readlines()
        
        for waypoint_row in waypoint_file_lines:
            waypoint_row = waypoint_row.strip()
            waypoint_row_parts = waypoint_row.split("\t")
            if len(waypoint_row_parts) > 1:
                if row_number != delete_row:
                    output_rows.append(waypoint_row_parts)
            
            row_number += 1

    else:
        output_rows.append([
            "Created From File",
            "Waypoints [r, c]", 
            "Geometric Center",
            "Metadata"
        ])

    with open(waypoints_file, "w") as f:
        output = "\n".join(["\t".join(output_row) for output_row in output_rows])
        f.write(output)



def get_waypoints_tasks(waypoints_keys, image_data):
    
    waypoints_file_status = {}
    
    for waypoints_key in waypoints_keys:
        waypoints_key_basename = waypoints_key
        if "/" in waypoints_key:
            waypoints_key_basename = waypoints_key.split("/")[-1]
        elif "\\" in waypoints_key:
            waypoints_key_basename = waypoints_key.split("\\")[-1]
        
        if ".tsv-working" in waypoints_key_basename:
            waypoints_key_basename = waypoints_key_basename.replace(".tsv-working", ".tsv")
            waypoints_file_status[waypoints_key_basename] = "in-progress"
        else:
            waypoints_file_status[waypoints_key_basename] = "complete"

    waypoints_tasks = []

    for image_data_row in image_data:
        if image_data_row["seed_source_image"] != image_data_row["file_name"]:
            continue

        waypoints_file = image_data_row["seed_source_image"] + ".tsv"
        
        waypoint_task_status = waypoints_file_status.get(waypoints_file, "open")

        task_hash_string = "waypoints::" + image_data_row["file_name"]
        task_hash = base64.urlsafe_b64encode(task_hash_string)

        waypoints_tasks.append(
            {
                "image_file_name": image_data_row["file_name"],
                "task_hash": task_hash,
                "status": waypoint_task_status
            }
        )

    return waypoints_tasks
