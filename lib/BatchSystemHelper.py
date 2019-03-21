import lib.Utility as util
import lib.Logging as log

queued_job_filename = './queued_job.tmp'


class BatchSystemJob:
  """
  Class holding the description of a batch system job.
  This class should be independent of the actually used batch system, but still supply enough information
  for the automation process.
  """

  def __init__(s, job_id, b_name, iter_nr, has_instrumentation, cube_file, item_id, build, benchmark, flavor,
               max_iter):
    s.job_id = job_id
    s.benchmark_name = b_name
    s.iter_nr = iter_nr
    s.has_instrumentation = has_instrumentation
    s.cube_file = cube_file
    s.item_id = item_id
    s.build = build
    s.benchmark = benchmark
    s.flavor = flavor
    s.max_iterations = max_iter

  def is_instrumented(s):
    return s.has_instrumentation

  def is_first_iteration(s):
    return s.iter_nr == 0

  def is_iteration(s, number):
    return s.iter_nr == number

  def is_last_iteration(s):
    return s.iter_nr == s.max_iterations

  def get_job_id(s):
    return s.job_id

  def get_benchmark_name(s):
    return s.benchmark_name

  def get_iteration_number(s):
    return s.iter_nr

  def get_cube_file_path(s):
    return s.cube_file

  def get_item_id(s):
    return s.item_id

  def get_build(s):
    return s.build

  def get_benchmark(s):
    return s.benchmark

  def get_flavor(s):
    return s.flavor


def create_batch_queued_temp_file(job_id, benchmark_name, iterationNumber, DBIntVal, DBCubeFilePath, itemID,
                                  build, benchmark, flavor):
  try:
    with open(queued_job_filename, 'w') as myfile:
      myfile.write(str(job_id) + '\n')
      myfile.write(benchmark_name + '\n')
      myfile.write(str(iterationNumber) + '\n')
      myfile.write(str(DBIntVal) + '\n')
      myfile.write(DBCubeFilePath + '\n')
      myfile.write(itemID + '\n')
      myfile.write(build + '\n')
      myfile.write(benchmark + '\n')
      myfile.write(flavor + '\n')
      myfile.close()

  except:
    log.get_logger().log('Unable to create batch system temporary file. Exit.', level='error')
    exit(1)


def read_batch_queued_job():
  if check_queued_job():
    lines = [line.rstrip('\n') for line in open(queued_job_filename)]
    return lines
  else:
    log.get_logger().log('Batch system queued file does not exist. Exit.', level='error')
    exit(1)


def check_queued_job():
  return util.check_file(queued_job_filename)


def get_runtime_of_submitted_job(job_id):
  first_line = open('stderr.txt.runner.' + job_id).readline().rstrip()
  values = first_line.split("\t")
  return values[1]


def remove_queued_job_tmp_file():
  util.remove(queued_job_filename)
