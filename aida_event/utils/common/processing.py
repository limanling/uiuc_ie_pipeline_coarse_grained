import requests
import json
import numpy as np
from utils.common.io import read_dict_from_json_file, read_list_from_file, category_to_bio_category, remove_in_trigger_label

def label_index_to_label_name(input_matrix, sequence_length, label_names):
    result_list = list()
    for sentence_index in range(input_matrix.shape[0]):
        sequence_result_list = list()
        for token_index in range(sequence_length[sentence_index]):
            label_output = label_names[input_matrix[sentence_index, token_index]]
            sequence_result_list.append(label_output)
        result_list.append(sequence_result_list)
    return result_list





def label_preprocessor(token_list, dict_key):
    '''
    Find singletons of "I" labels, and the replace manually replace them.
    :param token_list:
    :param dict_key:
    :return:
    '''
    for idx, one_token in enumerate(token_list):
        if "I-" in one_token[dict_key]:
            category_current = category_detector(one_token[dict_key])
            if idx == 0 or token_list[idx-1][dict_key] == 'O':
                # if the previous label is O
                one_token[dict_key] = "B-%s" % category_current
            else:
                category_previous = category_detector(token_list[idx-1][dict_key])
                if category_current != category_previous:
                    one_token[dict_key] = "I-%s" % category_previous


def category_detector(label):
    if label == 'O':
        return 'O'
    else:
        return '-'.join(label.split('-')[1:])


def trigger_remover(token_list, dict_key):
    for one_token in token_list:
        if "Entity" not in one_token[dict_key]:
            one_token[dict_key] = 'O'


def recover_label(input_list, config_path="xmie.json", label_category='category_list_path'):
    output_list = list()
    config_dict  = read_dict_from_json_file(config_path)
    label_list = read_list_from_file(config_dict['tagger'][label_category])
    for one_entry in input_list:
        output_list.append(label_list[one_entry])
    return(output_list)


def empty_chunk_dict():
    one_chunk_dict = dict()
    one_chunk_dict["index"] = list()
    one_chunk_dict["category"] = list()
    one_chunk_dict["token"] = list()
    return one_chunk_dict


def label_normalizer(token_list, dict_key):
    # put everyting in a chunk
    chunk_list = list()
    one_chunk_dict = empty_chunk_dict()
    for idx, one_token in enumerate(token_list):
        current_label = one_token[dict_key]
        current_category = category_detector(current_label)
        if idx == 0:
            one_chunk_dict["index"].append(idx)
            one_chunk_dict["category"].append(current_category)
            one_chunk_dict["token"].append(one_token["token_surface"])
        else:
            previous_label = token_list[idx-1][dict_key]
            previous_category = category_detector(previous_label)
            if previous_category == 'O':
                if current_category == previous_category:
                    one_chunk_dict["index"].append(idx)
                    one_chunk_dict["category"].append(current_category)
                    one_chunk_dict["token"].append(one_token["token_surface"])
                else:
                    chunk_list.append(one_chunk_dict)
                    one_chunk_dict = empty_chunk_dict()
                    one_chunk_dict["index"].append(idx)
                    one_chunk_dict["category"].append(current_category)
                    one_chunk_dict["token"].append(one_token["token_surface"])
            else:
                if current_category == 'O':
                    chunk_list.append(one_chunk_dict)
                    one_chunk_dict = empty_chunk_dict()
                    one_chunk_dict["index"].append(idx)
                    one_chunk_dict["category"].append(current_category)
                    one_chunk_dict["token"].append(one_token["token_surface"])
                else:
                    if "B-" in previous_label and "B-" in current_label:
                        chunk_list.append(one_chunk_dict)
                        one_chunk_dict = empty_chunk_dict()
                        one_chunk_dict["index"].append(idx)
                        one_chunk_dict["category"].append(current_category)
                        one_chunk_dict["token"].append(one_token["token_surface"])
                    else:
                        if "I-" in current_label:
                            one_chunk_dict["index"].append(idx)
                            one_chunk_dict["category"].append(current_category)
                            one_chunk_dict["token"].append(one_token["token_surface"])
                        else:
                            chunk_list.append(one_chunk_dict)
                            one_chunk_dict = empty_chunk_dict()
                            one_chunk_dict["index"].append(idx)
                            one_chunk_dict["category"].append(current_category)
                            one_chunk_dict["token"].append(one_token["token_surface"])
    chunk_list.append(one_chunk_dict)
    return chunk_list


def masking_type(result_list, target_type):
    for one_sentence in result_list:
        for one_token in one_sentence:
            if target_type in one_token["prediction_stage_one"]:
                one_token["prediction"] = 'O'
            if target_type in one_token["ground_truth"]:
                one_token['ground_truth'] = 'O'


def purge_none_argument(one_arg_info):
    result_dict = dict()
    for one_key in one_arg_info:
        result_dict[one_key] = list()
    for one_key in one_arg_info:
        for one_argument in one_arg_info[one_key]:
            if one_argument[4] != 'Other':
                result_dict[one_key].append(one_argument)
    return result_dict

def remove_multiple_token_trigger(sentence_list):
    dead_event_mention_id = list()
    for one_token_idx, one_token in enumerate(sentence_list):
        if one_token['label'] == 'O':
            continue
        if "Entity" in one_token['label']:
            continue
        if "I-" in one_token['label']:
            dead_event_mention_id.append(one_token['mention_id'])
    for one_token in sentence_list:
        if one_token['label'] == 'O':
            continue
        if "Entity" in one_token['label']:
            continue
        if one_token['mention_id'] in dead_event_mention_id:
            one_token['label'] = 'O'


def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest

def find_dep_path(start_token_id, end_token_id, depparse_dict):
    path_result = list()
    shortest_path = find_shortest_path(depparse_dict['graph'], start_token_id+1, end_token_id+1)
    for one_index in range(len(shortest_path[:-1])):
        path_result.append(depparse_dict['matrix'][shortest_path[one_index], shortest_path[one_index+1]])
    return path_result