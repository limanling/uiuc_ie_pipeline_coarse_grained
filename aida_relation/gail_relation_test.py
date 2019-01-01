import requests
import os
import json
import argparse
import io


parser = argparse.ArgumentParser(description='Call the aida relation API acquire output')
parser.add_argument('-l', '--list', help='LTF file list path', required=True)
parser.add_argument('-f', '--ltf_folder', help='LTF folder path', required=True)
parser.add_argument('-e', '--edl_cs', help='EDL CS file path', required=True)
parser.add_argument('-t', '--edl_tab', help='EDL tab file path', required=True)
parser.add_argument('-o', '--output_path', help='Output CS file path', required=True)
args = vars(parser.parse_args())

input_file_list_file_path = args['list']
input_ltf_folder_path = args['ltf_folder']
input_edl_cs_file_path = args['edl_cs']
input_edl_tab_file_path = args['edl_tab']
output_relation_output_file_path = args['output_path']

temp_dict = dict()
temp_dict['edl_cs'] = io.open(input_edl_cs_file_path, encoding='utf-8').read().strip("\n")
temp_dict['edl_tab'] = io.open(input_edl_tab_file_path, encoding='utf-8').read().strip("\n")
temp_dict['input'] = dict()
for one_line in io.open(input_file_list_file_path):
    one_line = one_line.strip()
    base_name = one_line.replace(".ltf.xml", "")
    one_ltf_xml_file_path = os.path.join(input_ltf_folder_path, one_line)
    temp_dict['input'][base_name] = io.open(one_ltf_xml_file_path, encoding="utf-8").read()

json_string = json.dumps(temp_dict)
# print(json_string)
r = requests.post('http://127.0.0.1:5000/aida_relation_en', json=json_string)
if r.status_code == 200:
    print("Successfully extracted relations")
    f = open(output_relation_output_file_path, 'w')
    f.write(r.text)
    f.close()
else:
    print(r.status_code)