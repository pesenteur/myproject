# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 16:15:51 2026

@author: whuxu
"""

import pickle
import numpy as np

if __name__ == '__main__':
    
    data_list = "../ec_number_list.pkl"
    with open(data_list, 'rb') as file:
        ec2id = pickle.load(file)
        
    id2ec = {}
    for ec in ec2id:
        id2ec[ec2id[ec]] = ec
    assert len(ec2id) == len(id2ec) == 5106    
    
        
    data_set = "train"
    data_list = "/work/home/xugang/projects/weak/go/data/EC_number_nc.pkl"
    with open(data_list, 'rb') as file:
        dataset = pickle.load(file)

    dataset = dataset[data_set]
    print ("file length: ", len(dataset))
    
    count = np.zeros(5106)
    for sample_idx in range(len(dataset)):
        
        name = dataset[sample_idx]['name']
        label = np.array(dataset[sample_idx]['label'])
        seq = dataset[sample_idx]['seq']
        count += label
        if label[ec2id["3.1.1.101"]] == 1: print (name)
    print (count[ec2id["3.1.1.101"]])