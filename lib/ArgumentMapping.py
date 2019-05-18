"""
File: Runner.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module provides mapper classes to handle argument.
"""

import sys
sys.path.append('..')


class PiraArgument:
  """
  In this class the 0-th entry is always the name of the parameter.
  The 1-st entry is always the value to pass to the target application - it might be a file name.
  When a string is constructed from this class, always parametername+parametervalue is returned.
  """

  def __init__(self, param_name, param_value, file_name=None):
    self._param_name = param_name
    self._param_val = param_value
    self._file_name = file_name

  def __getitem__(self, key):
    if key == 0:
      return self._param_name
    elif key == 1:
      if self._file_name is None:
        return self._param_val
      else:
        return self._file_name
    else:
      raise IndexError('PiraArgument only accepts 0 or 1 index.')

  def __str__(self):
    return self._param_name + self._param_val

  def get_params(self):
    return [self._param_name]


class PiraListArgument(PiraArgument):

  def __init__(self, param_names, param_vals, file=None):
    self._p_names = param_names
    self._p_vals = param_vals
    self._p_files = file

  def __getitem__(self, key):
    if key >= 3 * len(self._p_names):
      raise IndexError('Out of Range in PiraListArgument')

    if key % 3 == 2:
      return self._p_files
    elif key % 3 == 1:
      if key >= 3:
        e_key = key - 3
      else:
        e_key = key - 1
      return self._p_vals[e_key]
    elif key % 3 == 0:
      if key >= 3:
        e_key = key - 2
      else:
        e_key = key
      return self._p_names[e_key]

    raise IndexError('Wrong index')

  def __str__(self):
    s = ''
    for n, v in zip(self._p_names, self._p_vals):
      s += n + v
    return s

  def get_params(self):
    return self._p_names  # This should already be a list


class ArgumentMapper:

  def __iter__(self):
    raise StopIteration('Not implemented.')

  def as_list(self):
    l = []
    for p in self:
      l.append(p)

    return l

  def as_string(self) -> str:
    s = ''
    for p in self:
      s += str(p[0]) + str(p[1]) + '.'

    return s

  def __str__(self):
    return self.as_string()


class CmdlineLinearArgumentMapper(ArgumentMapper):
  """
  Mapper to create a linear mapping of one or more commandline passed arguments.
  If given more than one argument, it acts like a zip iterator, therefore, all arguments
  must receive the same number of values.
  """

  def __init__(self, argmap, files=None):
    self._argmap = argmap
    self._files = files
    arg_vals = self._argmap.values()
    l_elem = list(arg_vals)[0]
    for e in arg_vals:
      if len(e) is not len(l_elem):
        raise RuntimeError('CmdlineLinearArgumentMapper: All parameters need the same number of values')
    self._num_elems = len(l_elem)

  def __iter__(self):
    if len(self._argmap.keys()) is 1:
      key = list(self._argmap.keys())[0]
      # If this is not a file mapper, we just return as normal
      if self._files == None:
        for v in self._argmap[key]:
          yield PiraArgument(key, v)
      else:
        # If this is a file mapper, we need to give the correct file as well
        for v, f in zip(self._argmap[key], self._files):
          yield PiraArgument(key, v, f)

    else:
      keys = self._argmap.keys()
      values = []
      names = []
      files = []
      for counter in range(0, self._num_elems):
        for k in keys:
          val = self._argmap[k][counter]
          names.append(k)
          values.append(val)
          files.append(self._files[counter])

        print('CmdlineLinearArgumentMapper::__iter__: names ' + str(names) + ' | values ' + str(values) + ' | files ' + str(files))
        yield PiraListArgument(names, values, files)
        names = []
        values = []
        files = []

  def __getitem__(self, key):
    if key is 0:
      key = list(self._argmap.keys())[0]
      return PiraArgument(key, self._argmap[key][0])

    else:
      raise IndexError('Only direct access to first element allowed.')

  def get_argmap(self):
    return self._argmap


class CmdlineCartesianProductArgumentMapper(ArgumentMapper):
  """
  Mapper to create the Cartesian product of all given argument/values. All arguments passed
  via the commandline. Here, the arguments do not need to have equally many values.
  FIXME: Does not work for more than 2 parameters.
  """

  def __init__(self, argmap):
    self._argmap = argmap

  def __iter__(self):
    keys = self._argmap.keys()
    res = []
    for k in keys:
      for v in self._argmap[k]:
        for kk in keys:
          if k is kk:
            continue
          for vv in self._argmap[kk]:
            res.append(k)
            res.append(v)

            res.append(kk)
            res.append(vv)
            yield tuple(res)
            res = []

  def __getitem__(self, key):
    pass


class MPIArgumentMapper(ArgumentMapper):
  def __init__(self, argmap, base_mapper):
    self._n_mpi = argmap['np']
    self._base_mapper = base_mapper

  def __iter__(self):
    for nps in self._n_mpi:
      for args in self._base_mapper:
        # args is PiraListArgument
        #print('MPI Argument Mapper: ' + str(args))
        #print('ARGS: ' + str(args[1]) + ' | ' + str(args[4]))
        res = []
        res.append(nps)
        for v in args:
          res.append(v)
        print('Yielded: ' + str(res))
        yield res

  def get_argmap(self):
    return self._base_mapper.get_argmap()


class UserArgumentMapper(ArgumentMapper):
  """
  Used for complex mappings of arguments to inputs / files.
  
  TODO: How should this be implemented? Ideas:
  1) Loads another functor that does the final mapping.
  2) Config has explicit mapping that is loaded.
  """
  pass


class ArgumentMapperFactory:
  """
  Creates the correct ArgumentMapper for the specific circumstance.
  """

  @classmethod
  def get_mapper(cls, options):
    requested_mapper = options['mapper']
    is_file_mapper = 'pira-file' in options

    # The term 'pira-file' indicates that a FileMapper needs to be used instead of a regular mpapper.
    # The options have a field called pira-file, which holds a list of filenames to be used.
    # Currently, this can only be used with a linear mapper.
    if requested_mapper == 'Linear':
      if is_file_mapper:
        return CmdlineLinearArgumentMapper(options['argmap'], options['pira-file'])
      return CmdlineLinearArgumentMapper(options['argmap'])

    elif requested_mapper == 'CartesianProduct':
      return CmdlineCartesianProductArgumentMapper(options['argmap'])

    elif requested_mapper == 'MPILinear':
      if is_file_mapper:
        return MPIArgumentMapper(options['argmap'], CmdlineLinearArgumentMapper(options['argmap'], options['pira-file']))
      return MPIArgumentMapper(options['argmap'], CmdlineLinearArgumentMapper(options['argmap']))

    else:
      raise RuntimeError('Unknown Mapper: ' + requested_mapper)
