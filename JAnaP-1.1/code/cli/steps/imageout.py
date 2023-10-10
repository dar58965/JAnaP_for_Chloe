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


class ImageDataGenerator:

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


    def __get_image_data(self):
        pass

    def get_operations(self, limit=None):
        """
        Can only operate on images with complete perimeter sets

        :param limit:
        :return:
        """

        pass

