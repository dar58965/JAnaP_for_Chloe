import os
import sys
import inspect

import controllers
import controllers.configuration


# Get the default configuration file location
absolute_location = os.path.abspath(inspect.getfile(inspect.currentframe()))
absolute_path = os.path.dirname(absolute_location)
absolute_root_path = os.path.abspath(os.path.join(absolute_path, ".."))

# Load configuration from default location
local_config_file = os.path.join(absolute_root_path, "node.conf.local")
if os.path.isfile(local_config_file):
    config_file = local_config_file
else:
    config_file = os.path.join(absolute_root_path, "node.conf")
controllers.configuration.parse_config_file(config_file)

# Add the code path to the system path
code_dir = controllers.configuration.NodeConfiguration.Paths.code_root
sys.path.insert(0, code_dir)

from controllers import configuration
from controllers.shared import get_project

import cli.jobs.job

from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(project_hash=None, job_type=None, job_hash=None, job_search=None)
parser.add_option("--project", action="store",
                  dest="project_hash", metavar="HASH")
parser.add_option("--job", action="store",
                  dest="job_type", metavar="NAME")
parser.add_option("--job_hash", action="store",
                  dest="job_hash", metavar="HASH")
parser.add_option("--job-search", action="store",
                  dest="job_search")

(options, args) = parser.parse_args()


projects_root = configuration.NodeConfiguration.Paths.projects_root

# List available projects and then quit if no project is specified
if options.project_hash is None:
    print "Available project hashes: "
    for project_directory_name in os.listdir(projects_root):
        if not os.path.isdir(os.path.join(projects_root, project_directory_name)):
            continue
        hash = project_directory_name

        print "    - " + hash

    exit()

else:
    project = get_project(options.project_hash)
    job_manager = cli.jobs.job.JobManager(project)

    # List available jobs
    if options.job_type is None:
        print "Registered job types: "

        job_types = job_manager.get_job_types()

        for job_type in job_types:
            print "    - " + job_type

    elif options.job_type is not None and options.job_hash is None:
        job_headers = job_manager.get_job_headers(job_type=options.job_type)

        if options.job_search is not None:
            for j_idx in range(0, len(job_headers)):
                if options.job_search in job_headers[j_idx].get("job_key"):
                    print "   - [%s] => %s" % (str(j_idx), job_headers[j_idx])
        else:
            oj_counter = 0

            print "Ready Jobs (next 20):"
            for j_idx in range(0, len(job_headers)):
                if job_headers[j_idx].get("status") == "open":
                    print "   - [%s] => %s" % (str(j_idx), job_headers[j_idx])
                    oj_counter += 1

                if oj_counter >= 20:
                    break

            print len(job_headers)

    else:
        job_headers = job_manager.get_job_headers(job_type=options.job_type)

        if options.job_hash.isdigit():
            job_idx = int(options.job_hash)
            job_header = job_headers[job_idx]

            print "Job Header: ", job_header
            job_manager.run_job_debugger(job_header["job_type"],
                                         job_header["job_key"])

        else:
            pass
        pass
