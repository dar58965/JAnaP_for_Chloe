import time
import datetime
import os
import atexit

import multiprocessing

import cli.project
import cli.jobs.job
import cli.output

from controllers import configuration

THREAD_SLEEP_TIME = 5

def process_project_operations(hash, n_threads=None):
    # Currently hashes are just the directory names, might want to support
    # spaces in the future though so I've separated them. They're currently
    # effectively interchangeable.
    # TODO: Abstract
    project_directory_name = hash

    projects_root = configuration.NodeConfiguration.Paths.projects_root
    project_directory = os.path.join(projects_root, project_directory_name)

    project = cli.project.Project(project_directory)

    worker_thread_heartbeat = \
        os.path.join(project.get_system_directory(), "heartbeat")

    # Create heartbeat
    with open(worker_thread_heartbeat, "w") as f:
        f.write(str(datetime.datetime.now()))

    job_manager = cli.jobs.job.JobManager(project)
    job_manager.run_jobs(limit=10, n_threads=n_threads)

    # Create heartbeat
    with open(worker_thread_heartbeat, "w") as f:
        f.write(str(datetime.datetime.now()))

    return project

def process_output_task():
    pass

def process_pending_output(projects_root):
    for project_directory_name in os.listdir(projects_root):
        if not os.path.isdir(os.path.join(projects_root, project_directory_name)):
            continue

        project_directory = os.path.join(projects_root, project_directory_name)

        project = cli.project.Project(project_directory)

        output_directory = project.get_output_directory()

        for output_entry_name in os.listdir(output_directory):
            output_entry = os.path.join(output_directory, output_entry_name)

            if output_entry_name == "do-feature-data":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_feature_data_file(project)
                os.remove(lock_file)
            elif output_entry_name == "do-feature-data-filtered":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_feature_data_file(project, filtered=True)
                os.remove(lock_file)
            elif output_entry_name == "do-path-data":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_path_data_file(project)
                os.remove(lock_file)
            elif output_entry_name == "do-path-data-filtered":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_path_data_file(project, filtered=True)
                os.remove(lock_file)
            
            elif output_entry_name == "do-cell-data-v2":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_cell_data_file(project)
                os.remove(lock_file)

            elif output_entry_name == "do-fastclass-feature-data-filtered":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_feature_data_file_fastclass(project, filtered=True)
                os.remove(lock_file)
            elif output_entry_name == "do-fastclass-feature-data":
                lock_file = output_entry + ".lock"

                os.rename(output_entry, lock_file)
                cli.output.generate_feature_data_file_fastclass(project, filtered=False)
                os.remove(lock_file)


def delete_fw_lock(projects_root):
    print "Cleaning up foreground worker lock..."

    fw_lock_file = os.path.join(projects_root, "fw-lock")

    if os.path.isfile(fw_lock_file):
        os.remove(fw_lock_file)


def update_fw_lock(projects_root):
    fw_lock_file = os.path.join(projects_root, "fw-lock")

    with open(fw_lock_file, "w") as f:
        f.write(str(time.time()))


def check_fw_lock(projects_root):
    fw_lock_file = os.path.join(projects_root, "fw-lock")

    if os.path.isfile(fw_lock_file):
        with open(fw_lock_file, "r") as f:
            fw_t_raw = f.read()

        fw_t = float(fw_t_raw)

        if abs(time.time() - fw_t) < 600:
            return True
        else:
            # fw_lock_file timeout is 600s, remove it if it's stale
            os.remove(fw_lock_file)

    return False


def process_operations(projects_root, n_threads=None):
    for project_directory_name in os.listdir(projects_root):
        if not os.path.isdir(os.path.join(projects_root, project_directory_name)):
            continue

        hash = project_directory_name

        process_project_operations(hash, n_threads)


def cleanup_foreground():
    projects_root = configuration.NodeConfiguration.Paths.projects_root

    delete_fw_lock(projects_root)


def foreground_thread():
    # Attempt to remove the fw lock file on exit - this isn't required but is
    # nice. If it does not get removed, it will be removed if it is older than
    # 600 seconds by the background thread spawned by the web application
    # atexit.register(cleanup_foreground())

    num_cores = multiprocessing.cpu_count()
    n_threads = int(num_cores / 2)
    if n_threads < 1:
        n_threads = None

    # Temp Speed +
    n_threads = n_threads + 2
    
    projects_root = configuration.NodeConfiguration.Paths.projects_root

    while True:
        # Create foreground lock
        update_fw_lock(projects_root)

        print "%s: Starting Thread Iteration" % str(datetime.datetime.now())

        process_operations(projects_root, n_threads)

        time.sleep(THREAD_SLEEP_TIME)


def background_thread():
    projects_root = configuration.NodeConfiguration.Paths.projects_root

    while True:
        print "%s: Starting Thread Iteration" % str(datetime.datetime.now())

        # Handle file generation
        process_pending_output(projects_root)

        if check_fw_lock(projects_root) == False:
            print "No fw lock"
            process_operations(projects_root)
            time.sleep(THREAD_SLEEP_TIME)
        else:
            print "Sleeping 120s: fast-worker has lock currently"
            time.sleep(120)


