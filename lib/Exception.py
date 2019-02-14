"""
File: Exception.py
Author: JP Lehr, Sachin Manawadi 
Email: jan.lehr@sc.tu-darmstadt.de
Github: https://github.com/jplehr
Description: Module holding base exception for all PIRA Exceptions.
"""


class PiraException(Exception):

  def __init__(self, message):
    super().__init__()
    self._message = message

  def __str__(self):
    return self._message
