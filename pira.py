import argparse
import lib.Logging as log
import lib.Pira as pira
'''
trying DB

database = db("db_file")
cur = database.create_cursor(database.conn)
database.create_table(cur,tables.sql_create_application_table)
database.create_table(cur,tables.sql_create_builds_table)
database.create_table(cur,tables.sql_create_items_table)
database.create_table(cur,tables.sql_create_experiment_table)

app = ('app_1','globa_falv_1','global_sub_1')
database.insert_data_application(cur,app)
cur.execute("SELECT * FROM Application" )
rows = cur.fetchall()

for row in rows:
    print(row)

'''

parser = argparse.ArgumentParser()
parser.add_argument('config', help='The configuration json file.')
parser.add_argument('--version', help='Which config file version to use', choices=[1, 2], default=1, type=int)
parser.add_argument('--tape', help='Path to tape file to dump.')
parser.add_argument('--runtime-filter', help='Use run-time filtering', default=False, action='store_true')
parser.add_argument('--num-reps', help='Number of iterations run', default=3, type=int)
group = parser.add_argument_group('ExP')
group.add_argument(
    '--extrap-dir', help='The base directory where extra-p folder structure is placed', type=str, default='')
group.add_argument('--extrap-prefix', help='The prefix in extra-p naming scheme', type=str)
args = parser.parse_args()

try:
  log.get_logger().log('Starting', level='debug')
  pira.main(args)

finally:
  if args.tape is not None:
    log.get_logger().dump_tape(args.tape)
  else:
    log.get_logger().dump_tape('tape.tp')

log.get_logger().log('End of process')
log.get_logger().show_perf()
