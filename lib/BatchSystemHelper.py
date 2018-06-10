import Utility as util
import Logging as log

queued_job_filename = './queued_job.tmp'


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
  print values[1]
  return values[1]


def remove_queued_job_tmp_file():
  util.remove(queued_job_filename)
