from optparse import OptionParser, OptionGroup


OPTYPE_APPLICATION = 100
APPLICATION_SETUP = (OPTYPE_APPLICATION, 10)
APPLICATION_HYDRATE = (OPTYPE_APPLICATION, 20)
APPLICATION_PROJECT_CREATE = (OPTYPE_APPLICATION, 30)
APPLICATION_PROJECT_LIST = (OPTYPE_APPLICATION, 40)

OPTYPE_PROJECT = 200
PROJECT_SYNC = (OPTYPE_PROJECT, 10)
PROJECT_SETUP = (OPTYPE_PROJECT, 20)
PROJECT_CLEAN = (OPTYPE_PROJECT, 30)
PROJECT_ALL = (OPTYPE_PROJECT, 40)

def get_parser(default_app_config):
    parser = OptionParser()

    parser.set_defaults(app_config_file=default_app_config)

    # General Options
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", default=False,
                      help="")


    # Application Level Operations
    group = OptionGroup(parser, "Application Operations")
    group.add_option("--hydrate", action="store_const",
                     dest="operation", const=APPLICATION_HYDRATE,
                     help="")
    group.add_option("--project-create", action="store_const",
                     dest="operation", const=APPLICATION_PROJECT_CREATE,
                     help="")
    group.add_option("--list", action="store_const",
                     dest="operation", const=APPLICATION_PROJECT_LIST,
                     help="")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Project Operations")
    group.add_option("-p", "--project", action="store",
                     dest="project", default=None,
                     help="Select project")
    group.add_option("--setup", action="store_const",
                     dest="operation", const=PROJECT_SETUP,
                     help="")
    group.add_option("--clean", action="store_const",
                     dest="operation", const=PROJECT_CLEAN,
                     help="")
    group.add_option("--all", action="store_const",
                     dest="operation", const=PROJECT_ALL,
                     help="")
    parser.add_option_group(group)

    return parser
