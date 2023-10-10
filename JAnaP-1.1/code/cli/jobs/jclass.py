import os
import json
import cv2
import numpy

from matplotlib import pyplot

from skimage.morphology import disk, white_tophat

import cells.images
import cells.images.filter
import cells.shapes

from cells.edge import classify, segments, features

from .job import BaseJob

class JunctionClass(BaseJob):
    
    job_name = "jclass"
    job_description = "Classify all features rather than performing " + \
        "classification relative to perimeter"
    
    job_type = "jclass"
    
    priority = "30"
    
    def __init__(self, project):
        self.__input_image_directory = project.get_input_image_directory()

        self.__perimeter_directory = \
            project.get_artifacts_directory("perimeters")
        
        self.__job_output_directory = \
            project.get_artifacts_directory("junction-class")
            
        self.__job_output_directory_detail = \
            project.get_artifacts_directory("junction-detail")
            
        self.__project = project
        
    def get_job_headers(self, entity_map):
        job_headers = []

        for entity_row in entity_map:
            job_key = entity_row["cell_id"]

            job_file_key = job_key + ".json"

            job_file = \
                os.path.join(self.__job_output_directory, job_file_key)

            perimeter_file_key = entity_row["cell_id"] + ".json"
            perimeter_file = os.path.join(self.__perimeter_directory, perimeter_file_key)

            if os.path.isfile(job_file):
                status = "done"
            else:
                if os.path.isfile(perimeter_file):
                    status = "open"
                else:
                    status = "not-ready"

            job_headers.append({
                "job_key": job_key,
                "job_type": self.job_type,
                "status": status
            })

        return job_headers
        
    def do_job(self, entity_map, key):
    
        job_entity_row = None
        
        for entity_row in entity_map:
            if entity_row["cell_id"] == key:
                job_entity_row = entity_row
                break
        
        if job_entity_row is None:
            raise Exception("Could not find key")
            
        image_file_name = job_entity_row["file_name"]
        image_file = os.path.join(self.__input_image_directory, image_file_name)

        perimeter_file_key = job_entity_row["cell_id"] + ".json"
        perimeter_file = os.path.join(self.__perimeter_directory, perimeter_file_key)

        with open(perimeter_file, "r") as f:
            perimeter = json.load(f)

        # Get parameters
        image_original = cells.images.load_image(image_file)
        
        w, h, d = image_original.shape

        disk_size = \
            self.__project.get_parameter("disk_element_size", job_entity_row, w)
        filter_threshold = \
            self.__project.get_parameter("filter_intensity_cutoff",
                                         job_entity_row, w)
        
        
        # Generate mask
        feature_mask, image_processed = self.__get_shared_data(image_original,
                                                               filter_threshold,
                                                               disk_size)
                                                               
        window_size = 5
        feature_data = features.get_cell_junction_data(feature_mask, perimeter,
                                                        window_size)

        detail_data = features.get_path_junction_data(image_processed, perimeter,
                                                        window_size, filter_threshold)

        output_file_key = key + ".json"
        output_file = os.path.join(self.__job_output_directory, output_file_key)
        
        with open(output_file, "w") as f:
            json.dump(feature_data, f)

        # Save details
        detail_file_key = key + ".json"
        detail_file = os.path.join(self.__job_output_directory_detail, detail_file_key)

        with open(detail_file, "w") as f:
            json.dump(detail_data, f)

        return {
            "output_file": output_file_key,
            "image_file": job_entity_row["file_name"]
        }
        
    def __get_shared_data(self, image_original, filter_threshold, disk_size):

        image_intensity, image_cost = \
            cells.images.filter.filter_image(image_original)
        
        selem = disk(disk_size)

        image_processed = white_tophat(image_intensity, selem)

        feature_mask = segments.get_feature_mask(image_processed,
                                                 filter_threshold)

        return feature_mask, image_processed