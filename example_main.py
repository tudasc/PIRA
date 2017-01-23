import lib.Runner as runner
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('config', help='The configuration json file.')
parser.add_argument('--top-lvl-dir', default=None, help='Top level directory for benchmarks. If given, then not read from json file')

args = parser.parse_args()

runner.run(args.config, args.top_lvl_dir)
