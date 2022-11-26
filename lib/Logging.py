"""
File: Logging.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
Description: Module to handle output of PIRA.
"""

import logging
import sys


class Logger:
  """
    Class to steer output
  """

  def __init__(self):
    self.state = {'debug': False, 'info': True, 'warn': True, 'error': True, 'perf': True}
    self.tape = []
    self.perf_tape = []

  def log(self, msg, level='debug') -> None:
    if self.state[level]:
      self.print_level(level, msg)

    self.record(level, msg)

  def set_state(self, state_id, val='True') -> None:
    self.state[state_id] = val

  def toggle_state(self, state_id) -> None:
    self.state[state_id] = not self.state[state_id]

  def print_level(self, level, msg) -> None:
    if level == 'debug':
      self.print_debug(msg)
    elif level == 'info':
      self.print_info(msg)
    elif level == 'warn':
      self.print_warn(msg)
    elif level == 'error':
      self.print_error(msg)

  def print_debug(self, msg) -> None:
    msg_str = '[Debug] // Start\n' + str(msg) + '\n[Debug] // End'
    print(msg_str)

  def print_info(self, msg) -> None:
    msg_str = '[Info] ' + str(msg)
    print(msg_str)

  def print_warn(self, msg) -> None:
    msg_str = '[Warning!] ' + str(msg)
    print(msg_str)

  def print_error(self, msg) -> None:
    msg_str = '[Error] ' + str(msg)
    print(msg_str)

  def record(self, level, msg) -> None:
    msg_str = '[' + level + '] ' + str(msg)
    self.tape.append(msg_str)
    if level == 'perf':
      self.perf_tape.append('[PERF] ' + str(msg))

  def show_perf(self) -> None:
    for p in self.perf_tape:
      print(p)

  def get_last_msg(self) -> str:
    return self.tape[len(self.tape) - 1]

  def dump_tape(self, out_file=None, cli=False) -> None:
    if out_file is not None:
      of = open(str(out_file), 'w')
      for m in self.tape:
        of.write(m)
        of.write('\n')
      of.close()

    if cli:
      for msg in self.tape:
        print(msg)


# to enable logging with datetime, comment in this line instead
#FORMAT = "[%(levelname)s at %(asctime)s in '%(caller_filename)s' in '%(caller_function)s' line %(caller_line_number)d]: %(message)s"
FORMAT = "[%(levelname)s in '%(caller_filename)s' in '%(caller_function)s' line %(caller_line_number)d]: %(message)s"
DATEFORMAT = "%Y-%m-%d-%H:%M:%S"


class PiraLogger:
  """
  Logger via the logging library to console, can also log to a logfile.
  """

  def __init__(self, file: str = None, log_stack_in_debug=False):
    self.state = {'debug': False, 'info': True, 'warn': True, 'error': True, 'perf': True}
    self.tape = []
    self.perf_tape = []
    self.stack_debug = log_stack_in_debug
    # configuring logging library
    self.loglevel = None
    if self.state["error"]:
      self.loglevel = logging.ERROR
    if self.state["warn"]:
      self.loglevel = logging.WARNING
    if self.state["info"]:
      self.loglevel = logging.INFO
    if self.state["debug"]:
      self.loglevel = logging.DEBUG

    # logger
    self.logger = logging.getLogger(__name__)

    # formatter
    formatter = logging.Formatter(fmt=FORMAT, datefmt=DATEFORMAT)
    # handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    #handler.setLevel(self.loglevel)
    self.logger.addHandler(handler)
    self.logger.setLevel(self.loglevel)
    # handler for file
    if file:
      handler = logging.FileHandler(file, mode="a", encoding="utf-8")
      handler.setLevel(self.loglevel)
      handler.setFormatter(formatter)
      self.logger.addHandler(handler)

  def get_caller(self):
    return self.logger.findCaller(stack_info=True, stacklevel=1)

  def log(self, msg, level='debug') -> None:
    filename, line_number, function_name, stack_info = self.get_caller()
    extras = {
        "caller_filename": filename,
        "caller_line_number": line_number,
        "caller_function": function_name,
        "caller_stack_info": stack_info,
    }
    if self.state[level]:
      self.log_level(level, msg, extras)

    self.record(level, msg)

  def set_state(self, state_id, val='True') -> None:
    self.state[state_id] = val
    self.loglevel = None
    if self.state["error"]:
      self.loglevel = logging.ERROR
    if self.state["warn"]:
      self.loglevel = logging.WARNING
    if self.state["info"]:
      self.loglevel = logging.INFO
    if self.state["debug"]:
      self.loglevel = logging.DEBUG
    self.logger.setLevel(self.loglevel)

  def toggle_state(self, state_id) -> None:
    self.state[state_id] = not self.state[state_id]
    self.loglevel = None
    if self.state["error"]:
      self.loglevel = logging.ERROR
    if self.state["warn"]:
      self.loglevel = logging.WARNING
    if self.state["info"]:
      self.loglevel = logging.INFO
    if self.state["debug"]:
      self.loglevel = logging.DEBUG
    self.logger.setLevel(self.loglevel)

  def log_level(self, level, msg, extras) -> None:
    if level != "debug":
      extras.pop("caller_stack_info")
    if level == 'debug':
      if self.stack_debug:
        self.logger.debug("\n[DEBUG] // Start\n" + msg + "\n" +
                          str(extras["caller_stack_info"] + "\n[DEBUG] // End"),
                          extra=extras)
      else:
        self.logger.debug("\n[DEBUG] // Start\n" + msg + "\n[DEBUG] // End", extra=extras)
    elif level == 'info':
      self.logger.info(msg, extra=extras)
    elif level == 'warn':
      self.logger.warning(msg, extra=extras)
    elif level == 'error':
      self.logger.error(msg, extra=extras)

  def record(self, level, msg) -> None:
    msg_str = '[' + level + '] ' + str(msg)
    self.tape.append(msg_str)
    if level == 'perf':
      self.perf_tape.append('[PERF] ' + str(msg))

  def show_perf(self) -> None:
    for p in self.perf_tape:
      print(p)

  def get_last_msg(self) -> str:
    return self.tape[len(self.tape) - 1]

  def dump_tape(self, out_file=None, cli=False) -> None:
    if out_file is not None:
      of = open(str(out_file), 'w')
      for m in self.tape:
        of.write(m)
        of.write('\n')
      of.close()

    if cli:
      for msg in self.tape:
        print(msg)


logger = Logger()
logger_new = PiraLogger()


def get_logger(old: bool = False):
  if old:
    return logger
  return logger_new
