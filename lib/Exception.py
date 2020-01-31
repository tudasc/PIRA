"""
File: Exception.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module holding base exception for all PIRA Exceptions.
"""


class PiraException(Exception):

  def __init__(self, message):
    super().__init__()
    self._message = message

  def __str__(self):
    return self._message
