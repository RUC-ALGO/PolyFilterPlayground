from data.loader import loader

from torch_geometric.utils import to_undirected, remove_self_loops, add_self_loops
import numpy as np
import torch as th

# from utils.data_split import random_planetoid_splits
import os


class platonov_dataloader(loader):
    def __init__(self, ds_name, device='cuda:0', self_loop=True, 
                    digraph=False, largest_component=False, 
                    n_cv=3, cv_id=0):
        super(platonov_dataloader, self).__init__(
            ds_name, 
            cross_validation=True, 
            largest_component=largest_component,
            n_cv=n_cv, 
            cv_id=cv_id
            )
        self.device = device
        self.digraph = digraph
        self.self_loop = self_loop


    def load_vanilla_data(self):
        dataset = np.load(os.path.join('dataset/platonov', f'{self.ds_name.replace("-", "_")}.npz'))
        self.edge_index = th.LongTensor(dataset['edges']).to(self.device).T
        if not self.digraph:
            self.edge_index = to_undirected(self.edge_index)
        if self.self_loop:
            self.edge_index = remove_self_loops(self.edge_index)[0]
            self.edge_index = add_self_loops(self.edge_index)[0]
        self.features = th.FloatTensor(dataset['node_features']).to(self.device)
        self.labels = th.LongTensor(dataset['node_labels']).to(self.device)
        if self.labels.dim()==2 and self.labels.shape[-1]==1:
            self.labels = self.labels.squeeze()
        self.n_nodes = self.labels.shape[0]
        self.in_feats = self.features.shape[1]
        
        # infer the number of classes for non one-hot and one-hot labels
        if len(self.labels.shape) == 1:
            labels = self.labels.unsqueeze(1)
        self.n_classes = max(self.labels.max().item() + 1, labels.shape[-1])
        self.n_edges = self.edge_index.shape[-1]


    def load_fixed_splits(self):
        dataset = np.load(os.path.join('dataset/platonov', f'{self.ds_name.replace("-", "_")}.npz'))
        self.train_mask = th.tensor(dataset['train_masks'][self.cv_id])
        self.val_mask = th.tensor(dataset['val_masks'][self.cv_id])
        self.test_mask = th.tensor(dataset['test_masks'][self.cv_id])
        return 
    

    def load_a_mask(self, p=None):
        if p==None:
            assert ValueError, "Only support fixed split!"
        
        self.load_fixed_splits()

        if self.largest_component and self.n_components_orig > 1:
            assert NotImplementedError, "For the largest component option, "\
                "the fixed train/val/test nids should be reindexed. "\
                    "It is not implemented yet."
        
        
        return 

        
def test_platonov():
    loader = platonov_dataloader('questions', 'cuda:1', True)
    loader.load_data()
    loader.load_mask()
    print('Success!')


def test_platonov_lcc():
    for ds in ['questions', 'roman-empire', 'minesweeper', 'tolokers', 
                          'amazon_ratings', 'chameleon-filtered', 'squirrel-filtered']:
        print(ds)
        loader = platonov_dataloader(ds, 
                                     'cuda:1', 
                                     self_loop=True,
                                     digraph=False,
                                     largest_component=True)
        loader.load_data()
        loader.load_mask()
        print('Success!')


if __name__=='__main__':
    # test_platonov()
    test_platonov_lcc()