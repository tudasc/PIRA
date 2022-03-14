"""
File: Logging.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: Module to handle output of PIRA.
"""


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


logger = Logger()


def get_logger():
  return logger
