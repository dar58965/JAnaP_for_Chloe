import glob
import os

import cells.waypoints.seeding

import cli.project
#import cli.jobs.trace
#import cli.jobs.shapes
#import cli.jobs.imdata
#import cli.jobs.classify
#import cli.jobs.jclass
#import cli.jobs.jclasssum
#import cli.jobs.edgeseg

# from cli.project import get_dimension_string_match, get_dimension_date_parse
import cli.jobs

class WaypointV1Chain:

    def __init__(self, project):
        self.__project_variant = project.get_variant()
        self.__project_dimensions = project.get_dimensions()
        self.__images_directory = project.get_input_image_directory()
        self.__waypoints_directory = project.get_artifacts_directory("waypoints")
        
        self.jobs = cli.jobs.get_job_types()
        #{
        #    "trace": cli.jobs.trace.Trace(project),
        #    "imdata": cli.jobs.imdata.ImageData(project),
        #    "shapes": cli.jobs.shapes.Shapes(project),
        #    "classedge": cli.jobs.classify.ClassifyEdges(project),
        #    "jclass": cli.jobs.jclass.JunctionClassify(project), 
        #    "jclasssum": cli.jobs.jclasssum.JunctionClassSummarize(project),
        #    "fastclass": cli.jobs.edgeseg.FastSegClassify(project),
        #}

        # Use this for an ordered list of the jobs in the chain
        job_keys = []
        priortized_jobs = sorted(self.jobs.values(), key=lambda x: x.priority)
        for pj in priortized_jobs:
            job_keys.append(pj.job_name)

        self.job_types = job_keys

    def get_entity_map(self):
        """
        file_name (image)
        file_root (image)
        seed_source_image
        cell_number
        cell_id
        variant
        dimensions
        :return:
        """

        return self.__get_entity_map()


    def __get_image_list(self, images_directory):
        image_list = []

        images_directory_glob = images_directory
        if images_directory_glob[-1] != os.sep:
            images_directory_glob = images_directory_glob + os.sep
        images_directory_glob = images_directory_glob + "*"

        for image_file in glob.glob(images_directory_glob):
            file_name = os.path.basename(image_file)

            image_list.append(file_name)

        return image_list


    def __hydrate_image_data(self, image_list, variant, dimensions):
        image_data = []

        variant_values = variant.get("values", [])
        variant_primary_value = variant.get("primary_value", None)

        for file_name in image_list:

            image_variant = None
            image_root = file_name

            for value in variant_values:
                # Filter all variant values out of root
                image_root = image_root.replace(value, "")

                # Determine current image variant value
                if value in file_name:
                    image_variant = value

            seed_source_image = file_name
            if (variant_primary_value not in seed_source_image and
                        variant_primary_value is not None):
                for value in variant_values:
                    seed_source_image = \
                        seed_source_image.replace(value, variant_primary_value)

            image_dimensions = {}

            for key, value in dimensions.iteritems():
                if value["type"] == "String Match":
                    image_dimensions[key] = \
                        cli.project.get_dimension_string_match(file_name,
                                                   value.get("data", []))
                elif value["type"] == "Date Parse":
                    image_dimensions[key] = \
                        cli.project.get_dimension_date_parse(file_name)

            image_data.append({
                "file_name": file_name,
                "file_root": image_root,
                "seed_source_image": seed_source_image,
                "variant": image_variant,
                "dimensions": image_dimensions
            })

        return image_data


    def __hydrate_cell_data_from_waypoints(self, image_data,
                                           include_working=False):
        input_waypoints_directory = self.__waypoints_directory

        cell_data = []

        # Caching the file reads makes this twice as fast
        i_w_file_cache = {}

        for image_data_row in image_data:
            waypoints_base_key = image_data_row["seed_source_image"] + ".tsv"
            waypoints_working_key = image_data_row[
                                        "seed_source_image"] + ".tsv-working"

            waypoints_file = None

            if os.path.isfile(os.path.join(input_waypoints_directory,
                                           waypoints_base_key)):
                waypoints_file = os.path.join(input_waypoints_directory,
                                              waypoints_base_key)
            elif include_working and \
                    os.path.isfile(os.path.join(input_waypoints_directory,
                                                waypoints_working_key)):
                waypoints_file = os.path.join(input_waypoints_directory,
                                              waypoints_working_key)

            # If there are no working or completed waypoints, there's no file
            # to check anyway. Only checking working if include_working is true.
            if waypoints_file is None:
                continue

            if i_w_file_cache.get(waypoints_file) is not None:
                image_waypoints = i_w_file_cache.get(waypoints_file)
            else:
                image_waypoints = cells.waypoints.seeding.load_waypoints(
                    waypoints_file)
                i_w_file_cache[waypoints_file] = image_waypoints

            file_name = image_data_row.get("file_name")
            file_root = image_data_row.get("file_root")

            for waypoints_row in image_waypoints:
                current_row = image_data_row.copy()

                center_r, center_c = waypoints_row.get("geometric_center")

                cell_number = file_root.replace(" ", "") + "--" + str(
                    center_r) + "-" + str(center_c)
                cell_id = file_name.replace(" ", "") + "--" + str(
                    center_r) + "-" + str(center_c)

                current_row["cell_number"] = cell_number
                current_row["cell_id"] = cell_id

                cell_data.append(current_row)

        return cell_data

    def __get_entity_map(self):
        images_directory = self.__images_directory
        variant = self.__project_variant
        dimensions = self.__project_dimensions

        # Get a list of image files
        image_list = self.__get_image_list(images_directory)

        # Hydrate image related data
        image_data = self.__hydrate_image_data(image_list, variant, dimensions)

        # Add cell data
        entity_data = self.__hydrate_cell_data_from_waypoints(image_data)

        return entity_data


def get_chain(project):
    return WaypointV1Chain(project)
