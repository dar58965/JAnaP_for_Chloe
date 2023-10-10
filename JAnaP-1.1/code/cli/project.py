import os
import json
import datetime
import dateutil.parser

import chains.factory

class Project():
    __config_file_name = "_project.config.json"


    def __init__(self, project_root):
        self.project_root = project_root
        
        self.__project_hash = project_root.split(os.sep)[-2] \
            if (project_root[-1] == os.sep) else project_root.split(os.sep)[-1]
        
        self.__load_configuration()

    def get_chain(self):
        return chains.factory.get_chain(self)

    def __migrate_project(self):
        ## Helper for migrations

        parameter_defaults = {
            "image_scale": {
                "description": "uM per pixel",
                "default_value": 0,
                "value_map": {
                    "image-size:1024": 0.17857,
                    "image-size:2048": 0.0892857
                }
            },
            "filter_intensity_cutoff": {
                "description": "Minimum intensity for junction pixels",
                "default_value": 15,
                "value_map": {

                }
            },
            "disk_element_size": {
                "description": "Size of the tophat filter disk",
                "default_value": 5.0,
                "value_map": {

                }
            },
            "image_filter_type": {
                "description": "Image filter type. Leave as 111 to have no filter. 100 for red only, 10 (010) for green only or 1 (001) for blue only.",
                "default_value": "111",
                "value_map": {

                }
            }
        }

        for key, data in parameter_defaults.iteritems():
            if key not in self.__parameters.keys():
                self.__parameters[key] = data

        for job_name in self.get_chain().job_types:
            if job_name not in self.__job_chain_configs.keys():
                self.__job_chain_configs[job_name] = {
                    "is_active": False,
                    "limit": None,
                    "starred_only": False
                }

    def __load_configuration(self):
        config_file = os.path.join(self.project_root, self.__config_file_name)

        if not os.path.isfile(config_file):
            self.__variant = {
                "name": "", 
                "values": [],
                "primary_value": ""
            }

            self.__dimensions = {}

            self.__parameters = {}
            self.__job_chain_configs = {}

            self.__starred_images = []

            self.__project_name = None
            self.__created_ts = None
        else:
            with open(config_file, "r") as f:
                config_object = json.load(f)
            
            self.__variant = config_object.get("variant")
            self.__dimensions = config_object.get("dimensions", {})

            self.__parameters = config_object.get("parameters", {})
            self.__job_chain_configs = config_object.get("job_chain_configs", {})

            self.__starred_images = config_object.get("starred_images", [])

            self.__project_name = config_object.get("project_name")

            t_created_ts = config_object.get("created_ts")

            if t_created_ts is not None:
                self.__created_ts = dateutil.parser.parse(t_created_ts)
            else:
                self.__created_ts = t_created_ts

        self.__migrate_project()



    def __save_configuration(self):
        if self.__created_ts is not None:
            created_ts_encoded = str(self.__created_ts)
        else:
            created_ts_encoded = None

        config_object = {
            "project_name": self.__project_name,
            "variant": self.__variant,
            "dimensions": self.__dimensions,
            "parameters": self.__parameters,
            "job_chain_configs": self.__job_chain_configs,
            "created_ts": created_ts_encoded,
            "starred_images": self.__starred_images
        }
        
        config_file = os.path.join(self.project_root, self.__config_file_name)

        with open(config_file, "w") as f:
            json.dump(config_object, f)

    def _set_project_name(self, project_name):
        self.__project_name = project_name
    
    def _set_created_ts(self):
        self.__created_ts = datetime.datetime.now()

    def get_project_hash(self):
        return self.__project_hash

    def get_project_name(self):
        if self.__project_name is None:
            project_name_parts = self.__project_hash.split("_")
            
            project_name = " ".join([part.capitalize() 
                if (len(part) > 4 or part == project_name_parts[0]) else part for part in project_name_parts])

            return project_name
        else:
            return self.__project_name

    def get_created_ts(self):
        return self.__created_ts

    def save(self):
        self.__save_configuration()

    def get_variant(self):
        """
        Get the variant object

        Variant structure:
            {
                "name": "Stain",
                "values": ["TxRed", "GFP"],
                "primary_value": "GFP"
            }

        """
        
        return self.__variant

    def set_variant(self, variant):
        self.__variant = variant

        self.__save_configuration()

    def get_dimensions(self):
        """
        Dimensions are a dictionary of dictionaries

        {
            "name": {
                "type": ("Date Parse" or "String Match"),
                "data":
            }
        }
        
        """

        return self.__dimensions

    def add_dimension(self, dimension_name, dimension_type):
        self.__dimensions[dimension_name] = {
            "type": dimension_type
        }

        self.__save_configuration()

    def save_dimension_data(self, dimension_name, data):

        self.__dimensions[dimension_name]["data"] = data

        self.__save_configuration()

    def delete_dimension(self, dimension_name):
        del self.__dimensions[dimension_name]
        self.__save_configuration()

    def get_parameters(self):
        return self.__parameters

    def get_parameter(self, parameter, entity_row, image_width=None):
        if self.__parameters.get(parameter, None) is None:
            return None

        if len(self.__parameters[parameter]["value_map"].keys()) == 0:
            return self.__parameters[parameter]["default_value"]

        variant_string = "variant:" + entity_row.get("variant", "")

        if variant_string in self.__parameters[parameter]["value_map"].keys():
            return self.__parameters[parameter]["value_map"].get(variant_string)

        if image_width is not None:
            img_string = "image-size:" + str(image_width)

            if img_string in self.__parameters[parameter]["value_map"].keys():
                return self.__parameters[parameter]["value_map"].get(img_string)

        return self.__parameters[parameter]["default_value"]

    def save_parameter_data(self, parameter_name, data):
        self.__parameters[parameter_name] = data
        self.__save_configuration()

    def delete_parameter(self, parameter_name):
        del self.__parameters[parameter_name]
        self.__save_configuration()

    def get_starred_images(self):
        return self.__starred_images

    def add_starred_image(self, image_filename):
        if image_filename not in self.__starred_images:
            self.__starred_images.append(image_filename)


    def remove_starred_image(self, image_filename):
        if image_filename in self.__starred_images:
            self.__starred_images.remove(image_filename)

    def get_job_settings(self):
        return self.__job_chain_configs

    def save_job_settings(self, job_type, data):
        self.__job_chain_configs[job_type] = data
        self.__save_configuration()

    def get_input_image_directory(self):
        input_directory = os.path.join(self.project_root, "input")
        input_image_directory = os.path.join(input_directory, "images")
    
        return input_image_directory

    def get_artifacts_directory(self, artifact_name=None):
        artifact_root = os.path.join(self.project_root, "artifacts")

        if artifact_name is None:
            artifact_directory = artifact_root
        else:
            artifact_directory = os.path.join(artifact_root, artifact_name)

        if not os.path.isdir(artifact_directory):
            os.makedirs(artifact_directory)

        return artifact_directory


    def get_system_directory(self):
        system_directory = os.path.join(self.project_root, "system")

        if not os.path.isdir(system_directory):
            os.makedirs(system_directory)

        return system_directory

    def get_output_directory(self, output_type=None):
        output_root = os.path.join(self.project_root, "output")

        if output_type is None:
            output_directory = output_root
        else:
            output_directory = os.path.join(output_root, output_type)

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        return output_directory


    @staticmethod
    def create(project_root, project_name):

        # Create project directory
        os.makedirs(project_root)

        # Create input directory
        input_directory = os.path.join(project_root, "input")
        os.makedirs(input_directory)

        ## Create images directory
        input_image_directory = os.path.join(input_directory, "images")
        os.makedirs(input_image_directory)

        # Create artifacts directory
        artifact_root = os.path.join(project_root, "artifacts")
        os.makedirs(artifact_root)

        ## Create waypoints directory
        artifact_waypoints_directory = os.path.join(artifact_root, "waypoints")
        os.makedirs(artifact_waypoints_directory)

        # Create configuration
        project = Project(project_root)
        project._set_project_name(project_name)
        project._set_created_ts()
        project.save()

        return project


def get_dimension_date_parse(filename):
    clean_filename = filename.strip()
    year = clean_filename[0:2]
    month = clean_filename[2:4]
    day = clean_filename[4:6]

    if year != "16":
        return ""
    else:
        return "20" + year + "-" + month + "-" + day


def get_dimension_string_match(filename, data):

    for match_candidate in data:
        tokens = match_candidate.get("tokens", [])

        match = True
        for token in tokens:
            if token not in filename:
                match = False

        if match:
            return match_candidate.get("value")

    return ""
