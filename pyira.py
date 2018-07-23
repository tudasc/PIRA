import lib.Runner as runner
import argparse
from lib.db import database as db
import lib.tables as tables
import lib.Logging as log

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
args = parser.parse_args()

runner.run(args.config)

log.get_logger().log('End of process')
log.get_logger().show_perf()
