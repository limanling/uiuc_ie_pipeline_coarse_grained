import os
import argparse
import xml.etree.ElementTree as ET

def location_sentence_id(ltf_dict_with_file_id, start_offset, end_offset):
    for one_entry in ltf_dict_with_file_id:
        sentence_id = one_entry[0]
        start_offset_in_reference = one_entry[1]
        end_offset_in_reference = one_entry[2]
        if start_offset >= start_offset_in_reference and end_offset-1 <= end_offset_in_reference:
            return sentence_id
    return 0

def time_ex_locator_dict_generator(ltf_dict, time_ex_path):
    time_expression_dict = dict()
    black_list = list()
    for one_line in open(time_ex_path):
        one_line = one_line.strip()
        one_line_list = one_line.split('\t')
        if len(one_line_list) == 3:
            if one_line_list[2] != 'TME':
                black_list.append(one_line_list[0])
            continue
        if one_line_list[0] in black_list:
            continue
        if '_mention' in one_line:
            continue
        print(one_line)
        search_key = one_line_list[3]
        filler_id = one_line_list[0]
        file_id = search_key.split(':')[0]
        if file_id not in time_expression_dict:
            time_expression_dict[file_id] = dict()
        start_offset = int(search_key.split(':')[1].split('-')[0])
        end_offset = int(search_key.split(':')[1].split('-')[1])
        sentence_id = location_sentence_id(ltf_dict[file_id], start_offset, end_offset)
        if sentence_id == 0:
            continue
        if sentence_id not in time_expression_dict[file_id]:
            time_expression_dict[file_id][sentence_id] = list()
        time_expression_dict[file_id][sentence_id].append((filler_id, search_key))
    return time_expression_dict

parser = argparse.ArgumentParser(description='Insert time expression into event extraction output')
parser.add_argument('-l', '--ltf', help='LTF folder path', required=True)
parser.add_argument('-f', '--filler', help='Filler file path', required=True)
parser.add_argument('-i', '--input_file_path', help='Input file path', required=True)
parser.add_argument('-o', '--output_file_path', help='Output file path', required=True)
args = vars(parser.parse_args())

ltf_source_path = args['ltf']
time_ex_path = args['filler']
event_input_path = args['input_file_path']
event_output_path = args['output_file_path']

ltf_dict = dict()
for one_file in os.listdir(ltf_source_path):
    one_ltf_path = os.path.join(ltf_source_path, one_file)
    one_file_id = one_file.replace('.ltf.xml', '')
    if one_file_id not in ltf_dict:
        ltf_dict[one_file_id] = list()
    one_root = ET.parse(one_ltf_path).getroot()
    for one_seg in one_root[0][0].findall('SEG'):
        segment_id = one_seg.attrib['id']
        start_char = int(one_seg.attrib['start_char'])
        end_char = int(one_seg.attrib['end_char'])
        ltf_dict[one_file_id].append((segment_id, start_char, end_char))

time_ex_locator_dict = time_ex_locator_dict_generator(ltf_dict, time_ex_path)

event_type_dict = dict()
to_write_list = list()
for one_line in open(event_input_path):
    one_line = one_line.strip()
    one_line_list = one_line.split('\t')
    if len(one_line_list) == 3:
        event_type_dict[one_line_list[0]] = one_line_list[-1]
        to_write_list.append(one_line)
        continue
    to_write_list.append(one_line)
    if 'canonical_mention' in one_line_list[1]:
        event_mention_id = one_line_list[0]
        search_key = one_line_list[3]
        file_id = search_key.split(':')[0]
        start_offset = int(search_key.split(':')[1].split('-')[0])
        end_offset = int(search_key.split(':')[1].split('-')[1])
        sentence_id = location_sentence_id(ltf_dict[file_id], start_offset, end_offset)
        if file_id not in time_ex_locator_dict:
            continue
        if sentence_id not in time_ex_locator_dict[file_id]:
            continue
        offset_difference = 0
        temp_string = ''
        for one_entry in time_ex_locator_dict[file_id][sentence_id]:
            current_argument_type = '%s_Time.actual' % event_type_dict[event_mention_id]
            argument_start_offset = int(one_entry[1].split(':')[1].split('-')[0])
            if offset_difference == 0:
                offset_difference = abs(argument_start_offset-start_offset)
            elif offset_difference < abs(argument_start_offset-start_offset):
                offset_difference = abs(argument_start_offset-start_offset)
            else:
                continue
            temp_string = "%s\t%s\t%s\t%s\t1.0" % (event_mention_id,
                                                   current_argument_type,
                                                   one_entry[0],
                                                   one_entry[1])
        if temp_string == '':
            continue
        to_write_list.append(temp_string)

f_w = open(event_output_path, 'w')
f_w.write('\n'.join(to_write_list))
f_w.close()
