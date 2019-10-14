import sqlite3 as db
import lib.Logging as log
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt


class database:

  def __init__(self, conf_db_name):
    try:
      self.conn = db.connect(conf_db_name)
    except Exception as e:
      log.get_logger().log(e.message, level='warn')
    return None

  def create_cursor(self, conn):
    try:
      cursor = conn.cursor()
      return cursor
    except Exception as e:
      log.get_logger().log(e.message, level='warn')

  def create_table(self, cursor, table_name):
    try:
      cursor.execute(table_name)
    except Exception as e:
      log.get_logger().log(e.message, level='warn')

  def insert_data_application(self, cursor, values):
    #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
    sql = ''' INSERT INTO Application(AppID,App_Name,Global_Flavor,Global_Submitter)
              VALUES(?,?,?,?) '''

    cursor.execute(sql, values)
    self.conn.commit()

  def insert_data_builds(self, cursor, values):
    #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
    sql = ''' INSERT INTO Builds(BuildID,Build_Name,Prefix,Flavors,AppName)
              VALUES(?,?,?,?,?) '''

    cursor.execute(sql, values)
    self.conn.commit()

  def insert_data_items(self, cursor, values):
    #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
    sql = ''' INSERT INTO Items(ItemID,Item_Name,Inst_Analysis_Functor_Path,Builders_Funtor_Path,Run_Args,Runner_Functor_Path,Submitter_Functor_Path,Exp_Data_Dir_Base_Path,BuildName)
              VALUES(?,?,?,?,?,?,?,?,?) '''

    cursor.execute(sql, values)
    self.conn.commit()

  def insert_data_experiment(self, cursor, values):
    #cursor.execute("INSERT INTO "+table_name+" VALUES (?,?,?)")
    sql = ''' INSERT INTO Experiment(Experiment_ID,BenchmarkName,Iteration_No,IsWithInstrumentation,CubeFilePath,Runtime,Item_ID)
              VALUES(?,?,?,?,?,?,?) '''
    cursor.execute(sql, values)
    self.conn.commit()
