"""
File: TimeTracking.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: This module allows to track timings of the various bits and pieces with convenience functions.
"""

import os
import lib.Logging as L


class TimeTracker():
  """
    Lightweight covenience class for time tracking of various components
  """

  def __init__(self):
    self._s = os.times()
    self._e = self._s

  def f_track(self, sec_name, function, *args):
    self._start()
    res = function(*args)
    self.stop()
    time_tuple = self.get_time()
    L.get_logger().log(sec_name + ' took %.3f seconds' % time_tuple[0], level='perf')
    return (res, time_tuple)

  def m_track(self, sec_name, obj, method_name, *args):
    obj_method = self._get_callable(obj, method_name)
    self._start()
    res = obj_method(*args)
    self.stop()
    time_tuple = self.get_time()
    L.get_logger().log(sec_name + ' took %.3f seconds' % time_tuple[0], level='perf')
    return (res, time_tuple)

  def get_time(self):
    u_time = self._e[2] - self._s[2]
    s_time = self._e[3] - self._s[3]
    return (u_time, s_time)

  def _start(self):
    self._s = os.times()

  def stop(self):
    self._e = os.times()

  def _get_callable(self, obj, name):
    try:
      obj_method = getattr(obj, name)
      return obj_method
    except Exception as e:
      L.get_logger().log('No such attribute', level='error')
      raise e
