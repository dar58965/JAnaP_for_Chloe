import os
import json

import cv2

import cells.waypoints.seeding
import cells.waypoints.perimeter
import cells.images
import cells.images.filter
import cells.shapes

from .job import BaseJob

class Shapes(BaseJob):
    job_name = "shapes"
    job_description = ""
    job_type = "shapes"

    priority = 20

    def __init__(self, project):
        self.__project = project
        self.__input_image_directory = project.get_input_image_directory()

        self.__perimeter_directory = \
            project.get_artifacts_directory("perimeters")

        self.__shape_directory = \
            project.get_artifacts_directory("shape-factors")


    def get_job_headers(self, entity_map):
        job_headers = []

        for entity_row in entity_map:
            cell_id = entity_row["cell_id"]

            shape_file_key = cell_id + ".json"

            shape_factor_file = \
                os.path.join(self.__shape_directory, shape_file_key)

            perimeter_file_key = cell_id + ".json"

            perimeter_file = \
                os.path.join(self.__perimeter_directory, perimeter_file_key)
            
            if os.path.isfile(shape_factor_file):
                status = "done"
            else:
                if os.path.isfile(perimeter_file):
                    status = "open"
                else:
                    status = "pending"

            job_headers.append({
                "job_key": cell_id,
                "job_type": "shapes",
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

        # Get fully qualified image location
        file_name = job_entity_row["file_name"]
        image_path = os.path.join(self.__input_image_directory, file_name)

        # Load cell perimeter
        perimeter_file_key = key + ".json"
        perimeter_file = os.path.join(self.__perimeter_directory,
                                      perimeter_file_key)
        with open(perimeter_file, "r") as f:
            perimeter = json.load(f)

        # Compute shape factors
        shape_data = self.__calculate_shape_data(image_path, perimeter, job_entity_row)

        # Save shape factor lines
        shape_file_key = key + ".json"
        shape_file = os.path.join(self.__shape_directory, shape_file_key)

        with open(shape_file, "w") as f:
            json.dump(shape_data, f)

        return {
            "output_file": shape_file,
            "image_file": job_entity_row["file_name"]
        }

    def __calculate_shape_data(self, image_path, perimeter_path, job_entity_row):
        image_original = cells.images.load_image(image_path)

        image_intensity, image_cost = \
            cells.images.filter.filter_image(image_original)

        w, h = image_intensity.shape

        conversion_factor = \
            self.__project.get_parameter("image_scale", job_entity_row, w)

        shape_calculator = cells.shapes.CellShapes(image_intensity,
                                                   perimeter_path)

        shape_data = {}

        perimeter = shape_calculator.get_perimeter()
        shape_data["perimeter_pixels"] = len(perimeter_path)
        shape_data["perimeter_measured"] = perimeter
        shape_data["perimeter_um"] = perimeter * conversion_factor

        area = shape_calculator.get_area()
        shape_data["area_measured"] = area
        shape_data["area_um"] = area * conversion_factor**2

        shape_data["convex_area"] = shape_calculator.get_convex_area()
        shape_data["solidity"] = shape_calculator.get_solidity()
        shape_data["circularity"] = shape_calculator.get_circularity()

        shape_data["hull_aspect_ratio_ab"], shape_data["hull_aspect_ratio"] = \
            shape_calculator.get_hull_aspect_ratios()
            
        #adding angle
        shape_data["angle"] = shape_calculator.get_angle()

        return shape_data
