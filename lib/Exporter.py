"""
File: Exporter.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module that implements various exporters, e.g., CSV-export.
"""

import lib.Logging as L
import typing



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

