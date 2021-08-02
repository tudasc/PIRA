"""
File: Exporter.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module that implements various exporters, e.g., CSV-export.
"""

import csv

import lib.Logging as L
import typing

from lib.Exception import PiraException
from lib.Measurement import RunResult


class CSVExporter:

  def __init__(self, name):
    if name is None:
      raise RuntimeError('name argument for CSVExport-ctor must not be None')
    self._name = name
    self._exports = {}

  def get_name(self):
    return self._name

  def add_new_export(self, name, values):
    if name is None:
      raise RuntimeError('name argument needs to be not None')
    if values is None:
      raise RuntimeError('values argument needs to be not None')
    if name in self._exports:
      raise KeyError('Key already exists')

    self._exports[name] = values

  def add_export(self, name, values):
    self._exports[name] += values

  def export(self, file_name, keys=None):
    if keys is None:
      keys = [str(x) for x in self._exports.keys()]

    L.get_logger().log('[CSVExporter::export] Keys to export: ' + str(keys))


class RunResultExporter:

  def __init__(self):
    self.rows = []
    self.width = 0

  def add_row(self, run_type: str, rr: RunResult):
    # first element is type of run
    row = [run_type]
    if(len(rr.get_accumulated_runtime()) != len(rr.get_nr_of_iterations())):
      raise PiraException("Could not add row to RunResultExporter; lengths of accumulated runtimes and number of iterations do not match")
    else:
      # assemble row content
      for i in range(len(rr.get_accumulated_runtime())):
        row.append(rr.get_accumulated_runtime()[i])
        row.append(rr.get_nr_of_iterations()[i])

      # add row to table
      self.rows.append(row)

      # check if width attribute needs to be updated
      if(len(row) > self.width):
        self.width = len(row)

  def export(self, file_name: str, dialect='unix'):
    with open(file_name, 'w', newline='') as csvfile:

      writer = csv.writer(csvfile, dialect)

      # construct table header
      fieldnames = ['Type of Run']
      for i in range((self.width - 1) // 2):
        fieldnames.append('Accumulated Runtime')
        fieldnames.append('Number of Runs')

      # write table header as first row
      writer.writerow(fieldnames)

      # write rows
      writer.writerows(self.rows)



class PiraRuntimeExporter:

  class MetaInformationProvider:
    
    def __init__(self, str_for_average: str, str_for_median: str, str_for_stdev: str):
      self._average = str_for_average
      self._median = str_for_median
      self._stdev = str_for_stdev

    def get_average(self, unused_void, unused_void_2):
      return self._average

    def get_median(self, unused_void,unused_void_2):
      return self._median

    def get_stdev(self,unused_void, unused_void_2):
      return self._stdev

    def get_num_data_sets(self):
      return 1

  def __init__(self):
    self._iteration_data = [('Data', PiraRuntimeExporter.MetaInformationProvider('Average', 'Median', 'Stdev'))]

  def add_iteration_data(self, name: str, rt_info) -> None:
    self._iteration_data.append( (name, rt_info) )

  def export(self, file_name: str, dialect='unix'):
    with open(file_name, 'w', newline='') as csvfile:

      writer = csv.writer(csvfile, dialect)

      writer_data = []
      for el in self._iteration_data:
        for nd in range(0,el[1].get_num_data_sets()):
          writer_data.append(el[0])
      writer.writerow(writer_data)

      writer_data = []
      for el in self._iteration_data:
        for nd in range(0,el[1].get_num_data_sets()):
          writer_data.append(el[1].get_average(0,nd))
      writer.writerow(writer_data)

      writer_data = []
      for el in self._iteration_data:
        for nd in range(0,el[1].get_num_data_sets()):
          writer_data.append(el[1].get_median(0,nd))
      writer.writerow(writer_data)

      writer_data = []
      for el in self._iteration_data:
        for nd in range(0,el[1].get_num_data_sets()):
          writer_data.append(el[1].get_stdev(0,nd))
      writer.writerow(writer_data)

