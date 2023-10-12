import os
import datetime
import json
import platform
import time
import traceback

from joblib import Parallel, delayed
import multiprocessing

class BaseJob(object):
    pass

def unwrap_job(project, entity_map, jt, jk):
    jm = JobManager(project, entity_map)

    return jm.parallel_run_job(jt, jk)

class JobManager:

    def __init__(self, project, entity_map=None):
        self.project = project
        self.chain = project.get_chain()
        self.__system_directory = project.get_system_directory()

        self.__entity_map = entity_map

    def get_job_types(self):
        return self.chain.job_types

    def get_job_headers(self, job_type=None, key_filter=None):
        """
        Get all of the job headers for this job type

        Job Header:
            job_key
            job_type
            status
            data
        :return:
        """

        if self.__entity_map is None:
            entity_map = self.chain.get_entity_map()
            self.__entity_map = entity_map
        else:
            entity_map = self.__entity_map

        job_headers = []

        for jt in self.chain.job_types:
            if job_type is None or job_type == jt:
                jh_list = self.chain.jobs[jt](self.project).get_job_headers(entity_map)
                job_headers.extend(jh_list)

        return job_headers

    def get_job_metrics(self, job_type=None):
        job_metrics = {}

        operations_log = os.path.join(self.__system_directory, "operations.log")

        if os.path.isfile(operations_log):
            with open(operations_log, "r") as f:
                log_entries = f.readlines()
        else:
            log_entries = []
        
        for jt in self.chain.job_types:
            if job_type is None or job_type == jt:
                total_cpu_time = 0.0
                job_count = 0

                for log_entry in log_entries:
                    try:
                        log_data = json.loads(log_entry)

                        if log_data.get("job_type") == jt and \
                                        log_data.get("runtime") is not None:
                            total_cpu_time += float(log_data.get("runtime"))
                            job_count += 1
                    except:
                        pass

                if job_count > 0:
                    job_metrics[jt] = {
                        "avg_time": round(total_cpu_time / float(job_count), 4),
                        "cpu_time": round(total_cpu_time, 4)
                    }
                else:
                    job_metrics[jt] = {
                        "avg_time": round(0, 4),
                        "cpu_time": round(total_cpu_time, 4)
                    }

        if job_type is None:
            return job_metrics
        else:
            return job_metrics.get(job_type)

    def __check_open_job_exception(self, job_type, job_key):
        """
        Check if there is currently an open exception for a job

        :return:
        """
        je_directory = os.path.join(self.__system_directory, "job_errors")
        je_exception_key = job_type + "--" + job_key + ".json"
        je_exception_file = os.path.join(je_directory, je_exception_key)

        return os.path.isfile(je_exception_file)

    def __write_job_exception(self, job_type, job_key, message, stacktrace):
        je_directory = os.path.join(self.__system_directory, "job_errors")

        if not os.path.isdir(je_directory):
            os.makedirs(je_directory)

        je_exception_key = job_type + "--" + job_key + ".json"

        je_exception_file = os.path.join(je_directory, je_exception_key)

        exception_data = {
            "ts": str(datetime.datetime.now()),
            "job_type": job_type,
            "job_key": job_key,
            "node": str(platform.node()),
            "message": message,
            "traceback": stacktrace
        }

        with open(je_exception_file, "w") as f:
            f.writelines(json.dumps(exception_data))


    def __write_log_entry(self, job_type, job_key, elapsed_time, result_data):
        log_entry = {
            "ts": str(datetime.datetime.now()),
            "job_type": job_type,
            "job_key": job_key,
            "runtime": str(elapsed_time),
            "node": str(platform.node())
        }

        for key, value in result_data.iteritems():
            log_entry[key] = value

        operations_log = os.path.join(self.__system_directory,
                                      "operations.log")

        log_entry_row = json.dumps(log_entry)

        with open(operations_log, "a") as f:
            f.writelines(log_entry_row + '\n')

    def __run_job(self, job_type, job_key):
        start = time.time()

        if self.__entity_map is None:
            entity_map = self.chain.get_entity_map()
            self.__entity_map = entity_map
        else:
            entity_map = self.__entity_map

        try:
            result = self.chain.jobs[job_type](self.project).do_job(entity_map, job_key)

        except Exception as e:
            message = str(e)
            stacktrace = traceback.format_exc()

            self.__write_job_exception(job_type, job_key, message, stacktrace)
        else:
            elapsed_time = time.time() - start

            self.__write_log_entry(job_type, job_key, elapsed_time, result)

        return True

    def parallel_run_job(self, job_type, job_key):
        print "\t\t", "start", job_type, job_key
        result = self.__run_job(job_type, job_key)
        print "\t\t", "finish", job_type, job_key

        return result

    def __multiprocess(self, job_arguments, n_threads):
        num_cores = multiprocessing.cpu_count()

        print ("\tRunning Jobs: %s jobs spread across %s threads / %s cores" %
               (str(len(job_arguments)), str(n_threads), str(num_cores)))

        start = time.time()

        results = Parallel(n_jobs=n_threads)(
            delayed(unwrap_job)(self.project, self.__entity_map, jt, jk)
            for jt, jk in job_arguments)

        print ("\t-- Done: %s" % str(time.time() - start))

    def run_jobs(self, limit=5, n_threads=None):
        # There's a bit of a race condition here. The only time this is really
        # concerning is if an output job is running. To get around this we
        # separate the output jobs from the compute jobs

        job_headers = self.get_job_headers()

        job_count = 0

        job_settings = self.project.get_job_settings()

        job_arguments = []

        for job_header in job_headers:
            if job_header.get("status") != "open":
                continue

            if not job_settings[job_header["job_type"]]["is_active"]:
                continue


            if self.__check_open_job_exception(job_header["job_type"],
                                               job_header["job_key"]):
                #print ("\tSkipping Job: %s-%s" % (job_header["job_type"],
                #                                  job_header["job_key"]))

                continue

            if n_threads is None:
                self.__run_job(job_header["job_type"], job_header["job_key"])
            else:
                job_arguments.append((job_header["job_type"], job_header["job_key"]))
            job_count += 1

            if limit is not None and job_count >= limit:
                break

        if n_threads is not None:
            self.__multiprocess(job_arguments, n_threads)

    def run_job_debugger(self, job_type, job_key):
        # runs a job without marking it as done
        if self.__entity_map is None:
            entity_map = self.chain.get_entity_map()
            self.__entity_map = entity_map
        else:
            entity_map = self.__entity_map

        result = self.chain.jobs[job_type](self.project).do_job(entity_map, job_key)

