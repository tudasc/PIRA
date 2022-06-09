#!/usr/bin/env python3
"""
File: check.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: 
    This script is used to check the output of the integration tests against expectations defined in a file.
    Call this script from the run-script of each integration test. (Usage information: `check.py -h`)
    The expectations file is required to be a JSON file with the this structure:
    ```
    [
        {
            "iteration": 0,
            "expect": ['foo', 'foobar'],
            "may-expect": ['.*bar.*'],
            "never-expect": ['evil']
        },
        {
            "iteration": 1,
            "expect": ['foo'],
            "may-expect": ['foobar', '.*bar.*'],
            "never-expect": ['evil', 'some_function']
        }
    ]

    ```

    The expectations follow the following semantics:
     - `expect`: Fails if at least one of the functions is *not* present in the iteration's instrumentation.
     - `may-expect`: Attention! This field contains regexex! Instrumented functions matching any of the regexes do not provoke a failure. 
        The goal is to avoid long lists of uninteresting functions.
     - Instrumented functions which are not listed in `expect` or match the regex in `may-expect` provoke a failure.
     - `never-expect`: Can be used to explicitly state function which should be absent from the instrumentation.
     - `never-expect` is "stronger" than `may-expect`. If a function is listed in `never-expect` it provokes a failure, regardless of a possible match with `may-expect`.
"""

import argparse
from distutils.command.config import config
import json
import os
import re
from xmlrpc.client import FastMarshaller


def prepare_instrumentation_file(lines):
  """ Prepare a Score-P instrumenation list by removing prefixes, etc. """
  lines = filter(lambda line: "SCOREP_" not in line, lines)
  lines = map(lambda line: line.replace("INCLUDE", ""), lines)
  lines = map(lambda line: line.strip(), lines)
  lines = filter(lambda line: line != "", lines)
  return list(lines)


def matches_any_regex(line, regexes):
  for regex in regexes:
    if re.search(regex, line):
      return True
  return False


class ExpectationTriple:
  """ Represents the triple of expected, may-expect and never-expected for a single iteration. """

  def __init__(self, entry):
    self.iteration = entry["iteration"]
    self.expect = entry["expect"]
    self.may_expect = entry["may-expect"]
    self.never_expect = entry["never-expect"]

  def check_lines(self, lines, verbose=False):
    """ Check a given instrumentation list against expectations. """
    result = True

    if verbose:
      print(f"Iteration {self.iteration}")
      print(f"\tactual instrumentation:         {lines}")
      print(f"\texpected instrumentation:       {self.expect}")
      print(f"\tmaybe-expected instrumentation: {self.may_expect}")
      print(f"\tnever-expected instrumentation: {self.never_expect}")

    conflict = set(self.expect) & set(self.never_expect)
    if conflict:
      print(f"Problem in expectations file. The following functions are both expected and never-expected: {conflict}")
      return False

    # test whether all expected functions are present
    expected_but_missing = set(self.expect) - set(lines)
    if expected_but_missing:
      print(
          f"Iteration {self.iteration}: The following functions were expected to be present in the instrumenation, but were not: {expected_but_missing}"
      )
      result = False

    remaining = set(lines) - set(self.expect)

    # test for functions which have been marked as explicitly not expected
    explicitly_not_expected = set(remaining) & set(self.never_expect)
    if explicitly_not_expected:
      print(
          f"Iteration {self.iteration}: The following functions were instrumented, but explicitly not expected: {explicitly_not_expected}"
      )
      result = False

    # remove all functions from remaining which match an expression in may-expect
    remaining = list(filter(lambda x: not matches_any_regex(x, self.may_expect), remaining))

    # test for any further functions which are instrumented, but unexptected
    remaining = set(remaining) - explicitly_not_expected
    if remaining:
      print(
          f"Iteration {self.iteration}: The following functions were instrumented, but not (may-) expected: {remaining}"
      )
      result = False

    return result


def main():
  # parse cli arguments
  parser = argparse.ArgumentParser(description="Check instrumentation output of PIRA integration tests.")
  parser.add_argument('instr_dir_path',
                      metavar='dir',
                      help="Path to directory containing the filter lists produced by PIRA.")
  parser.add_argument('expected_path', metavar='expected', help="Path to JSON file describing the expected output.")
  parser.add_argument('benchmark_name',
                      metavar='benchmark',
                      help="Benchmark name as in the filter list files. Most likely;: \"application_name\"_\"flavour\"")
  parser.add_argument('-v',
                      '--verbose',
                      action='store_true',
                      help="Print actual and expected instrumentation before comparing.")
  args = parser.parse_args()

  # populate expectations data structure
  expectations = {}
  with open(args.expected_path, "r") as f:
    for entry in json.load(f):
      expectations[entry["iteration"]] = ExpectationTriple(entry)

  # iterate over expectations
  result = True
  for i, exp in expectations.items():
    instr_file_name = "instrumented-" + args.benchmark_name + "_it-" + str(i) + ".txt"
    instr_file_path = os.path.join(args.instr_dir_path, instr_file_name)

    try:
      with open(instr_file_path, "r") as f:
        lines = prepare_instrumentation_file(f.readlines())
      result &= exp.check_lines(lines, verbose=args.verbose)
    except OSError as err:
      print(f"Error opening instrumentation file for iteration {i}: {err}")
      result = False

  if result:
    print("All checks passed.")

  # exit with error code iff there have been violated expectation
  exit(not result)


if __name__ == '__main__':
  main()
