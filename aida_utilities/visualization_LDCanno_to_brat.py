import os
import argparse
from collections import defaultdict

parser = argparse.ArgumentParser(description='Convert the visualization to brat file')
parser.add_argument('-i', '--input_anno_file', help='Input file path', required=True)
parser.add_argument('-o', '--output_folder_path', help='Output folder path', required=True)
args = vars(parser.parse_args())

input_anno_file = args['input_anno_file']
output_brat_folder = args['output_folder_path']

try:
    os.mkdir(output_brat_folder)
except:
    pass

for one_file in os.listdir(output_brat_folder):
    if '.rsd.ann' in one_file:
        one_file_path = os.path.join(output_brat_folder, one_file)
        os.remove(one_file_path)

uri_head = 'https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#'

entity_dict = dict()
event_dict = dict()
file_content_dict = dict()

T_flag = 1
E_flag = 1

entity_mention_dict = dict()
trigger_mention_dict = dict()
# arc_dict = dict()
arc_dict = defaultdict(lambda: defaultdict(str))
# T_flag_dict = dict()
# for ent: T_flag_dict[ent_id][doc_id][flag_name] = int(start_offset)
# for evt: T_flag_dict[evt_men_id][doc_id][flag_name] = int(start_offset)
T_flag_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# entity
# P103_ent_mentions.tab
# tree_id	entitymention_id	entity_id	provenance	textoffset_startchar	textoffset_endchar	text_string	justification	type	level	kb_id
ent_mentions_file = os.path.join(input_anno_file, 'P103_ent_mentions.tab')
ent_men_dict = {}
for one_line in open(ent_mentions_file):
    one_line = one_line.strip('\n')
    strs = one_line.split('\t')
    # print(one_line)
    # print(strs[0], len(strs))
    type_info = strs[8]
    doc_id = strs[3]
    start_offset = strs[4]
    try:
        end_offset = int(strs[5])
    except:
        continue
    ent_id = strs[2]

    # ent_men_id = strs[1]
    # ent_men_dict[ent_id] = ent_men_id
    # print(doc_id)
    # if doc_id not in file_content_dict:
    #     f_read = open(os.path.join(output_brat_folder, '%s.rsd.txt' % doc_id))
    #     f_content = f_read.read()
    #     file_content_dict[doc_id] = f_content
    #     f_read.close()
    # text_string = file_content_dict[doc_id][start_offset:(end_offset+1)]
    text_string = strs[6]
    f_write = open(os.path.join(output_brat_folder, '%s.rsd.ann' % doc_id),'a')
    flag_name = "T%d" % T_flag
    T_flag += 1
    # print(flag_name)
    # print(str(start_offset))
    # print(str(end_offset + 1))
    # one_temp_line = '%s\t%s %d %d\t%s\n' % (str(flag_name), str(type_info), str(start_offset), str(end_offset+1), str(text_string.replace('\n', ' ')))
    one_temp_line = flag_name + '\t' + type_info + ' ' + str(start_offset) + ' ' +str(end_offset + 1) +'\t'+ text_string.replace('\n', ' ') +'\n'
    T_flag_dict[ent_id][doc_id][flag_name] = int(start_offset)
    f_write.write(one_temp_line)
    f_write.close()

# Relation
# P103_rel_slots.tab
# tree_id	relationmention_id	slot_type	arg_id
# P103_rel_mentions.tab
# tree_id	relationmention_id	relation_id	provenance	textoffset_startchar	textoffset_endchar	text_string	justification	type	subtype	attribute	start_date_type	start_date	end_date_type	end_date	kb_id


# Trigger
# P103_evt_mentions.tab
# tree_id	eventmention_id	event_id	provenance	textoffset_startchar	textoffset_endchar	text_string	justification	type	subtype	attribute	attribute2	start_date_type	start_date	end_date_type	end_date	kb_id	political_status
evt_mentions_file = os.path.join(input_anno_file, 'P103_evt_mentions.tab')
evt_men_doc = {}
evt_type_dict = {}
for one_line in open(evt_mentions_file):
    one_line = one_line.strip('\n')
    strs = one_line.split('\t')
    type_info = strs[8]
    doc_id = strs[3]
    try:
        start_offset = int(strs[4])
        end_offset = int(strs[5])
    except:
        continue
    evt_men_id = strs[1]
    evt_men_doc[evt_men_id] = doc_id
    evt_type_dict[evt_men_id] = type_info
    # if doc_id not in file_content_dict:
    #     f_read = open(os.path.join(output_brat_folder, '%s.rsd.txt' % doc_id))
    #     f_content = f_read.read()
    #     file_content_dict[doc_id] = f_content
    #     f_read.close()
    # text_string = file_content_dict[doc_id][start_offset:end_offset + 1]
    text_string = strs[6]
    f_write = open(os.path.join(output_brat_folder, '%s.rsd.ann' % doc_id),'a')
    flag_name = "T%d" % T_flag
    T_flag += 1
    one_temp_line = '%s\t%s %d %d\t%s\n' % (flag_name, type_info, start_offset, (end_offset+1), text_string.replace('\n', ' '))
    T_flag_dict[evt_men_id][doc_id][flag_name] = int(start_offset)
    f_write.write(one_temp_line)
    f_write.close()

# Argument
# P103_evt_slots.tab
# tree_id	eventmention_id	slot_type	attribute	arg_id
evt_slot_file = os.path.join(input_anno_file, 'P103_evt_slots.tab')
for one_line in open(evt_slot_file):
    one_line = one_line.strip('\n')
    strs = one_line.split('\t')
    evt_men = strs[1]  # event mention
    try:
        doc_id = evt_men_doc[evt_men] # no start and end
    except:
        continue

    # for ent: T_flag_dict[ent_id][doc_id][flag_name] = int(start_offset)
    # for evt: T_flag_dict[evt_men_id][doc_id][flag_name] = int(start_offset)
    for _ in T_flag_dict[evt_men][doc_id]:
        event_trigger_flag_offset = T_flag_dict[evt_men][doc_id][_]
    role_name = strs[2]
    argument_flag_dict = {}
    for ent_flag in T_flag_dict[strs[4]][doc_id]:
        # print(ent_flag)
        offset = abs(T_flag_dict[strs[4]][doc_id][ent_flag] - event_trigger_flag_offset)
        argument_flag_dict[ent_flag] = offset
    # print(argument_flag_dict)
    argument_flag_name = sorted(argument_flag_dict, key=lambda x: len(x[1]), reverse=False) #[0][0]
    arc_dict[evt_men][role_name] = argument_flag_name
    # print(argument_flag_dict)
    # print('-------------------')

print(arc_dict)
for evt_men in arc_dict:
    one_temp_line_list = list()
    event_type = evt_type_dict[evt_men]
    try:
        doc_id = evt_men_doc[evt_men]
    except:
        continue
    for _ in T_flag_dict[evt_men][doc_id]:
        event_trigger_flag_name = _
        one_temp_line_list.append('%s:%s' % (event_type, event_trigger_flag_name))
    for role_name in arc_dict[evt_men]:
        if (len(arc_dict[evt_men][role_name]) <= 0):
            continue
        print('-------')
        print(arc_dict[evt_men])
        argument_flag_name = arc_dict[evt_men][role_name][0]
        print('argument_flag_name', argument_flag_name)
        print('role_name', role_name)
        one_temp_line_list.append('%s:%s' % (role_name, argument_flag_name))
    flag_name = "E%d" % E_flag
    one_temp_line = '%s\t%s\n' % (flag_name, ' '.join(one_temp_line_list))
    E_flag += 1
    f_write = open(os.path.join(output_brat_folder, '%s.rsd.ann' % doc_id),'a')
    f_write.write(one_temp_line)
    f_write.close()