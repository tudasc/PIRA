import lib.Runner as runner
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('config', help='The configuration json file.')

args = parser.parse_args()

print('running')
runner.run(args.config)
print('done')
