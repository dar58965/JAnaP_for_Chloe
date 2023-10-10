import os

import cells.waypoints.seeding
import cells.images


def get_image_collection(project):
    
    input_image_directory = project.get_input_image_directory()
    variant = project.get_variant()
    dimensions = project.get_dimensions()

    image_data = cells.images.get_image_collection(input_image_directory, variant, dimensions)

    return image_data


def __waypoints_get_cell_collection(project, image_collection):
    cell_collection = []

    input_waypoints_directory = project.get_artifacts_directory("waypoints")

    # Caching the file reads makes this twice as fast
    i_w_file_cache = {}

    for image_data_row in image_collection:
        waypoints_base_key = image_data_row["seed_source_image"] + ".tsv"
        waypoints_working_key = image_data_row["seed_source_image"] + ".tsv-working"
        
        waypoints_file = None

        if os.path.isfile(os.path.join(input_waypoints_directory, waypoints_base_key)):
            waypoints_file = os.path.join(input_waypoints_directory, waypoints_base_key)
        elif os.path.isfile(os.path.join(input_waypoints_directory, waypoints_working_key)):
            waypoints_file = os.path.join(input_waypoints_directory, waypoints_working_key)

        # If there are no working or completed waypoints, there's no file to check anyway
        if waypoints_file is None:
            continue
        
        if i_w_file_cache.get(waypoints_file) is not None:
            image_waypoints = i_w_file_cache.get(waypoints_file)
        else:
            image_waypoints = cells.waypoints.seeding.load_waypoints(waypoints_file)
            i_w_file_cache[waypoints_file] = image_waypoints

        file_name = image_data_row.get("file_name")
        file_root = image_data_row.get("file_root")
        
        for waypoints_row in image_waypoints:
            current_row = image_data_row.copy()

            center_r, center_c = waypoints_row.get("geometric_center")
        
            cell_number = file_root.replace(" ", "") + "--" + str(center_r) + "-" + str(center_c)
            cell_id = file_name.replace(" ", "") + "--" + str(center_r) + "-" + str(center_c)

            current_row["cell_number"] = cell_number
            current_row["cell_id"] = cell_id
            current_row["geometric_center"] = waypoints_row.get("geometric_center")
            current_row["waypoints"] = waypoints_row.get("waypoints")
            
            cell_collection.append(current_row)
    
    return cell_collection

def get_cell_collection(project, image_collection=None):
    """
    Returns: 
        [
            {
                "file_name": file_name,
                "file_root": image_root,
                "stain": stain,
                "experiment_name": experiment_name,
                "experiment_date": experiment_date,
                "seed_source_image": seed_source_image

                "cell_number": ...,
                "cell_id": ...,
                "geometric_center": ...

                // Optional depending on seeding method: 
                "waypoints": ...,
            }
        ]
    """

    if image_collection is None:
        image_collection = get_image_collection(project)
    
    return __waypoints_get_cell_collection(project, image_collection)
    