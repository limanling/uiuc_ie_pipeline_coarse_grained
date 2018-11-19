# IO modules

import json
import logging
import os
from gensim.models.word2vec import Word2Vec
import numpy as np


def stdout_logger(module_name=__name__):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)
    return logger


def w2v_model_from_file(model_path):
    logger = stdout_logger()
    logger.info("Loading pretrained Word2Vec from %s" % model_path)
    w2v_model = Word2Vec.load(model_path)
    word_count = len(w2v_model.wv.vocab)
    logger.info("A vocabulary of %d have been loaded to memory" % word_count)
    return w2v_model


def w2v_model_to_embedding(w2v_model, w2i_dict):
    logger = stdout_logger()
    pretrained_embedding_matrix = np.zeros((len(w2i_dict.word2idx_dict),200), dtype=np.float32)
    hit_list = list()
    missed_list = list()
    for one_key in w2i_dict.word2idx_dict.keys():
        # print(one_key in w2v_model.wv.vocab)
        if one_key in w2v_model.wv.vocab:
            pretrained_embedding_matrix[w2i_dict.word2idx_dict[one_key], :] = w2v_model[one_key]
            hit_list.append(w2i_dict.word2idx_dict[one_key])
        else:
            missed_list.append(w2i_dict.word2idx_dict[one_key])
    embedding_mean = np.mean(pretrained_embedding_matrix[hit_list,:])
    embedding_std = np.std(pretrained_embedding_matrix[hit_list,:])
    for one_missed_key in missed_list:
        pretrained_embedding_matrix[one_missed_key, :] = np.random.normal(embedding_mean, embedding_std, (200))
    # for padding, we make everything zero
    pretrained_embedding_matrix[0, :] = np.zeros((200), dtype=np.float32)
    # for unknown, we put in an average
    pretrained_embedding_matrix[1, :] = np.mean(pretrained_embedding_matrix[hit_list,:], axis=0)
    pretrained_embedding_matrix[2, :] = np.zeros((200), dtype=np.float32) + 1
    pretrained_embedding_matrix[3, :] = np.zeros((200), dtype=np.float32) - 1
    return pretrained_embedding_matrix


def dict_to_json(input_dict):
    json_string = json.dumps(input_dict, indent=4, separators=(',', ': '))
    return json_string


def read_dict_from_json_file(file_path):
    dict_from_json = json.load(open(file_path))
    return dict_from_json


def read_list_from_file(file_path):
    result_list = list()
    for one_line in open(file_path):
        one_line = one_line.strip()
        result_list.append(one_line)
    return result_list


def category_to_bio_category(category_list):
    bio_category_list = list()
    for one_category in category_list:
        if one_category == 'O':
            bio_category_list.append('O')
        else:
            bio_category_list.append('B-%s' % one_category)
            bio_category_list.append('I-%s' % one_category)
    return bio_category_list

def remove_in_trigger_label(category_list):
    result_list = list()
    for one_category in category_list:
        if one_category == 'O':
            result_list.append(one_category)
            continue
        if 'Entity' in one_category:
            result_list.append(one_category)
            continue
        if 'I-' in one_category:
            continue
        else:
            result_list.append(one_category)
    return result_list


def dict_of_event_argument(input_list):
    result_dict = dict()
    for one_entry in input_list:
        event_type = one_entry.split('\t')[0]
        argument_role = one_entry.split('\t')[1]
        if event_type not in result_dict:
            result_dict[event_type] = [argument_role]
        else:
            result_dict[event_type].append(argument_role)
    return result_dict


def all_files_in_root(root_folder):
    result_list = list()

    def recursive_exploration(target_path, file_list):
        if ".DS_store" in target_path:
            return
        if os.path.isfile(target_path) is True:
            file_list.append(target_path)
        else:
            for one_file in os.listdir(target_path):
                one_path = os.path.join(target_path, one_file)
                recursive_exploration(one_path, file_list)
    recursive_exploration(root_folder, result_list)
    return result_list
