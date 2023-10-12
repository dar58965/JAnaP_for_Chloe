import os
import json

import cv2
import numpy.ma

import cells.waypoints.seeding
import cells.waypoints.perimeter
import cells.images
import cells.images.filter
import cells.shapes

from .job import BaseJob

class ImageData(BaseJob):
    job_name = "imdata"
    job_description = ""
    job_type = "imdata"
    priority = 50

    def __init__(self, project):
        self.__input_image_directory = project.get_input_image_directory()

        self.__perimeter_directory = \
            project.get_artifacts_directory("perimeters")

        self.__imdata_directory = \
            project.get_artifacts_directory("image-data")


    def get_job_headers(self, entity_map):
        job_headers = []

        visited = []
        for entity_row in entity_map:
            job_key = entity_row["file_name"]
            if job_key in visited:
                continue
            else:
                visited.append(job_key)

            job_file_key = job_key + ".json"

            job_file = \
                os.path.join(self.__imdata_directory, job_file_key)

            cell_id = entity_row["cell_id"]

            perimeter_file_key = cell_id + ".json"

            perimeter_file = \
                os.path.join(self.__perimeter_directory, perimeter_file_key)

            if os.path.isfile(job_file):
                status = "done"
            else:
                if os.path.isfile(perimeter_file):
                    status = "open"
                else:
                    status = "pending"

            job_headers.append({
                "job_key": job_key,
                "job_type": "imdata",
                "status": status
            })

        return job_headers

    def do_job(self, entity_map, key):
        # Get required data
        job_entity_rows = []

        for entity_row in entity_map:
            if entity_row["file_name"] == key:
                job_entity_rows.append(entity_row)

        if len(job_entity_rows) == 0:
            raise Exception("Could not find key")

        # Get fully qualified image location
        file_name = key
        image_path = os.path.join(self.__input_image_directory, file_name)

        # Load cell perimeters
        perimeters = {}

        for entity_map_row in job_entity_rows:
            file_key = entity_map_row["cell_id"] + ".json"
            perimeter_file = os.path.join(self.__perimeter_directory, file_key)

            with open(perimeter_file, "r") as f:
                perimeter = json.load(f)

            perimeters[entity_map_row["cell_id"]] = perimeter

        # Compute shape factors
        image_data = self.__calculate_image_data(image_path, perimeters)

        # Save shape factor lines
        imdata_file_key = key + ".json"
        imdata_file = os.path.join(self.__imdata_directory, imdata_file_key)

        with open(imdata_file, "w") as f:
            json.dump(image_data, f)

        return {
            "output_file": imdata_file,
            "image_file": key
        }

    def __calculate_image_data(self, image_path, perimeter_paths):

        image_original = cells.images.load_image(image_path)

        image_intensity, image_cost = \
            cells.images.filter.filter_image(image_original)

        w, h = image_intensity.shape

        legend_mask = cells.images.filter.get_legend_mask(w, h, None)

        masked_image_intensity = numpy.ma.array(image_intensity,
                                                mask=legend_mask)

        mean_intensity = numpy.mean(masked_image_intensity)
        min_intensity = numpy.min(masked_image_intensity)
        max_intensity = numpy.max(masked_image_intensity)

        image_data = {
            "width": w,
            "height": h,
            "mean_intensity": mean_intensity,
            "min_intensity": int(min_intensity),
            "max_intensity": int(max_intensity)
        }

        return image_data
