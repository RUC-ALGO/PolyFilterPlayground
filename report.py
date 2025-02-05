from tune import *

import argparse
import optuna
import optuna.study

import numpy as np
import random 
import torch as th
import torch.nn.functional as F

import time

from opts.tune.public_hypers import public_hypers_default
from opts.tune.public_hypers import convert_dict_to_optuna_suggested
from opts.tune.public_static_settings import public_static_opts
from opts.tune.public_hypers import public_hypers_default
from opts.tune.private_static_settings import *
from opts.tune.private_hypers import *

from utils.optuna_utils import _get_complete_and_pruned_trial_nums
from utils.exp_utils import _prepare_optuna_cache_dir


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--to-file", action='store_true', default=False)

    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument("--model", type=str, default='OptBasisGNN')
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--dataset", type=str, default="cora")
        
    ## log options
    parser.add_argument("--logging", action='store_true', default=False)
    parser.add_argument("--log-detail", action='store_true', default=False)
    parser.add_argument("--log-detailedCh", action='store_true', default=False)
    parser.add_argument("--id-log", type=int, default=0)
    ##
    parser.add_argument("--optuna-n-trials", type=int, default=100)
    parser.add_argument("--study-kw", type=str, required=True, help="Keyword for the study")    

    static_args = parser.parse_args()
    if static_args.gpu < 0:
        static_args.gpu = 'cpu'
    return static_args
    
def initialize_static_args(model=None, dataset=None):
    # 1. Set static args: Define the static arguments shared across tasks and models
    ## 1.1 Static options shared by all tasks
    static_args = parse_args()
    
    ## 1.2 Static options shared by all tasks (Part II)
    dargs = vars(static_args)
    if model is not None and dataset is not None:
        dargs.update({"model": model, "dataset": dataset})

    ## 1.3 Static options of the specific model
    dargs.update(public_static_opts)
    if f'{static_args.model}_static_opts' in globals().keys():
        k = f'{static_args.model}_static_opts'
        dargs.update(globals()[k])
    return static_args


if __name__ == '__main__':
    static_args = initialize_static_args()

    # Path of .db is decided by 
    # `model`, `dataset` and `study_kw`    
    dataset = static_args.dataset
    db_name = f'{static_args.model}-{dataset}'
    dir_name = _prepare_optuna_cache_dir(static_args)
    
    study = optuna.load_study(
        study_name="{}".format(db_name),
        storage = optuna.storages.RDBStorage(url='sqlite:///{}/{}.db'.format(dir_name, db_name), 
                engine_kwargs={"connect_args": {"timeout": 10000}}),
    )
    kw = f"{static_args.model}-{dataset}-{study.user_attrs['kw']}"
    
    # Make sure the tuning process is completed
    n_trials = static_args.optuna_n_trials
    num_completed, num_pruned = _get_complete_and_pruned_trial_nums(study)
    if num_completed + num_pruned >= n_trials:
        print("# Finished! Now I will report.")
    else:
        print("# There remains {} trials to finish the study! \
              \nPlease finish tuning before report!".format(n_trials - num_completed - num_pruned))
        exit(0)
    
    from utils.optuna_utils import _gen_scripts
    tofile = f"--es-ckpt {kw} --log-detail --log-detailedCh 1>logs/{kw}.log 2>logs/{kw}.err"
    cmd_str = _gen_scripts(study, vars(static_args), prefix="python train.py", postfix=f"--n-cv 10 {tofile}")
    print(cmd_str)

    if static_args.to_file:
        print(cmd_str, file=open('cmds.sh', 'a'))