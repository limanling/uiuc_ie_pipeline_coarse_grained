import requests
import os
import json

input_file_list_file_path = 'data/rico_hurricane/ltf_lst'
input_ltf_folder_path = 'data/rico_hurricane/ltf'

temp_dict = dict()
temp_dict['ltf_files'] = dict()
for one_line in open(input_file_list_file_path):
    one_line = one_line.strip()
    one_ltf_xml_file_path = os.path.join(input_ltf_folder_path, one_line)
    temp_dict['ltf_files'][one_line] = open(one_ltf_xml_file_path).read()

json_string = json.dumps(temp_dict)
r = requests.post('http://127.0.0.1:5233/aida_event_en_imitation', json=json_string)
print(r.status_code)