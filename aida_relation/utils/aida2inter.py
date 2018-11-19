import argparse
import sys
import xml.dom.minidom as xmldom
import xml.etree.ElementTree as ET
import os
import time


def mkdir(output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    else:
        print("%s is existed" % output_dir)


def assembly_list(l_list):
    new_list = []
    for i in range(len(l_list) - 1):
        for j in range(len(l_list) - i - 1):
            new_list.append([l_list[i], l_list[i + j + 1]])
    return new_list


#########################################################
# doc2mention --- HC000T6IX: [[1, 7], [38, 47], ....,]
# mention2type --- 'HC00007XV:187-192': 'GPE'
#########################################################
def doc_to_men_to_type(edl_result_path):
    mention2type = {}
    doc2mention = {}
    with open(edl_result_path) as fmodel:
        for line in fmodel:
            temp = line.strip().split("\t")
            doc_id, mention_offset = temp[3].strip().split(":")
            entity_type = temp[5].strip()
            mention_id = temp[3].strip()
            if mention_id not in mention2type:
                mention2type[mention_id] = entity_type
            if doc_id not in doc2mention:
                doc2mention[doc_id] = [mention_offset.split("-")]
            else:
                doc2mention[doc_id].append(mention_offset.split("-"))
    return doc2mention, mention2type


##############################################################################
# doc2segment --- {'HC00007XV': {'segment-0': [1, 48], 'segment-1': [52, 104]}}

# docseg2mention --- {'HC00002Y5': {'segment-0': [['1', '4'],['5','7']], 'segment-1': [['62', '68']}

# doc2segtext --- {'HC00002Y5': {'segment-0': ['MH17'], 'segment-1': ['While',
# 'western']}}

# doc2segoffset --- {'HC00002Y5': {'segment-0': [['1', '4'], ['5', '5'], ['7', '13']]}}
###############################################################################
def doc_to_segment(doc2men_dict, raw_data_path, raw_data_path1=None):
    doc2segment = {}
    docseg2mention = {}
    doc2segtext = {}
    doc2segoffset = {}
    for key in doc2men_dict:
        fpath = raw_data_path + key + ".ltf.xml"
        if not os.path.exists(fpath):
            fpath = raw_data_path1 + key + ".ltf.xml"
        domobj = xmldom.parse(fpath)
        elementobj = domobj.documentElement
        subElementObj = elementobj.getElementsByTagName("SEG")
        temp = {}
        for i in range(len(subElementObj)):
            temp[subElementObj[i].getAttribute("id")] = \
                [int(subElementObj[i].getAttribute("start_char")), int(subElementObj[i].getAttribute("end_char"))]
        doc2segment[key] = temp
        # doc2seg2mention
        temp_seg2mention_dict = {}
        for mention in doc2men_dict[key]:
            for seg in doc2segment[key]:
                if doc2segment[key][seg][0] <= int(mention[1]) <= doc2segment[key][seg][1]:
                    if seg not in temp_seg2mention_dict:
                        temp_seg2mention_dict[seg] = [mention]
                    else:
                        temp_seg2mention_dict[seg].append(mention)
        docseg2mention[key] = temp_seg2mention_dict
        # seg_to_text, seg_to_offset
        tree = ET.parse(fpath)
        root = tree.getroot()
        temp_seg_text = {}
        temp_seg_offset = {}
        for doc in root:
            for text in doc:
                for seg in text:
                    if seg.attrib["id"] not in temp_seg_text:
                        temp_seg_text[seg.attrib["id"]] = []
                        temp_seg_offset[seg.attrib["id"]] = []
                    for token in seg:
                        if token.tag == "TOKEN":
                            temp_seg_text[seg.attrib["id"]].append(token.text)
                            temp_seg_offset[seg.attrib["id"]].append([token.attrib["start_char"],
                                                                      token.attrib["end_char"]])
        doc2segtext[key] = temp_seg_text
        doc2segoffset[key] = temp_seg_offset
    return doc2segment, docseg2mention, doc2segtext, doc2segoffset


def doc_to_offset(f_list, raw_data_path, raw_data_path1=None):
    temp_doc_offset = {}
    for item in f_list:
        fpath = raw_data_path + item + ".ltf.xml"
        if not os.path.exists(fpath):
            fpath = raw_data_path1 + item + ".ltf.xml"
        tree = ET.parse(fpath)
        root = tree.getroot()
        for doc in root:
            for text in doc:
                for seg in text:
                    for token in seg:
                        if token.tag == "TOKEN":
                            if item not in temp_doc_offset:
                                temp_doc_offset[item] = [token.attrib["end_char"]]
                            else:
                                temp_doc_offset[item].append(token.attrib["end_char"])
    return temp_doc_offset


if __name__ == '__main__':
    # print(params)
    convert_AIDA_config = argparse.ArgumentParser(description='convert to intermediate format')
    # paths
    convert_AIDA_config.add_argument("--output_file",
                                     type=str,
                                     default="AIDA_plain_text.txt",
                                     help="the converted intermediate results")

    convert_AIDA_config.add_argument("--max_sen_len",
                                     type=str,
                                     default=121,
                                     help="max sentence length")

    convert_AIDA_config.add_argument("--ltf_data_path",
                                     type=str,
                                     default="",
                                     help="raw data path")

    convert_AIDA_config.add_argument("--edl_result_path",
                                     type=str,
                                     default="",
                                     help="entity linking results from boliang and xiaoman")

    convert_AIDA_config.add_argument("--output_dir",
                                     type=str,
                                     default="",
                                     help="output dir")

    params, _ = convert_AIDA_config.parse_known_args()

    configs = {
        'edl_result_path': params.edl_result_path,
        'ltf_data_path': params.ltf_data_path,
        'output_dir': params.output_dir,
        'output_file': params.output_file,
        'max_sen_len': params.max_sen_len
    }

    start_time = time.clock()
    doc2mention, mention2type = doc_to_men_to_type(configs['edl_result_path'])
    doc2segment, docseg2mention, doc2segtext, doc2segoffset = doc_to_segment(doc2mention, configs['ltf_data_path'])
    error = 0
    mkdir(configs['output_dir'])
    with open(configs['output_dir'] + configs['output_file'], "w") as fmodel:
        for doc_id in docseg2mention:
            for segment in docseg2mention[doc_id]:
                list_offset = []
                for i in range(len(docseg2mention[doc_id][segment])):
                    if docseg2mention[doc_id][segment][i] in doc2segoffset[doc_id][segment]:
                        mention_loffset = doc2segoffset[doc_id][segment].index(docseg2mention[doc_id][segment][i])
                        list_offset.append([mention_loffset, mention_loffset])
                    else:
                        temp = []
                        for j in range(len(doc2segoffset[doc_id][segment])):
                            if docseg2mention[doc_id][segment][i][0] in doc2segoffset[doc_id][segment][j]:
                                temp.append(j)
                            if docseg2mention[doc_id][segment][i][1] in doc2segoffset[doc_id][segment][j]:
                                temp.append(j)
                        list_offset.append(temp)
                list_offset = sorted(list_offset)
                out_list = assembly_list(list_offset)
                if out_list:
                    for item in out_list:
                        if len(doc2segtext[doc_id][segment]) < configs['max_sen_len']:
                            try:
                                ltf_mention1 = doc_id + ":" + doc2segoffset[doc_id][segment][item[0][0]][0] + "-" + \
                                           doc2segoffset[doc_id][segment][item[0][1]][1]
                                ltf_mention2 = doc_id + ":" + doc2segoffset[doc_id][segment][item[1][0]][0] + "-" + \
                                           doc2segoffset[doc_id][segment][item[1][1]][1]
                            except:
                                print(doc_id)
                                error += 1
                                continue
                            output_sentence = ""
                            for word in doc2segtext[doc_id][segment]:
                                output_sentence += (word + " ")
                            output_seg = doc_id + ":" + str(doc2segment[doc_id][segment][0]) + "-" + \
                                         str(doc2segment[doc_id][segment][1])
                            output_sentence = output_sentence.strip()
                            if item[0][1] != item[1][0]:
                                fmodel.write("1" + " " + str(item[0][0]) + " " + str(item[0][1]) + " " +
                                         str(item[1][0]) + " " + str(item[1][1]) + " "
                                         + output_sentence + "\t" + mention2type[ltf_mention1] + " " + mention2type[
                                             ltf_mention2]
                                         + "\t" + ltf_mention1 + " " + ltf_mention2 + "\t" + output_seg + "\n")
                # # find back the ltf offset
    end_time = time.clock()
    print(error)
    print("Preprocess running time is: %s" % str(end_time - start_time))
