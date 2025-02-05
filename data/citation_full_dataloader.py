import sys
from data.loader import loader

# import loader

from torch_geometric.utils import add_remaining_self_loops
from torch_geometric.datasets import Planetoid
import torch_geometric.transforms as T

import numpy as np
import os
import torch as th

from data.split import random_planetoid_splits


class citation_full_supervised_loader(loader):
    def __init__(
        self,
        ds_name,
        device="cuda:0",
        self_loop=True,
        digraph=False,
        largest_component=False,
        n_cv=3,
        cv_id=0
    ):
        super(citation_full_supervised_loader, self).__init__(
            ds_name,
            self_loop,
            cross_validation=True,
            largest_component=largest_component,
            n_cv=n_cv,
            cv_id=cv_id
        )
        self.device = device
        self.digraph = digraph
        self.self_loop = self_loop
        self.ds_name = ds_name.lower()


    def load_vanilla_data(self):
        data = Planetoid(
            root='~/datasets/Planetoid', 
            name=self.ds_name.split('full')[0], 
            transform=None)
        g = data[0]
        if self.self_loop:
            g.edge_index, _ = add_remaining_self_loops(g.edge_index)

        self.edge_index = g.edge_index.to(self.device)
        self.features = g.x.to(self.device)
        self.labels = g.y.to(self.device)

        self.in_feats = self.features.shape[1]
        self.n_classes = data.num_classes
        self.n_edges = self.edge_index.shape[-1]
        self.n_nodes = self.labels.shape[0]


    def load_a_mask(self, p=None):
        if p == None:
            splits_file_path = os.path.join(
                "dataset/splits",
                "{}_split_0.6_0.2_{}.npz".format(
                    self.ds_name.split("full")[0], self.cv_id
                ),
            )
            with np.load(splits_file_path) as splits_file:
                train_mask = splits_file["train_mask"]
                val_mask = splits_file["val_mask"]
                test_mask = splits_file["test_mask"]

            self.train_mask = th.BoolTensor(train_mask).to(self.device)
            self.val_mask = th.BoolTensor(val_mask).to(self.device)
            self.test_mask = th.BoolTensor(test_mask).to(self.device)

            if self.largest_component:
                self.train_mask = self.train_mask[self.lcc_flags]
                self.test_mask = self.test_mask[self.lcc_flags]
                self.val_mask = self.val_mask[self.lcc_flags]
            return
        else:
            (p_train, p_val, p_test) = p
            percls_trn = int(round(p_train * len(self.labels) / self.n_classes))
            val_lb = int(round(p_val * len(self.labels)))
            train_mask, val_mask, test_mask = random_planetoid_splits(
                self.labels,
                self.n_classes,
                percls_trn,
                val_lb,
                seed=self.seeds[self.cv_id],
            )
            self.train_mask = train_mask.bool()
            self.val_mask = val_mask.bool()
            self.test_mask = test_mask.bool()



# If use the script below for testing,
# set `export PYTHONPATH=/home/yuhe_guo/repos/polyPlayPerturb`
if __name__ == "__main__":
    # loader = citation_full_supervised_loader("corafull", "cuda:1", True)
    loader = citation_full_supervised_loader("corafull", 
                                             device="cuda:1", 
                                             self_loop=False,
                                             digraph=False,
                                             largest_component=True,
                                             )
    loader.load_data()
    loader.set_split_seeds()
    loader.load_mask(p=(0.6, 0.2, 0.2))
    pass
