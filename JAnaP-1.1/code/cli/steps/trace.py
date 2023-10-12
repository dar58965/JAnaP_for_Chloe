import os
import time
import datetime
import platform
import pickle
import json

import cells.waypoints.seeding
import cells.waypoints.perimeter
import cells.images
import cells.images.filter


class Trace:

    def __init__(self, project):
        self.__input_image_directory = project.get_input_image_directory()

        self.__waypoints_artifact_directory = \
            project.get_artifacts_directory("waypoints")

        self.__perimeter_artifact_directory = \
            project.get_artifacts_directory("perimeters")

        self.__system_directory = project.get_system_directory()

        variant = project.get_variant()
        dimensions = project.get_dimensions()

        self.__image_collection = \
            cells.images.get_image_collection(self.__input_image_directory,
                                              variant, dimensions)


    def __trace_perimeter(self, image_path, waypoints):
        # TODO: Abstract cost threshold
        cost_threshold = 5

        image_intensity, image_cost = \
            cells.images.filter.filter_image(image_path, cost_threshold)

        perimeter = \
            cells.waypoints.perimeter.get_perimeter(image_cost, waypoints)

        return perimeter

    def get_operations(self, limit=None):
        """
        Get a list of operations and their status

        This only includes operations that can potentially be done. Any images
        still in the process of being waypointed will be ignored.

        :return:
        """

        operations_list = []
        operations_data = []

        # Caching the file reads makes this twice as fast
        i_w_file_cache = {}

        for image_data_row in self.__image_collection:
            waypoints_base_key = image_data_row["seed_source_image"] + ".tsv"

            waypoints_file = os.path.join(self.__waypoints_artifact_directory,
                                          waypoints_base_key)

            if not os.path.isfile(waypoints_file):
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
                center_r, center_c = waypoints_row.get("geometric_center")

                cell_number = file_root.replace(" ", "") + "--" + str(
                    center_r) + "-" + str(center_c)
                cell_id = file_name.replace(" ", "") + "--" + str(
                    center_r) + "-" + str(center_c)

                perimeter_file_key = cell_id + ".json"

                perimeter_file = \
                    os.path.join(self.__perimeter_artifact_directory,
                                 perimeter_file_key)

                if os.path.isfile(perimeter_file):
                    status = "done"
                else:
                    status = "open"

                if limit is not None and status == "open":
                    current_row = image_data_row.copy()
                    current_row["cell_number"] = cell_number
                    current_row["cell_id"] = cell_id
                    current_row["geometric_center"] = \
                        waypoints_row.get("geometric_center")
                    current_row["waypoints"] = waypoints_row.get("waypoints")

                    operations_data.append(current_row)

                    if len(operations_data) >= limit:
                        return operations_data

                operations_list.append({
                    "cell_id": cell_id,
                    "file_name": file_name,
                    "operation_type": "trace",
                    "status": status
                })

        if limit is not None:
            return operations_data

        return operations_list

    def pop_operations(self, limit=1):
        """
        Do the first operation we come across that is not completed
        """

        operation_rows = self.get_operations(limit=limit)

        for operation_row in operation_rows:
            file_name = operation_row["file_name"]
            image_path = os.path.join(self.__input_image_directory, file_name)

            waypoints = operation_row["waypoints"]

            cell_id = operation_row["cell_id"]
            perimeter_file_key = cell_id + ".json"

            perimeter_file = os.path.join(self.__perimeter_artifact_directory,
                                          perimeter_file_key)

            start = time.time()

            perimeter = self.__trace_perimeter(image_path, waypoints)

            with open(perimeter_file, "w") as f:
                json.dump(perimeter, f)

            elapsed_time = time.time() - start

            self.__write_log_entry(cell_id, file_name, elapsed_time)

    def __write_log_entry(self, cell_id, file_name, elapsed_time):

        log_entry = [
            str(datetime.datetime.now()),
            cell_id,
            file_name,
            str(elapsed_time),
            str(platform.node())
        ]

        operations_log = os.path.join(self.__system_directory, "operations.log")

        with open(operations_log, "a") as f:
            f.writelines("\t".join(log_entry) + '\n')


    def get_operations_by_keys(self, keys):
        pass

