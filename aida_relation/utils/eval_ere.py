#############################################
# change the F1 metrics, add dependency CNN
#############################################
import data_pro as pro
from models import *
import torch.utils.data as D
import torch
from torch.autograd import Variable
import numpy as np
import torch.nn.functional as F
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split
import copy
import os
from sklearn.metrics import f1_score
import argparse
import io
import gc
import time

start = time.time()

def split_dataset():
    return None


def data_unpack_full(cat_data, target, max_len):
    list_x = np.split(cat_data.numpy(),
                      [max_len, max_len * 2, max_len * 3, max_len * 4, max_len * 5, max_len * 6, max_len * 7],
                      1)
    bx = Variable(torch.from_numpy(list_x[0]))
    bd1 = Variable(torch.from_numpy(list_x[1]))
    bd2 = Variable(torch.from_numpy(list_x[2]))
    b_en = Variable(torch.from_numpy(list_x[3]))
    b_dp = Variable(torch.from_numpy(list_x[4].astype(np.float32)))
    b_mask_e1 = Variable(torch.from_numpy(list_x[5].astype(np.float32)), requires_grad=False)
    b_mask_e1_e2 = Variable(torch.from_numpy(list_x[6].astype(np.float32)), requires_grad=False)
    b_mask_e2 = Variable(torch.from_numpy(list_x[7].astype(np.float32)), requires_grad=False)
    target = Variable(target)
    return bx, bd1, bd2, b_en, b_dp, b_mask_e1, b_mask_e1_e2, b_mask_e2, target


def data_unpack_mask(cat_data, target, max_len):
    list_x = np.split(cat_data.numpy(), [max_len, max_len * 2, max_len * 3, max_len * 4, max_len * 5, max_len * 6], 1)
    bx = Variable(torch.from_numpy(list_x[0])).cuda()
    bd1 = Variable(torch.from_numpy(list_x[1])).cuda()
    bd2 = Variable(torch.from_numpy(list_x[2])).cuda()
    b_en = Variable(torch.from_numpy(list_x[3])).cuda()
    b_mask_e1 = Variable(torch.from_numpy(list_x[4].astype(np.float32)), requires_grad=False).cuda()
    b_mask_e1_e2 = Variable(torch.from_numpy(list_x[5].astype(np.float32)), requires_grad=False).cuda()
    b_mask_e2 = Variable(torch.from_numpy(list_x[6].astype(np.float32)), requires_grad=False).cuda()
    target = Variable(target).cuda()
    return bx, bd1, bd2, b_en, b_mask_e1, b_mask_e1_e2, b_mask_e2, target


def data_unpack_dp(cat_data, target, max_len):
    list_x = np.split(cat_data.numpy(), [max_len, max_len * 2, max_len * 3, max_len * 4], 1)
    bx = Variable(torch.from_numpy(list_x[0])).cuda()
    bd1 = Variable(torch.from_numpy(list_x[1])).cuda()
    bd2 = Variable(torch.from_numpy(list_x[2])).cuda()
    b_en = Variable(torch.from_numpy(list_x[3])).cuda()
    b_dp = Variable(torch.from_numpy(list_x[4].astype(np.float32))).cuda()
    target = Variable(target).cuda()
    return bx, bd1, bd2, b_en, b_dp, target


def data_unpack(cat_data, target, max_len):
    list_x = np.split(cat_data.numpy(),
                      [max_len, max_len * 2, max_len * 3],
                      1)
    bx = Variable(torch.from_numpy(list_x[0])).cuda()
    bd1 = Variable(torch.from_numpy(list_x[1])).cuda()
    bd2 = Variable(torch.from_numpy(list_x[2])).cuda()
    b_en = Variable(torch.from_numpy(list_x[3])).cuda()
    target = Variable(target).cuda()
    return bx, bd1, bd2, b_en, target


def predict(logits, y):
    noNone = 0
    correct_no_None = 0
    predict_no_None = 0
    predict = torch.max(logits, 1)[1]
    # correct = torch.eq(predict, y)
    # acc = correct.sum().float() / float(correct.data.size()[0])
    for i in range(y.data.size()[0]):
        if y.data[i] != 32:
            noNone += 1
            if predict.data[i] == y.data[i]:
                correct_no_None += 1
        if predict.data[i] != 32:
            predict_no_None += 1
    if noNone == 0:
        noNone += 1
    if predict_no_None == 0:
        predict_no_None += 1
    return correct_no_None, predict_no_None, noNone


def F1_metrics(pred, truth):
    flag = True
    for i in range(len(pred)):
        if flag:
            total_pred = pred[i]
            total_truth = truth[i]
            flag = False
        else:
            total_pred = np.concatenate((total_pred, pred[i]), 0)
            total_truth = np.concatenate((total_truth, truth[i]), 0)
    macro_label = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
                   19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
    micro_label = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
                   19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    macro_f1 = f1_score(total_truth, total_pred, macro_label, average="macro")  # mo yu
    micro_f1 = f1_score(total_truth, total_pred, micro_label, average="micro")  # nyu
    return macro_f1, micro_f1


def make_weights_for_balanced_classes(y, nclasses, other=29, other_rate=0.1):
    count = [0] * nclasses
    for item in y:
        count[item] += 1
    weight_per_class = [1.0] * nclasses
    weight_per_class[other] = other_rate
    N = float(sum(count))
    # for i in range(nclasses):
    #     weight_per_class[i] = N / float(count[i]) / 100
    # print(weight_per_class)
    # weight_per_class[1] = weight_per_class[1]
    out_weight = [0.0] * len(y)
    for j, index in enumerate(y):
        out_weight[j] = weight_per_class[index]
    return out_weight


def all_metric(correct_no_None, predict_no_None, noNone):
    acc = float(correct_no_None) / float(predict_no_None)
    recall = float(correct_no_None) / float(noNone)
    if acc == 0 and recall == 0:
        acc = 1
    F1 = (2 * recall * acc) / (recall + acc)
    return acc, recall, F1


os.environ["CUDA_VISIBLE_DEVICES"] = "3"
train_config = argparse.ArgumentParser(description='relation extraction')

# training or testing data file path
train_config.add_argument("--eval_text_path", type=str,
                          help="eval text path, AIDA_plain_text.txt")
train_config.add_argument("--dp_path", type=str,
                          help="eval dp feature path")
train_config.add_argument("--eval_results_file", type=str,
                          help="eval results file")
train_config.add_argument("--train_path", type=str,
                          default="aida_relation/data/ere_filtered_train.txt",
                          help="train file path")
train_config.add_argument("--test_path", type=str,
                          default="aida_relation/data/ere_filtered_test.txt",
                          help="test file path")
train_config.add_argument("--embed_path", type=str, default="aida_relation/data/wiki-news-300d-1M.vec",
                          help="word embedding path")
# train_config.add_argument("--train_dp_path", type=str,
#                           default="/nas/data/m1/shig4/AIDA/extracted_features/ace_head_train_dp_feature.pkl",
#                           help="word embedding path")
# train_config.add_argument("--test_dp_path", type=str,
#                           default="/nas/data/m1/shig4/AIDA/extracted_features/ace_head_test_dp_feature.pkl",
#                           help="word embedding path")
train_config.add_argument("--checkpoint_path", type=str, default="aida_relation/data/",
                          help="model checkpoints")
train_config.add_argument("--piece_pooling", type=bool, default=True, help="max piece wise pooling")

# model choices
train_config.add_argument("--model", type=str, default="CNN", help="CNN encoder")

# tricks
train_config.add_argument("--sampler", type=bool, default=True, help="upsampling and downsampling")
# Hyper parameters for training
train_config.add_argument("--max_len", type=int, default=121, help="max length of sentences")
train_config.add_argument("--epoch", type=int, default=300, help="training epochs")
train_config.add_argument("--bz", type=int, default=64, help="batch size")
train_config.add_argument("--lr", type=float, default=0.02, help="learning rate")
train_config.add_argument("--kp", type=float, default=0.5, help="dropout")
train_config.add_argument("--cn", type=int, default=35, help="class num")
#######
train_config.add_argument("--pos_num", type=int, default=123, help="number of pos embeddings")
train_config.add_argument("--pos_dim", type=int, default=25, help="dimension of position embeddings")
train_config.add_argument("--enty_dim", type=int, default=25, help="dimension of entity type embeddings")
train_config.add_argument("--num_filters", type=int, default=500, help="number of filters or hidden units")
train_config.add_argument("--window_size", type=int, default=3, help="window size")

train_params, _ = train_config.parse_known_args()
eval_text_path = train_params.eval_text_path
eval_dp_feature_path = train_params.dp_path
eval_results_file = train_params.eval_results_file

##########################
# Build word vocabulary
##########################
data = pro.load_data(train_params.train_path)
t_data = pro.load_data(train_params.test_path)
word_dict = pro.build_dict(data[0] + t_data[0])
embedding = pro.load_embedding(train_params.embed_path, word_dict)
Entype_dict = pro.buildTypeDict(data[4] + t_data[4])
# leave 0 to PAD
enty_num = len(Entype_dict) + 1
##############################
# Vectorize sequence
##############################
e_data = pro.load_data(eval_text_path)
model = torch.load(train_params.checkpoint_path + "filter_ere_dp_mask_5000.636.pkl", map_location={'cuda:0': 'cpu'})
t_x, t_y, t_e1, t_e2, t_dist1, t_dist2, t_en_type_vec, t_dp_vec, t_pool_mask_e1, \
t_pool_mask, t_pool_mask_e2 = pro.vectorize_full(e_data, word_dict, train_params.max_len,
                                                 Entype_dict, eval_dp_feature_path)
t_y = np.array(t_y).astype(np.int64)

if train_params.piece_pooling:
    t_np_cat = np.concatenate((t_x, np.array(t_dist1), np.array(t_dist2), np.array(t_en_type_vec), np.array(t_dp_vec),
                               np.array(t_pool_mask_e1), np.array(t_pool_mask), np.array(t_pool_mask_e2)),
                              1)
else:
    t_np_cat = np.concatenate((t_x, np.array(t_dist1), np.array(t_dist2), np.array(t_en_type_vec), np.array(t_dp_vec)),
                              1)

########################
# initialize model
########################
config_model = {
    'batch_size': train_params.bz,
    'max_len': train_params.max_len,
    'embedding': embedding,
    'pos_embed_size': train_params.pos_dim,
    'pos_embed_num': train_params.pos_num,
    'entype_embd_size': train_params.enty_dim,
    'entype_embd_num': enty_num,
    'class_num': train_params.cn,
    "num_hidden": train_params.num_filters,
    'dropout': train_params.kp,
    'learning_rate': train_params.lr,
    'win_size': train_params.window_size
}

optimizer = torch.optim.SGD(model.parameters(), lr=config_model['learning_rate'])

####################
# train dataloader #
# test dataloader  #
####################
test = torch.from_numpy(t_np_cat.astype(np.int64))
t_y_tensor = torch.from_numpy(t_y)
test_datasets = D.TensorDataset(data_tensor=test, target_tensor=t_y_tensor)
test_dataloader = D.DataLoader(test_datasets, config_model['batch_size'], False, num_workers=1)

results = []
confidence_score = []

for (b_x_cat, b_y) in test_dataloader:
    if train_params.piece_pooling:
        bx, bd1, bd2, ben, bdp, bmask1, bmask, bmask2, by = data_unpack_full(b_x_cat, b_y, config_model['max_len'])
    else:
        bx, bd1, bd2, ben, bdp, by = data_unpack_dp(b_x_cat, b_y, config_model['max_len'])
    if train_params.piece_pooling:
        logits = model(bx, bd1, bd2, ben, bdp, bmask1, bmask, bmask2, False)
    else:
        logits = model(bx, bd1, bd2, ben, bdp, False)
    score = torch.nn.functional.softmax(logits, 1).data
    predict = torch.max(logits, 1)[1].data
    temp = []
    for idx in range(predict.size()[0]):
        temp.append(score[idx][predict[idx]])
    results.append(predict)
    confidence_score.append(temp)
index = 0
with open(eval_results_file, "w") as fmodel:
    for result, score in zip(results, confidence_score):
        for idx, rel in enumerate(result):
            # if rel not in [21, 26, 28, 31]:
            fmodel.write(str(rel) + "\t" + str(score[idx]) + "\n")
            # else:
            #     index += 1
            #     fmodel.write("1" + "\t" + str(score[idx]) + "\n")
end = time.time()
whole_time = end - start
print("Running time for English eval is %d" % whole_time)
print("test done!", index)
