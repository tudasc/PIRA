"""
File: BatchSystemHelper.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Needs attention
"""
import lib.Utility as util
import lib.Logging as log

queued_job_filename = './queued_job.tmp'


class BatchSystemJob:
  """
  Class holding the description of a batch system job.
  This class should be independent of the actually used batch system, but still supply enough information
  for the automation process.
  """

  def __init__(self, job_id, b_name, iter_nr, has_instrumentation, cube_file, item_id, build, benchmark, flavor,
               max_iter):
    self.job_id = job_id
    self.benchmark_name = b_name
    self.iter_nr = iter_nr
    self.has_instrumentation = has_instrumentation
    self.cube_file = cube_file
    self.item_id = item_id
    self.build = build
    self.benchmark = benchmark
    self.flavor = flavor
    self.max_iterations = max_iter

  def is_instrumented(self):
    return self.has_instrumentation

  def is_first_iteration(self):
    return self.iter_nr == 0

  def is_iteration(self, number):
    return self.iter_nr == number

  def is_last_iteration(self):
    return self.iter_nr == self.max_iterations

  def get_job_id(self):
    return self.job_id

  def get_benchmark_name(self):
    return self.benchmark_name

  def get_iteration_number(self):
    return self.iter_nr

  def get_cube_file_path(self):
    return self.cube_file

  def get_item_id(self):
    return self.item_id

  def get_build(self):
    return self.build

  def get_benchmark(self):
    return self.benchmark

  def get_flavor(self):
    return self.flavor


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
  return util.is_file(queued_job_filename)


def get_runtime_of_submitted_job(job_id):
  first_line = open('stderr.txt.runner.' + job_id).readline().rstrip()
  values = first_line.split("\t")
  return values[1]


def remove_queued_job_tmp_file():
  util.remove(queued_job_filename)
