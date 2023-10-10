import os
import json

import cells.waypoints.seeding
import cells.waypoints.perimeter
import cells.images
import cells.images.filter

from cli.jobs.job import BaseJob

class Trace(BaseJob):
    job_name = "trace"
    job_description = ""
    job_type = "trace"
    priority = 10

    def __init__(self, project):
        self.__input_image_directory = project.get_input_image_directory()

        self.__waypoints_directory = \
            project.get_artifacts_directory("waypoints")

        self.__perimeter_directory = \
            project.get_artifacts_directory("perimeters")

    def get_job_headers(self, entity_map):
        job_headers = []

        for entity_row in entity_map:
            cell_id = entity_row["cell_id"]

            perimeter_file_key = cell_id + ".json"

            perimeter_file = \
                os.path.join(self.__perimeter_directory, perimeter_file_key)

            if os.path.isfile(perimeter_file):
                status = "done"
            else:
                status = "open"

            job_headers.append({
                "job_key": cell_id,
                "job_type": "trace",
                "status": status
            })

        return job_headers

    def do_job(self, entity_map, key):
        # Get required data
        job_entity_row = None

        for entity_row in entity_map:
            if entity_row["cell_id"] == key:
                job_entity_row = entity_row
                break

        if job_entity_row is None:
            raise Exception("Could not find key")

        waypoints_base_key = job_entity_row["seed_source_image"] + ".tsv"

        waypoints_file = os.path.join(self.__waypoints_directory,
                                      waypoints_base_key)

        if not os.path.isfile(waypoints_file):
            raise Exception("Could not waypoints file")

        image_waypoints = cells.waypoints.seeding.load_waypoints(waypoints_file)

        job_waypoints_row = None
        file_name = job_entity_row["file_name"]

        for waypoints_row in image_waypoints:
            center_r, center_c = waypoints_row.get("geometric_center")

            row_cell_id = file_name.replace(" ", "") + "--" + str(
                center_r) + "-" + str(center_c)

            if row_cell_id == key:
                job_waypoints_row = waypoints_row

        waypoints = job_waypoints_row["waypoints"]
        image_path = os.path.join(self.__input_image_directory, file_name)

        perimeter_file_key = key + ".json"

        perimeter_file = os.path.join(self.__perimeter_directory,
                                      perimeter_file_key)

        perimeter = self.__trace_perimeter(image_path, waypoints)

        with open(perimeter_file, "w") as f:
            json.dump(perimeter, f)

        return {
            "output_file": perimeter_file,
            "image_file": job_entity_row["file_name"]
        }

    def __trace_perimeter(self, image_path, waypoints):
        image_original = cells.images.load_image(image_path)

        image_cost = \
            cells.images.filter.generate_cost_image_perimeter(image_original)
        
        perimeter = \
            cells.waypoints.perimeter.get_perimeter(image_cost, waypoints)
        
        return perimeter
