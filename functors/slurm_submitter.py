
slurm_binary = 'sbatch'
slurm_queye = 'squeue --format="%i %j"'


def dispatch(list_of_files, **kwargs):
    util = kwargs['util']
    rpj = kwargs['runs_per_job']
    dependent = kwargs['dependent']

    for file in list_of_files:
        job_id = -1 # Keeping track of job dependencies

        for i in xrange(0, rpj):
            if dependent:
                job_id = submit_with_dependencies(util, file, job_id)
            else:
                submit(util, file)


def submit_with_dependencies(util, run_script, job_id):
    command = slurm_binary + ' '
    if job_id < 0:
        command += run_script
    else:
        command += '-afterok:' + str(job_id) + ' ' + run_script

    util.shell(command, dry=True)


def submit(util, run_script):
    command = slurm_binary + ' ' + run_script
    util.shell(command, dry=True)


#
# Typical slurm options:
#   - number of submissions per job
#   - dependencies between the individual repetition of job
#   - array jobs
#   - ?
