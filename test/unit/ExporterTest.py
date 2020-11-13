"""
File: ExporterTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Unit test for Exporter module.
"""

import unittest

import lib.Exporter as E
import lib.Measurement as M
import os

class TestCSVExporter(unittest.TestCase):
  
  def test_init_None(self):
    with self.assertRaises(RuntimeError) as ex_cm:
      exporter = E.CSVExporter(None)

    exception = ex_cm.exception
    self.assertEqual(str(exception), 'name argument for CSVExport-ctor must not be None')

  def test_init(self):
    exporter = E.CSVExporter('test exporter')
    self.assertIsNotNone(exporter)
    self.assertEqual(exporter.get_name(), 'test exporter')

  def test_add_new_export_None_arguments(self):
    exporter = E.CSVExporter('TE')
    with self.assertRaises(RuntimeError) as e_cm:
      exporter.add_new_export(None, [1,2])
    
    exception = e_cm.exception
    self.assertEqual(str(exception), 'name argument needs to be not None')

    with self.assertRaises(RuntimeError) as e_cm:
      exporter.add_new_export('key', None)

    exception = e_cm.exception
    self.assertEqual(str(exception), 'values argument needs to be not None')

  def test_add_new_export(self):
    exporter = E.CSVExporter('TE')
    exporter.add_new_export('a', [1])
    self.assertTrue('a' in exporter._exports)
    self.assertEqual(exporter._exports['a'], [1])

  def test_add_new_export_key_exists(self):
    exporter = E.CSVExporter('TE')
    exporter.add_new_export('a', [1])
    with self.assertRaises(KeyError) as e_cm:
      exporter.add_new_export('a', [2])

    ex = e_cm.exception
    # This seems to be an incosistency in Python (?), as the other exceptions do not show this sort of behavior
    self.assertEqual(str(ex), "'Key already exists'")

  def test_add_export_key_error(self):
    exporter = E.CSVExporter('TE')
    with self.assertRaises(KeyError) as e_cm:
      exporter.add_export('a', [2])

    ex = e_cm.exception
    self.assertEqual(str(ex), "'a'")

  def test_add_export(self):
    exporter = E.CSVExporter('TE')
    exporter.add_new_export('a', [1])
    exporter.add_export('a', [2])
    self.assertEqual(exporter._exports['a'], [1, 2])

class TestRunResultExporter(unittest.TestCase):
  def test_init(self):
    rre = E.RunResultExporter()
    self.assertIsNotNone(rre)

  def test_add_row(self):
    rre = E.RunResultExporter()
    rr = M.RunResult(1,1)
    rr.add_values(2,2)
    rre.add_row("test", rr)
    self.assertEqual(len(rre.rows), 1)
    self.assertEqual(len(rre.rows[0]), 5)
    self.assertEqual(rre.rows[0][0], "test")
    self.assertEqual(rre.rows[0][1], 1)
    self.assertEqual(rre.rows[0][2], 1)
    self.assertEqual(rre.rows[0][3], 2)
    self.assertEqual(rre.rows[0][4], 2)
    self.assertEqual(rre.width, 5)

  def test_export(self):
    rre = E.RunResultExporter()
    rr = M.RunResult(1, 1)
    rr.add_values(2, 2)
    rre.add_row("test", rr)
    rre.export("test_file")
    with open("test_file", "r") as tf:
      data = tf.read()
      expected_data = '"Type of Run","Accumulated Runtime","Number of Runs","Accumulated Runtime","Number of Runs"\n"test","1","1","2","2"\n'
      self.assertEqual(data, expected_data)
    os.remove("test_file")