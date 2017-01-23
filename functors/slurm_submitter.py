
slurm_binary = 'sbatch'
slurm_queye = 'squeue --format="%i %j"'


def dispatch(list_of_tuples, **kwargs):
    util = kwargs['util']
    rpj = kwargs['runs_per_job']
    dependent = kwargs['dependent']

    for run_tuple in list_of_tuples:
        file_name = run_tuple[1]
        job_id = initial_dependency(util, run_tuple[0])

        for i in xrange(0, rpj):
            if dependent:
                job_id = submit_with_dependencies(util, file_name, job_id)
            else:
                submit(util, file_name)


def initial_dependency(util, benchmark_flavor):
    command = slurm_queye + ' | grep ' + benchmark_flavor[0] + '.'
    shell_output = util.shell(command, dry=True)
    out_list = shell_output.split('\n')
    ids = []
    for entry in out_list:
        if len(entry) == 0:
            continue
        job_id = entry.split(' ')[0]
        ids.append(int(job_id))

    if len(ids) == 0:
        return -1

    ids.sort()
    return ids.reverse()[0]


def submit_with_dependencies(util, run_script, job_id):
    command = slurm_binary + ' '
    if job_id < 0:
        command += run_script
    else:
        command += '-afterok:' + str(job_id) + ' ' + run_script

    shell_output = util.shell(command, dry=True)
    return extract_job_id(shell_output)


def extract_job_id(shell_string):
    """
    This function extracts the job id from the output of sbatch on the Lichtenberg cluster.
    :param shell_string:
    :return: job_id
    """
    delim_left = shell_string.rfind('job')
    delim_right = shell_string.find('\n', delim_left + 4)
    job_id = shell_string[delim_left + 4 : delim_right] # Account for 'job' in left delimiter

    return int(job_id)


def submit(util, run_script):
    command = slurm_binary + ' ' + run_script
    util.shell(command, dry=True)


#
# Typical slurm options:
#   - number of submissions per job
#   - dependencies between the individual repetition of job
#   - array jobs
#   - ?
