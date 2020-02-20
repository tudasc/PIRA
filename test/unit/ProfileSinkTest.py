"""
File: ProfileSinkTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Tests for the argument mapping
"""

import lib.ProfileSink as P
import lib.Configuration as C

import unittest
import typing


class TestProfileSink(unittest.TestCase):

  def setUp(self):
    self._dir = '/tmp'
    self._target = 'asd'
    self._flavor = 'fl'
    self._dbi = 'a'
    self._nreps = 1
    self._tc = C.TargetConfiguration(self._dir, self._dir, self._target, self._flavor, self._dbi)
    self._ic_true = C.InstrumentConfig(True, self._nreps)
    self._ic_false = C.InstrumentConfig()
    self._params = ['par1']
    self._prefix = 'pre'
    self._postfix = 'post'
    self._filename = 'profile.cubex'

  def test_base_raises(self):
    sb = P.ProfileSinkBase()
    self.assertRaises(RuntimeError, sb.process, '/tmp', self._tc, self._ic_true)

  def test_extrap_create(self):
    es = P.ExtrapProfileSink(self._dir, self._params, self._prefix, self._postfix, self._filename, self._nreps)
    self.assertEqual(es.get_target(), '')


if __name__ == '__main__':
  unittest.main()
