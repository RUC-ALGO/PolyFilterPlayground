import torch as th
import numpy as np


def index_to_mask(index, size):
    if th.is_tensor(index):
        mask = th.zeros(size, dtype=th.long, device=index.device)
        mask[index] = 1
    else:
        mask = np.zeros(size)
        mask[index] = 1
    return mask


def get_fingerprint(x):
    x = x.float()
    return x.dot(th.arange(x.shape[0]).float().to(x.device))


def random_planetoid_splits(y,
                            num_classes,
                            percls_trn=20,
                            val_lb=500,
                            seed=12134,
                            check_fingerprints=False):
    _state = th.get_rng_state()
    th.manual_seed(seed)
    indices = []
    for i in range(num_classes):
        index = (y == i).nonzero().view(-1)
        index = index[th.randperm(index.size(0), device=index.device)]
        indices.append(index)
    train_index = th.cat([i[:percls_trn] for i in indices], dim=0)

    rest_index = th.cat([i[percls_trn:] for i in indices], dim=0)
    rest_index = rest_index[th.randperm(rest_index.size(0))]

    num_nodes = y.shape[-1]
    train_mask = index_to_mask(train_index, size=num_nodes)
    val_mask = index_to_mask(rest_index[:val_lb], size=num_nodes)
    test_mask = index_to_mask(rest_index[val_lb:], size=num_nodes)
    th.set_rng_state(_state)

    if check_fingerprints:
        fingerprint_1 = get_fingerprint(y) # 
        fingerprint_2 = get_fingerprint(train_index)
        print('----'*20)
        print("Fingerprint: {}, {}; seed: {}".format(fingerprint_1, fingerprint_2, seed))
    
    return train_mask, val_mask, test_mask