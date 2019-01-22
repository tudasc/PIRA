"""
File: TimeTracking.py
Author: JP Lehr
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: This module allows to track timings of the various bits and pieces with convenience functions.
"""

import os
import lib.Logging as log


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
    self._stop()
    time_tuple = self.get_time()
    log.get_logger().log(sec_name + ' took %.3f seconds' % time_tuple[0], level='perf')
    return (res, time_tuple)

  def m_track(self, sec_name, obj, method_name, *args):
    obj_method = self._get_callable(obj, method_name)
    self._start()
    res = obj_method(*args)
    self._stop()
    time_tuple = self.get_time()
    log.get_logger().log(sec_name + ' took %.3f seconds' % time_tuple[0], level='perf')
    return (res, time_tuple)

  def get_time(self):
    u_time = self._e[2] - self._s[2]
    s_time = self._e[3] - self._s[3]
    return (u_time, s_time)

  def _start(self):
    self._s = os.times()

  def _stop(self):
    self._e = os.times()

  def _get_callable(self, obj, name):
    try:
      obj_method = getattr(obj, name)
      return obj_method
    except Exception as e:
      log.get_logger().log('No such attribute', level='error')
      raise e
    
