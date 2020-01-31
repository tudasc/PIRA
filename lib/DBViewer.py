"""
File: DBViewer.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: @deprecated Module to inspect the database entries.
"""

import sys
sys.path.append('..')
import sqlite3 as dbviewer
from lib.ConfigurationLoader import ConfigurationLoader as Conf
from sqlite3 import Error

config_loader = Conf()
configuration = config_loader.load_conf("../examples/hpcg.json")
try:
  conn = dbviewer.connect('../BenchPressDB')
  c = conn.cursor()
except Error as e:
  print(e)

for build in configuration.builds:
  for row in c.execute("SELECT App_Name FROM Application WHERE App_Name=?", (build,)):
    print("\n")
    print("Build Name")
    print("------------------------------------------------------------------------")
    print(row)
    print("------------------------------------------------------------------------")
    for item in configuration.builds[build]['items']:
      benchmark_name = configuration.get_benchmark_name(item)
      print("\n")
      print("Item Name")
      print("------------------------------------------------------------------------")
      print(item)
      print("------------------------------------------------------------------------")
      print("\n")
      print("-------------------------------------------------------------------------------------")
      print("BenchmarkName     Iteration_No     IsWithInstrumentation     CubeFilePath    Runtime")
      print("-------------------------------------------------------------------------------------")
      for row in c.execute(
          "SELECT BenchmarkName,Iteration_No,IsWithInstrumentation,CubeFilePath,Runtime FROM Experiment WHERE "
          "BenchmarkName=?", (benchmark_name[0],)):
        print(row)
