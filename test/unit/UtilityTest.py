"""
File: UtilityTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the utility module
"""

import unittest
import typing

import lib.Utility as U
import lib.Logging as L


class TestUtility(unittest.TestCase):

  def test_check_provided_directory(self):
    self.assertTrue(U.check_provided_directory('/home'))
    self.assertFalse(U.check_provided_directory('/glibberish/asdf'))

  def test_check_file(self):
    self.assertTrue(U.is_file('/bin/sh'))
    self.assertFalse(U.is_file('/bin/ushsdnsdhh'))

  def test_shell_dry_run(self):
    command = 'echo "Hello world!"'
    expected_out = '[debug] Utility::shell: DRY RUN SHELL CALL: ' + command

    out, t = U.shell(command, dry=True)
    lm = L.get_logger().get_last_msg()
    self.assertEqual(lm, expected_out)
    self.assertEqual(t, 1.0)
    self.assertEqual(out, '')

  def test_shell_time_invoc(self):
    command = 'echo "Hello World!"'
    expected_out = 'Hello World!\n'

    out, t = U.shell(command, time_invoc=True)
    self.assertEqual(out, expected_out)
    self.assertGreater(t, -1.0)  # XXX This is already a little fishy!

  def test_shell_invoc(self):
    command = 'echo "Hello World!"'
    expected_out = 'Hello World!\n'

    out, t = U.shell(command, time_invoc=False)
    self.assertEqual(out, expected_out)
    self.assertEqual(t, -1.0)  # XXX This is already a little fishy!

  def test_concat_a_b_with_sep_all_empty(self):
    a = ''
    b = ''
    sep = ''
    r = U.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, '')

  def test_concat_a_b_with_sep_empty(self):
    a = 'a'
    b = ''
    sep = ''
    r = U.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'a')

    b = 'a'
    a = ''
    r = U.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'a')

  def test_concat_a_b_with_sep(self):
    a = 'a'
    b = 'b'
    sep = '_'
    r = U.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'a_b')

    a = 'aaaa'
    b = ''
    r = U.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'aaaa_')

  def test_is_valid_file(self):
    file_name = '/work/scratch/j_lehr/temp1-a'
    res = U.is_valid_file_name(file_name)
    self.assertTrue(res)

  def test_is_valid_file_cube_pattern(self):
    file_name = '/work/scratch/j_lehr/_preparation_/hpcg-1-test_run-1'
    res = U.is_valid_file_name(file_name)
    self.assertTrue(res)

  def test_is_valid_file_false(self):
    file_name = '/work\\scratch/j_lehr/temp1-%a'
    res = U.is_valid_file_name(file_name)
    self.assertFalse(res)

  def test_is_valid_file_long(self):
    file_name = '/work/scratch/j_lehr/temp1-a/_asd-tes-12-_2-/asd/nul'
    res = U.is_valid_file_name(file_name)
    self.assertTrue(res)

  def test_is_valid_file_dot(self):
    file_name = '/work+tch/j.lehr/temp1-a'
    res = U.is_valid_file_name(file_name)
    self.assertFalse(res)

  def test_is_valid_file_plus(self):
    file_name = '/work+tch/j_lehr/temp1-a'
    res = U.is_valid_file_name(file_name)
    self.assertFalse(res)

  def test_is_valid_file_whitespace(self):
    file_name = '/work+tch/j_leh r/temp1-a'
    res = U.is_valid_file_name(file_name)
    self.assertFalse(res)

  def test_get_tempdir(self):
    tempdir = U.get_tempdir()

  def test_make_dir(self):
    U.make_dir("/home")

  def test_remove_dir(self):
    U.make_dirs(U.get_tempdir() + "/rm_dir_test")
    U.remove_dir(U.get_tempdir() + "/rm_dir_test")

if __name__ == '__main__':
  unittest.main()
