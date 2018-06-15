import sys
sys.path.append('../')

import unittest
import typing


import lib.Utility as u
import lib.Logging as log


class TestUtility(unittest.TestCase):

  def test_check_provided_directory(self):
    self.assertTrue(u.check_provided_directory('/home'))
    self.assertFalse(u.check_provided_directory('/glibberish/asdf'))

  def test_check_file(self):
    self.assertTrue(u.check_file('/bin/sh'))
    self.assertFalse(u.check_file('/bin/ushsdnsdhh'))

  def test_shell_dry_run(self):
    command = 'echo "Hello world!"'
    expected_out = '[debug] DRY RUN SHELL CALL: ' + command

    out, t = u.shell(command, dry=True)
    lm = log.get_logger().get_last_msg()
    self.assertEqual(lm, expected_out)
    self.assertEqual(t, -1.0)
    self.assertEqual(out, '')

  def test_shell_time_invoc(self):
    command = 'echo "Hello World!"'
    expected_out = 'Hello World!'

    out, t = u.shell(command, time_invoc=True)
    self.assertEqual(out, 'Hello World!')
    self.assertGreater(t, -1.0) # XXX This is already a little fishy!

  def test_shell_invoc(self):
    command = 'echo "Hello World!"'
    expected_out = 'Hello World!'

    out, t = u.shell(command, time_invoc=False)
    self.assertEqual(out, 'Hello World!')
    self.assertEqual(t, -1.0) # XXX This is already a little fishy!

  def test_concat_a_b_with_sep_all_empty(self):
    a = ''
    b = ''
    sep = ''
    r = u.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, '')

  def test_concat_a_b_with_sep_empty(self):
    a = 'a'
    b = ''
    sep = ''
    r = u.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'a')

    b = 'a'
    a = ''
    r = u.concat_a_b_with_sep(a,b,sep)
    self.assertEqual(r, 'a')

  def test_concat_a_b_with_sep(self):
    a = 'a'
    b = 'b'
    sep = '_'
    r = u.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'a_b')

    a = 'aaaa'
    b = ''
    r = u.concat_a_b_with_sep(a, b, sep)
    self.assertEqual(r, 'aaaa_')


if __name__ == '__main__':
  unittest.main()
