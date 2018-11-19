from utils.common.io import *
# from utils.common.ace import *
from utils.text.text_data_feeder_aida import TextDataFeeder
from utils.text.word_idx_dict import WordIdxDict
from evaluation_evaluation import evaluation_pipeline
from learning_core_imitation_evaluation import LearningCore

import xml.etree.ElementTree as ET
import shutil
import os
import numpy as np
import pickle
import argparse

def __info_box_dict(info_box):
    last_file_id = ""
    result_dict = dict()
    for one_item in info_box:
        if last_file_id != one_item[0]:
            last_file_id = one_item[0]
            result_dict[one_item[0]] = [one_item[1]]
        else:
            result_dict[one_item[0]].append(one_item[1])
    return result_dict


def __bio_combine_nam_nom(bio_nam_path, bio_nom_path, bio_both_path):
    bio_nam_file = open(bio_nam_path)
    bio_nom_file = open(bio_nom_path)
    bio_both_file = open(bio_both_path, "w")

    for one_line_nam in bio_nam_file:
        one_line_nam = one_line_nam.strip()
        one_line_nom = bio_nom_file.readline().strip()
        if len(one_line_nam) == 0:
            bio_both_file.write("\n")
            continue
        nam_info = one_line_nam.split()
        nom_info = one_line_nom.split()
        token = nam_info[0]
        file_id_offset_info = nam_info[1]
        nam_label = nam_info[2]
        nom_label = nom_info[2]
        output_label = 'O'
        if nam_label == 'O' and nom_label == 'O':
            output_label = 'O'
        else:
            if nam_label != 'O':
                output_label = nam_label
            if nom_label != 'O':
                output_label = nom_label
        bio_both_file.write("%s %s %s\n" % (token, file_id_offset_info, output_label))

    bio_both_file.close()


def __bio_dict(bio_path):
    f = open(bio_path)
    bio_dict = dict()
    bio_sentence_list = f.read().split("\n\n")
    last_file_id = ""
    for one_sentence in bio_sentence_list:
        one_sentence_list_raw = one_sentence.split("\n")
        file_id = one_sentence_list_raw[0].split()[1].split(":")[0]
        one_sentence_list = list()

        for one_token in one_sentence_list_raw:
            one_token_list = one_token.split()
            one_sentence_list.append(one_token_list)
        if last_file_id != file_id:
            last_file_id = file_id
            bio_dict[file_id] = [one_sentence_list]
        else:
            bio_dict[file_id].append(one_sentence_list)
    return bio_dict


def __new_bio_dict(one_file_id, tab_dict, ltf_path):
    result_dict = dict()
    result_dict[one_file_id] = list()

    # record if one entity has been label as a B- something
    used_flag_dict = dict()

    for one_key in tab_dict:
        used_flag_dict[one_key] = 0

    seg_root = ET.parse(ltf_path).getroot()[0][0]
    for one_seg in seg_root.findall('SEG'):

        one_sentence_list = list()
        for one_token in one_seg.findall('TOKEN'):
            original_text = one_token.text
            start_offset = int(one_token.attrib['start_char'])
            end_offset = int(one_token.attrib['end_char'])
            offset_info = "%s:%d-%d" % (one_file_id, start_offset, end_offset)
            token_label = 'O'
            for one_key in tab_dict:
                one_key_start_offset = int(one_key.split(':')[1].split('-')[0])
                one_key_end_offset = int(one_key.split(':')[1].split('-')[1])
                if start_offset >= one_key_start_offset and end_offset <= one_key_end_offset:
                    token_label_candidate = tab_dict[one_key][-3]
                    if used_flag_dict[one_key] == 0:
                        token_label = 'B-%s' % token_label_candidate
                        used_flag_dict[one_key] = 1
                    else:
                        token_label = 'I-%s' % token_label_candidate
                    break
            one_sentence_list.append([original_text, offset_info, token_label])
        result_dict[one_file_id].append(one_sentence_list)

    return result_dict

def __empty_bio_dict(one_file_id, ltf_path):
    result_dict = dict()
    result_dict[one_file_id] = list()
    seg_root = ET.parse(ltf_path).getroot()[0][0]
    for one_seg in seg_root.findall('SEG'):
        one_sentence_list = list()
        for one_token in one_seg.findall('TOKEN'):
            original_text = one_token.text
            start_offset = int(one_token.attrib['start_char'])
            end_offset = int(one_token.attrib['end_char'])
            offset_info = "%s:%d-%d" % (one_file_id, start_offset, end_offset)
            token_label = 'O'
            one_sentence_list.append([original_text, offset_info, token_label])
        result_dict[one_file_id].append(one_sentence_list)
    return result_dict


def __edl_tab_dict(tab_path):
    result_dict = dict()
    for one_line in open(tab_path, encoding='utf-8'):
        one_line = one_line.strip()
        one_line_list = one_line.split("\t")
        key_id = one_line_list[3]
        file_id = key_id.split(":")[0]
        if file_id not in result_dict:
            result_dict[file_id] = dict()
        result_dict[file_id][key_id] = one_line_list
    return result_dict


def __new_info_box(info_box, bio_dict):
    in_file_sent_id = 0
    new_info_box = list()
    last_file_id = ""
    for one_info_item in info_box:
        sentence_info = list()
        if one_info_item[0] != last_file_id:
            last_file_id = one_info_item[0]
            in_file_sent_id = 0
        edl_token_list = bio_dict[last_file_id][in_file_sent_id]
        for idx, one_edl_token in enumerate(edl_token_list):
            one_edl_token.append(one_info_item[1][idx])
            sentence_info.append(one_edl_token)
        new_info_box.append((last_file_id, sentence_info))
        in_file_sent_id += 1
    return new_info_box


def __edl_cs_dict(cs_path):
    result_dict=dict()
    for one_line in open(cs_path, encoding='utf-8'):
        one_line = one_line.strip()
        one_line_list = one_line.split("\t")
        if len(one_line_list) == 5:
            search_key = one_line_list[3]
            edl_key = one_line_list[0]
            confidence_score = one_line_list[-1]
            result_dict[search_key] = (edl_key, confidence_score)
    return result_dict


def bio_check(bio_path):
    f = open(bio_path)

    bio_sentence_list = f.read().split("\n\n")
    print(len(bio_sentence_list))


parser = argparse.ArgumentParser(description='Run through the neural network to acquire output')
parser.add_argument('-t', '--tdf_folder', help='TDF folder', required=True)
parser.add_argument('-f', '--ltf_folder', help='LTF folder', required=True)
parser.add_argument('-e', '--edl_folder', help='EDL folder', required=True)
parser.add_argument('-l', '--list', help='LTF file list', required=True)
parser.add_argument('-o', '--output_folder', help='Output folder for output', required=True)
args = vars(parser.parse_args())

# document_list_file_path = "data/rico_hurricane/rico_en_lst"
# ltf_folder_path = 'data/rico_hurricane/rico_en'
# tdf_folder_path = 'data/tdf'
# edl_folder_path = 'data/edl_sample'
# tab_path = os.path.join(edl_folder_path, "linking.corf.tab")
# cs_path = os.path.join(edl_folder_path, "linking.corf.cs")
# output_folder_path = 'data/temp_output'

document_list_file_path = args['list']
ltf_folder_path = args['ltf_folder']
tdf_folder_path = args['tdf_folder']
edl_folder_path = args['edl_folder']
tab_path = os.path.join(edl_folder_path, "merged.tab")
cs_path = os.path.join(edl_folder_path, "merged.cs")
output_folder_path = args['output_folder']

if os.path.exists(output_folder_path) is False:
    os.mkdir(output_folder_path)
else:
    shutil.rmtree(output_folder_path)
    os.mkdir(output_folder_path)

print("Loading model")
dev_tdf = pickle.load(open("aida_event/data/argument_dev_tdf.pkl", "rb"))
learning_core = LearningCore(token_vocab_size=len(dev_tdf.token_idx_dict.word2idx_dict),
                             pos_vocab_size=len(dev_tdf.pos_idx_dict.word2idx_dict),
                             char_vocab_size=len(dev_tdf.char_idx_dict.char2idx_dict),
                             dep_vocab_size=len(dev_tdf.dep_idx_dict.struct2idx_dict),
                             gpu_device=0,
                             config_path="aida_event/config/xmie.json")
learning_core.load('aida_event/data/model/core_epoch_00028_step_0001176.tfmodel')

tab_dict = __edl_tab_dict(tab_path)
cs_dict = __edl_cs_dict(cs_path)

document_count = len(open(document_list_file_path).read().split("\n"))
count_flag = 1

for one_line in open(document_list_file_path):
    one_line = one_line.strip()
    one_file_id = one_line.replace(".ltf.xml", "")
    print(one_file_id)
    print('%d out of %d files' % (count_flag, document_count))
    count_flag += 1
    print("Loading files ...")
    test_tdf = pickle.load(open(os.path.join(tdf_folder_path, "%s.pkl" % one_file_id), "rb"))
    info_box = pickle.load(open(os.path.join(tdf_folder_path, "%s_info.pkl" % one_file_id), "rb"))

    ltf_path = os.path.join(ltf_folder_path, "%s.ltf.xml" % one_file_id)

    try:
        bio_dict = __new_bio_dict(one_file_id, tab_dict[one_file_id], ltf_path)
    except:
        bio_dict = __empty_bio_dict(one_file_id, ltf_path)

    new_info_box = __new_info_box(info_box, bio_dict)

    sequence_evaluation_list, argument_evaluation_list = evaluation_pipeline(learning_core, test_tdf, new_info_box)

    pickle.dump((sequence_evaluation_list, argument_evaluation_list),
                open(os.path.join(output_folder_path, '%s_result.pkl' % one_file_id), "bw"))