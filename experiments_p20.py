import argparse
from elliot.run import run_experiment

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default='most_pop',
                      help='Model name')

args = parser.parse_args()

if args.model in ['most_pop', 'MF', 'NeuMF', 'ials', 'slim', 'easer', 'rp3beta', 'pure_svd']:
    run_experiment(f'''config_files/recsys_config_pinterest_{args.model}.yml''')
else:
    raise ValueError('Model Selected is not available for this experiment')
