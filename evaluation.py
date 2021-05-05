import argparse
from elliot.run import run_experiment

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='movielens',
                      help='dataset name in range [movilens, pintereset]')

args = parser.parse_args()

if args.dataset in ['movilens', 'pintereset']:
    run_experiment(f'''config_files/test_config_{args.dataset}.yml''')
else:
    raise ValueError('Dataset selected is not available for this experiment')
