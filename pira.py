"""
File: pira.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: This is PIRA.
"""
import argparse
import lib.Logging as log
import lib.Pira as pira

"""
  Pira Main

  This file contains the main entry point for the Pira framework.
  Options are defined here and then passed to the Pira class.
"""

parser = argparse.ArgumentParser()

# --- Required arguments section
parser.add_argument('config', help='The configuration json file.')

# --- Pira "mode" options
parser.add_argument('--version', help='Which config file version to use', choices=[1, 2], default=1, type=int)
parser.add_argument('--runtime-filter', help='Use run-time filtering', default=False, action='store_true')
parser.add_argument('--iterations', help='Number of Pira iterations', default=3, type=int)
parser.add_argument('--repetitions', help='Number of measurement repetitions', default=3, type=int)

# --- Pira debug options
parser.add_argument('--tape', help='Path to tape file to dump.')

# --- Pira modeling options
group = parser.add_argument_group('ExP')
group.add_argument(
    '--extrap-dir', help='The base directory where extra-p folder structure is placed', type=str, default='')
group.add_argument('--extrap-prefix', help='The prefix in extra-p naming scheme', type=str)


# ====== Start of Pira program ====== #
args = parser.parse_args()

try:
  log.get_logger().log('Starting', level='debug')
  pira.main(args)

finally:
  if args.tape is not None:
    log.get_logger().dump_tape(args.tape)
  else:
    log.get_logger().dump_tape('tape.tp')

log.get_logger().log('End of process')
log.get_logger().show_perf()
