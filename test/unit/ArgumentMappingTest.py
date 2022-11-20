"""
File: ArgumentMappingTest.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Tests for the argument mapping
"""

import lib.ArgumentMapping as A

import unittest


class TestPiraArgument(unittest.TestCase):

  def setUp(self):
    self._arg_name = 'arg1'
    self._arg_val = 'val_arg1'
    self._file_arg = 'file_val'

    self.one_arg_pa = A.PiraArgument(self._arg_name, self._arg_val)
    self.file_arg_pa = A.PiraArgument(self._arg_name, self._arg_val, self._file_arg)

  def test_arg_indexing(self):
    self.assertEqual(self.one_arg_pa[0], self._arg_name)
    self.assertEqual(self.one_arg_pa[1], self._arg_val)
    self.assertRaises(IndexError, self.one_arg_pa.__getitem__, 2)

  def test_file_args(self):
    self.assertEqual(self.file_arg_pa[0], self._arg_name)
    self.assertEqual(self.file_arg_pa[1], self._file_arg)
    self.assertRaises(IndexError, self.file_arg_pa.__getitem__, 2)

  def test_arg_as_string(self):
    self.assertEqual(str(self.one_arg_pa), 'arg1val_arg1')
    self.assertEqual(str(self.file_arg_pa), 'arg1val_arg1')


class TestCmdlineLinearArgumentMapper(unittest.TestCase):

  def setUp(self):
    self.mapper_as_in_cfg = {'mapper': 'Linear', 
                             'argmap': {
                               'arg1': ['a', 'b', 'c']
                               }
                             }
    self.mapper_2_params = {'mapper': 'Linear', 
                            'argmap': {
                              'arg1': ['a', 'b', 'c'], 
                              'arg2': ['x', 'y', 'z']
                              }
                            }
    self.mapper_diff_sizes = {'mapper': 'Linear', 
                              'argmap': {
                                'arg1': ['a', 'b', 'c'], 
                                'arg2': ['x', 'y']
                                }
                              }

  def test_correct_factory(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_as_in_cfg)

    self.assertIsNotNone(mapper)
    self.assertIsInstance(mapper, A.CmdlineLinearArgumentMapper)

  def test_arg_mapping(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_as_in_cfg)

    expected = [ ('arg1', 'a'), 
                 ('arg1', 'b'), 
                 ('arg1', 'c') ]
    for (exp, mapped) in zip(expected, mapper):
      self.assertEqual(exp, tuple(mapped))

  def test_mapper_as_string(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_as_in_cfg)

    expected = 'arg1a.arg1b.arg1c.'
    m_str = mapper.as_string()
    self.assertEqual(expected, m_str)

  def test_diff_sizes_except(self):
    self.assertRaises(RuntimeError, A.ArgumentMapperFactory.get_mapper, self.mapper_diff_sizes)

  def test_linear_2_params(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_2_params)

    expected = [ ('arg1', 'a', [], 'arg2', 'x', []), 
                 ('arg1', 'b', [], 'arg2', 'y', []), 
                 ('arg1', 'c', [], 'arg2', 'z', []) ]
    for (exp, mapped) in zip(expected, mapper):
      self.assertEqual(exp, tuple(mapped))


class TestCmdlineCatesianProductArgumentMapper(unittest.TestCase):

  def setUp(self):
    self.mapper_as_in_cfg = {'mapper': 'CartesianProduct', 
                             'argmap': {
                               'arg1': ['a'],
                               'arg2': ['x']
                               }
                             }
    self.mapper_2_params = {'mapper': 'Linear', 
                            'argmap': {
                              'arg1': ['a', 'b'], 
                              'arg2': ['x', 'y']
                              }
                            }
    self.mapper_diff_sizes = {'mapper': 'Linear',
                              'argmap': {
                                'arg1': ['a'], 
                                'arg2': ['x', 'y']
                                }
                              }
    self.mapper_3_params_cartesian = {'mapper': 'CartesianProduct',
                                      'argmap': {
                                        'arg1': ['a'],
                                        'arg2': ['b'],
                                        'arg3': ['c']
                                        }
                                      }

  def test_correct_factory(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_as_in_cfg)

    self.assertIsNotNone(mapper)
    self.assertIsInstance(mapper, A.CmdlineCartesianProductArgumentMapper)

  def test_arg_mapping(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_as_in_cfg)

    expected = [ ('arg1', 'a', 'arg2', 'x'), 
                 ('arg2', 'x', 'arg1', 'a') ]
    for (exp, mapped) in zip(expected, mapper):
      self.assertEqual(exp, mapped)

  @unittest.expectedFailure
  def test_arg_mapping_3_params(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_3_params_cartesian)

    expected = [ ('arg1', 'a', 'arg2', 'b', 'arg3', 'c'),
                 ('arg1', 'a', 'arg3', 'c', 'arg2', 'b'),
                 ('arg2', 'b', 'arg1', 'a', 'arg3', 'c'),
                 ('arg2', 'b', 'arg3', 'c', 'arg1', 'a'),
                 ('arg3', 'c', 'arg2', 'b', 'arg1', 'a'),
                 ('arg3', 'c', 'arg1', 'a', 'arg2', 'b') ]

    for (exp, mapped) in zip(expected, mapper):
      self.assertEqual(exp, mapped)

  def test_mapper_as_string(self):
    mapper = A.ArgumentMapperFactory.get_mapper(self.mapper_as_in_cfg)

    expected = 'arg1a.arg2x.'
    m_str = mapper.as_string()
    self.assertEqual(expected, m_str)


if __name__ == '__main__':
  unittest.main()
