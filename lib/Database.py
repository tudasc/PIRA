"""
File: Database.py
Author: JP Lehr, Sachin Manawadi 
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module to run the target software.
"""

import sys
sys.path.append('..')

import lib.FunctorManagement as fm
import lib.Utility as u
import lib.tables as pirasql
from lib.Exception import PiraException

import sqlite3 as db


class DBException(PiraException):

  def __init__(self, message):
    super().__init__(message)


class DBManager:
  """ 
  This class is used to communicate with PIRA DB.
  """

  class DBImpl:
    """
    Inner class to implement singleton pattern.

    Takes care of the actual database connection.
    """

    def __init__(self, name):
      self.conn = None
      self.cursor = None
      try:
        self.conn = db.connect(name)
      except Exception:
        raise DBException('Error in creating the database / connection')

    def create_cursor(self):
      try:
        self.cursor = self.conn.cursor()
        return self.cursor
      except Exception:
        raise DBException('Error in creating cursor')

    def create_table(self, table_name):
      try:
        self.cursor.execute(table_name)
      except Exception:
        raise DBException('Problem creating tables')

    def insert_data_application(self, values):
      self.create_table(pirasql.create_application_table)
      sql = ''' INSERT INTO Application(AppID,App_Name,Global_Flavor,Global_Submitter)
                VALUES(?,?,?,?) '''

      self.cursor.execute(sql, values)
      self.conn.commit()

    def insert_data_builds(self, values):
      self.create_table(pirasql.create_builds_table)
      sql = ''' INSERT INTO Builds(BuildID,Build_Name,Prefix,Flavors,AppName)
                VALUES(?,?,?,?,?) '''

      self.cursor.execute(sql, values)
      self.conn.commit()

    def insert_data_items(self, values):
      self.create_table(pirasql.create_items_table)
      sql = ''' INSERT INTO Items(ItemID,Item_Name,Inst_Analysis_Functor_Path,Builders_Funtor_Path,Run_Args,Runner_Functor_Path,Submitter_Functor_Path,Exp_Data_Dir_Base_Path,BuildName)
                VALUES(?,?,?,?,?,?,?,?,?) '''

      self.cursor.execute(sql, values)
      self.conn.commit()

    def insert_data_experiment(self, values):
      self.create_table(pirasql.create_experiment_table)
      sql = ''' INSERT INTO Experiment(Experiment_ID,BenchmarkName,Iteration_No,IsWithInstrumentation,CubeFilePath,Runtime,Item_ID)
                VALUES(?,?,?,?,?,?,?) '''
      self.cursor.execute(sql, values)
      self.conn.commit()

    def prep_db_for_build_item_in_flavor(self, config, build, item, flavor):
      """Generates all the necessary build work to write to the db.
  
      :config: PIRA configuration
      :build: the build
      :item: current item
      :flavor: current flavor
      :returns: unique ID for current item
  
      """
      build_tuple = (u.generate_random_string(), build, '', flavor, build)
      self.insert_data_builds(build_tuple)
      # XXX My implementation returns the full path, including the file extension.
      #     In case something in the database goes wild, this could be it.
      func_manager = fm.FunctorManager()
      analyse_functor = func_manager.get_analyzer_file(build, item, flavor)
      build_functor = func_manager.get_builder_file(build, item, flavor)
      run_functor = func_manager.get_runner_file(build, item, flavor)
      # TODO implement the get_submitter_file(build, item, flavor) method!

      benchmark_name = config.get_benchmark_name(item)
      submitter_functor = config.get_runner_func(build, item) + '/slurm_submitter_' + benchmark_name + flavor
      exp_dir = config.get_analyser_exp_dir(build, item)

      db_item_id = u.generate_random_string()
      db_item_data = (db_item_id, benchmark_name, analyse_functor, build_functor, '', run_functor, submitter_functor,
                      exp_dir, build)
      self.insert_data_items(db_item_data)

      return db_item_id

    def enter_run_data(self, unique_id: str, item_name: str, iteration_no: int, is_instrumented_run: bool,
                       path_to_cube: str, runtime: float, db_item_id) -> None:
      pass

  #### END OF INNER CLASS ###

  db_name = '_pira'
  db_ext = 'sqlite'

  instance = None

  def __init__(self, dbname):
    if not DBManager.instance:
      DBManager.instance = DBManager.DBImpl(dbname)

  def __getattr__(self, name):
    return getattr(self.instance, name)
