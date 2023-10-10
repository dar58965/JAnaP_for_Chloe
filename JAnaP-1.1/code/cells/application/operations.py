import os

import configuration as app_config


def get_project_headers():
    """
    Returns a project header for each project located in project directory

    Header dictionary format:

        {
            "project-name" => {
                "directory" => "/.../.../"
            }
        }

    :return:
    """

    project_root = app_config.data_path.project_root

    project_headers = {}

    for project_rel_path in os.walk(os.path.join(project_root, '.')).next()[1]:
        project_name = project_rel_path
        project_directory = \
            os.path.abspath(os.path.join(project_root, project_rel_path))
        project_directory = os.path.join(project_directory, '.')

        project_headers[project_name] = {
            "directory": project_directory
        }

    return project_headers

def setup():
    pass


def hydrate():
    pass


def clean():
    pass
