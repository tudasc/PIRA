"""
File: pira.py
License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
Description: This is PIRA.
"""

__version__ = '0.2.0'

import argparse
import lib.Logging as log
import lib.Pira as pira
import lib.Utility as U

"""
  Pira Main

  This file contains the main entry point for the Pira framework.
  Options are defined here and then passed to the Pira class.
"""

parser = argparse.ArgumentParser(prog='PIRA')

# --- Required arguments section
parser.add_argument('config', help='The configuration json file.')

# -- Pira folder option
pira_dir = U.get_default_pira_dir()
parser.add_argument('--pira-dir', help='The directory which stores PIRA runtime files', type=str, default=pira_dir)

# --- Pira "mode" options
parser.add_argument('--config-version', help='Which config file version to use', choices=[1, 2], default=2, type=int)
parser.add_argument('--runtime-filter', help='Use run-time filtering', default=False, action='store_true')
parser.add_argument('--iterations', help='Number of Pira iterations', default=3, type=int)
parser.add_argument('--repetitions', help='Number of measurement repetitions', default=3, type=int)

# --- Pira debug options
parser.add_argument('--tape', help='Path to tape file to dump.')

# --- Pira modeling options
group = parser.add_argument_group('Extra-P Options')
group.add_argument('--extrap-dir', help='The base directory where extra-p folder structure is placed', type=str, default='')
group.add_argument('--extrap-prefix', help='The prefix in extra-p naming scheme', type=str)

# CSV Export options
csv_group = parser.add_argument_group('CSV Export Options')
csv_group.add_argument('--csv-dir', help='Export runtime measurements as CSV files to the specified directory', type=str, default='')
csv_group.add_argument('--csv-dialect', help='The dialect the CSV file is written in. Possible values: excel, excel_tab, unix; defaults to unix', type=str, default='unix')

# Experimental options - even for research software they are experimental
experimental_group = parser.add_argument_group('Experimental Options - experimental even for research software')
experimental_group.add_argument('--hybrid-filter-iters', help='Do compiletime-filtering after x iterations', default=0, type=int)
experimental_group.add_argument('--export', help='Export performance models to IPCG file.', default=False, action='store_true')
experimental_group.add_argument('--export-runtime-only', help='Export only runtime data used for extra-p modeling', default=False, action='store_true')
experimental_group.add_argument('--load-imbalance-detection', help='Provide a path to an load imbalance detection configuration file (JSON) to enable load imbalance detection', type=str, default='')

# -- General Info
parser.add_argument('--version', help='Shows the version of this PIRA installation', action='version', version='%(prog)s ' + __version__)


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
