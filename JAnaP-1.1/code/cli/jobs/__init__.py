from imdata import *
from trace import *
from shapes import *
from fastclass import *
from jclass import *

def get_job_types():
    import cli.jobs.job
    job_subclasses = cli.jobs.job.BaseJob.__subclasses__()

    job_types = {}

    for job_class in job_subclasses:
        job_types[job_class.job_name] = job_class
    
    return job_types
    
