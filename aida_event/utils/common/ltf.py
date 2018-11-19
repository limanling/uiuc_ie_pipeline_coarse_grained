import os
import xml.etree.ElementTree as ET
from lxml import etree
import numpy as np
from xml.sax.saxutils import unescape

from utils.common.io import read_dict_from_json_file
import nltk
from utils.common.processing import label_preprocessor, remove_multiple_token_trigger
from utils.common.brat import BRATAnnotation


class LTF:
    def __init__(self,
                 stanford_nltk_wrapper,
                 file_path,
                 brat_annotation_folder,
                 config_file_path="config/xmie.json"):
        self._snw = stanford_nltk_wrapper
        self.file_path = file_path
        self.__brat_annotation_folder = brat_annotation_folder
        self.config_file_path = config_file_path
        self.file_name = self.file_path.split("/")[-1]
        self.file_id = self.file_name.replace('.ltf.xml', '')
        self.annotation_table = self.__annotation_table()
        self.original_table = self.__original_table()

    def __annotation_table(self):
        root = ET.parse(self.file_path).getroot()
        document_root = root[0]
        sentence_list = list()
        brat_annotation = BRATAnnotation(file_id=self.file_id, brat_annotation_folder=self.__brat_annotation_folder)

        for one_TEXT in document_root:
            stanford_sentence_list = list()
            for one_SEG in one_TEXT:
                token_list = list()
                for one_token in one_SEG.findall("TOKEN"):
                    token_list.append(unescape(one_token.text, {"&apos;": "'", "&quot;": '"'}))
                stanford_sentence_list.append(token_list)
            print("This document has %d sentence(s)" % len(stanford_sentence_list))
            pos_tag_result_stanford = self._snw.pos_tag_sentences(stanford_sentence_list)
            try:
                dep_parser_result_stanford = self._snw.dependency_parser_sentences(pos_tag_result_stanford)
                dep_parser_result_list = [x for x in dep_parser_result_stanford]
            except:
                print('This file has an assertion or value error, starting with single sentence extraction')
                dep_parser_result_list = list()
                for one_pos_tag_sentence in pos_tag_result_stanford:
                    try:
                        one_dep_parser_result = self._snw.dependency_parser(one_pos_tag_sentence)
                        dep_parser_result_list.append(one_dep_parser_result)
                    except:
                        dep_parser_result_list.append(None)
            count_flag = 0
            for one_SEG in one_TEXT:
                used_dict = dict()
                token_list = list()
                for one_token in one_SEG.findall("TOKEN"):
                    token_list.append(one_token.text)
                pos_tag_result = pos_tag_result_stanford[count_flag]
                token_list = list()
                for one_token_idx, one_token in enumerate(pos_tag_result):
                    token_dict = dict()
                    token_dict['word'] = one_token[0].lower()
                    token_dict['original_text'] = one_token[0]
                    token_dict['pos'] = one_token[1]
                    token_dict['label'] = 'O'
                    token_dict['start_char'] = int(one_SEG.findall("TOKEN")[one_token_idx].attrib["start_char"])
                    token_dict['end_char'] = int(one_SEG.findall("TOKEN")[one_token_idx].attrib["end_char"]) + 1 # remember to +1 when you are doing with Python
                    for one_label_id in brat_annotation.annotation_dict['sequence_label']:
                        if token_dict['start_char'] >= brat_annotation.annotation_dict['sequence_label'][one_label_id]['start_char'] and token_dict['end_char'] <= brat_annotation.annotation_dict['sequence_label'][one_label_id]['end_char']:
                            if one_label_id not in used_dict:
                                used_flag = 0
                                used_dict[one_label_id] = dict()
                                used_dict[one_label_id]["start_token_idx"] = one_token_idx
                                used_dict[one_label_id]["span_length"] = 0
                            else:
                                used_flag = 1
                                used_dict[one_label_id]["span_length"] += 1
                            label_name = brat_annotation.annotation_dict['sequence_label'][one_label_id]['token_type']
                            if used_flag == 0:
                                token_dict['label'] = 'B-%s' % label_name
                            else:
                                token_dict['label'] = 'I-%s' % label_name
                            # if "_" not in label_name:
                            #     token_dict['label'] = 'O'
                    token_list.append(token_dict)

                # for one_event_annotation_id in
                for one_event_id in brat_annotation.annotation_dict['structure_label']:
                    if brat_annotation.annotation_dict['structure_label'][one_event_id]["event_trigger_id"] in used_dict:
                        # print(brat_annotation.annotation_dict['structure_label'][one_event_id])
                        trigger_info = used_dict[brat_annotation.annotation_dict['structure_label'][one_event_id]["event_trigger_id"]]
                        trigger_idx = trigger_info['start_token_idx']
                        token_list[trigger_idx]["arguments"] = list()
                        event_type = brat_annotation.annotation_dict['structure_label'][one_event_id]['event_type']
                        for one_argument in brat_annotation.annotation_dict['structure_label'][one_event_id]['argument_list']:
                            try:
                                argument_idx = used_dict[one_argument[1]]['start_token_idx']
                            except KeyError:
                                continue
                            argument_dict = dict()
                            one_argument_role = one_argument[0]
                            argument_offset = trigger_idx - argument_idx
                            argument_dict['role'] = one_argument_role
                            argument_dict['offset'] = argument_offset
                            token_list[trigger_idx]["arguments"].append(argument_dict)
                sentence_dict = dict()
                sentence_dict["sequence"] = token_list
                sentence_dict["depparse"] = self.__depparse_table(dep_parser_result_list[count_flag], len(token_list))
                sentence_list.append(sentence_dict)
                count_flag += 1
        return sentence_list

    def __original_table(self):
        root = ET.parse(self.file_path).getroot()
        document_root = root[0]
        sentence_list = list()
        for one_TEXT in document_root:
            for one_SEG in one_TEXT:
                token_list = list()
                for one_token in one_SEG.findall("TOKEN"):
                    token_list.append(one_token)
                sentence_list.append(token_list)
        return sentence_list

    def __depparse_table(self, dep_parser_result, sentence_length):
        depparse_table = dict()
        depparse_table["graph"] = dict()
        depparse_table["matrix"] = np.empty([sentence_length + 1, sentence_length + 1], dtype=object)
        if dep_parser_result is None:
            return depparse_table
        dep_parser, = dep_parser_result
        for one_node in dep_parser.nodes:
            one_dep_dict = dep_parser.nodes[one_node]
            governor = one_dep_dict['head']
            dependent = one_dep_dict['address']
            rel = one_dep_dict['rel']
            if dependent == 0:
                continue
            depparse_table["matrix"][governor, dependent] = "g-%s" % rel
            depparse_table["matrix"][dependent, governor] = "d-%s" % rel
            if governor not in depparse_table["graph"]:
                depparse_table["graph"][governor] = [dependent]
            else:
                depparse_table["graph"][governor].append(dependent)
            if dependent not in depparse_table["graph"]:
                depparse_table["graph"][dependent] = [governor]
            else:
                depparse_table["graph"][dependent].append(governor)
        return depparse_table