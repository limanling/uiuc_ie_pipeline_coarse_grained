from utils.common.io import *
from utils.text.text_data_feeder_aida import TextDataFeeder
from utils.text.word_idx_dict import WordIdxDict

import xml.etree.ElementTree as ET

import os
import numpy as np
import pickle
import argparse
import shutil

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
    for one_line in open(tab_path):
        one_line = one_line.strip()
        one_line_list = one_line.split("\t")
        key_id = one_line_list[3]
        result_dict[key_id] = one_line_list
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
    entity_type_dict=dict()
    for one_line in open(cs_path, encoding='utf-8'):
        one_line = one_line.strip()
        one_line_list = one_line.split("\t")
        if len(one_line_list) == 3 and one_line_list[1] == 'type':
            entity_type_dict[one_line_list[0]] = one_line_list[2]
        if len(one_line_list) == 5:
            search_key = one_line_list[3]
            edl_key = one_line_list[0]
            confidence_score = one_line_list[-1]
            result_dict[search_key] = (entity_type_dict[one_line_list[0]], edl_key, confidence_score)
    return result_dict


def bio_check(bio_path):
    f = open(bio_path)

    bio_sentence_list = f.read().split("\n\n")
    print(len(bio_sentence_list))

parser = argparse.ArgumentParser(description='Final output to ColdStart++')
parser.add_argument('-t', '--tdf_folder', help='TDF folder', required=True)
parser.add_argument('-f', '--temp_output_folder', help='Temporary output file', required=True)
parser.add_argument('-e', '--edl_folder', help='EDL folder', required=True)
parser.add_argument('-l', '--list', help='LTF file list', required=True)
parser.add_argument('-o', '--output_folder', help='Output folder', required=True)
args = vars(parser.parse_args())

document_list_file_path = args['list']
edl_folder_path = args['edl_folder']
entity_cs_file_path = os.path.join(edl_folder_path, 'merged.cs')
tdf_folder_path = args['tdf_folder']
temp_output_folder_path = args['temp_output_folder']
output_folder_path = args['output_folder']

if os.path.exists(output_folder_path) is False:
    os.mkdir(output_folder_path)
else:
    shutil.rmtree(output_folder_path)
    os.mkdir(output_folder_path)

cs_dict = __edl_cs_dict(entity_cs_file_path)

document_count = len(open(document_list_file_path).read().split("\n"))
count_flag = 1
event_id = 0

string_to_write_list = list()
for one_line in open(document_list_file_path):
    one_line = one_line.strip()
    one_file_id = one_line.replace(".ltf.xml", "")
    print(one_file_id)
    print('%d out of %d files' % (count_flag, document_count))
    count_flag += 1
    print("Loading files ...")
    info_box = pickle.load(open(os.path.join(tdf_folder_path, "%s_info.pkl" % one_file_id), "rb"))

    try:
        sequence_evaluation_list, argument_evaluation_list = pickle.load(
            open(os.path.join(temp_output_folder_path, "%s_result.pkl" % one_file_id), "rb"))
    except:
        print("Does not work for %s" % one_file_id)
        continue
    trigger_list = list()
    event_dict = dict()

    for sent_id, one_sentence in enumerate(argument_evaluation_list):
        for one_trigger_entity_pair in one_sentence["argument_prediction"]:
            trigger_confidence_score = sequence_evaluation_list[sent_id][one_trigger_entity_pair[0]]['confidence_score']
            trigger_info = (info_box[sent_id][0], sent_id, one_trigger_entity_pair[0], one_trigger_entity_pair[3], trigger_confidence_score)
            if trigger_info not in trigger_list:
                event_id += 1
                trigger_list.append(trigger_info)
                event_dict[event_id] = dict()
                event_dict[event_id]["trigger"] = trigger_info
                event_dict[event_id]["argument"] = list()
            event_dict[event_id]["argument"].append(one_trigger_entity_pair)

    for one_key in event_dict:
        one_trigger = event_dict[one_key]["trigger"]
        one_event_type = one_trigger[3]
        type_info_string = ":Event_%06d\ttype\t%s" % (one_key, one_event_type)
        one_trigger_index = one_trigger[2]
        file_id = one_trigger[0]
        sent_id = one_trigger[1]
        trigger_text = info_box[sent_id][1][one_trigger_index].text
        trigger_start = info_box[sent_id][1][one_trigger_index].attrib['start_char']
        trigger_end = info_box[sent_id][1][one_trigger_index].attrib['end_char']
        trigger_confidence_score = one_trigger[4]
        mention_info_string = ':Event_%06d\tmention.actual\t"%s"\t%s:%s-%s\t%f' % (one_key, trigger_text,
                                                                                   file_id, trigger_start,
                                                                                   trigger_end,
                                                                                   trigger_confidence_score)
        canonical_mention_info_string = ':Event_%06d\tcanonical_mention.actual\t"%s"\t%s:%s-%s\t%f' % (one_key,
                                                                                                       trigger_text,
                                                                                                       file_id,
                                                                                                       trigger_start,
                                                                                                       trigger_end,
                                                                                                       trigger_confidence_score)
        string_to_write_list.append(type_info_string)
        string_to_write_list.append(mention_info_string)
        string_to_write_list.append(canonical_mention_info_string)
        for one_argument in event_dict[one_key]["argument"]:
            arg_start = one_argument[1]
            arg_end = one_argument[1] + one_argument[2] + 1
            argument_token_info = info_box[sent_id][1][arg_start:arg_end]
            argument_start_char = argument_token_info[0].attrib['start_char']
            argument_end_char = argument_token_info[-1].attrib['end_char']
            argument_role = one_argument[4]
            search_key = "%s:%s-%s" % (file_id, argument_start_char, argument_end_char)
            try:
                argument_entity_id = cs_dict[search_key][1]
                argument_confidence = one_argument[5]
                if argument_role == 'Other':
                    continue
                argument_info_string = ':Event_%06d\t%s_%s.actual\t%s\t%s\t%f' % (one_key,
                                                                                  one_event_type,
                                                                                  argument_role,
                                                                                  argument_entity_id,
                                                                                  search_key,
                                                                                  float(argument_confidence))
            except KeyError:
                print("Key Error in %s" % one_file_id)
                continue
            string_to_write_list.append(argument_info_string)
    # break

f = open(os.path.join(output_folder_path, "events_raw.cs"), "w")
for one_item in string_to_write_list:
    f.write("%s\n" % one_item)
f.close()
