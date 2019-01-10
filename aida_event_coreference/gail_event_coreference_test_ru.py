import requests
import os
import json
import argparse
import io

# input_event_cs_file_path = 'uk_events_eval.cs'
# output_event_coreference_output_file_path = 'test_test.cs'

parser = argparse.ArgumentParser(description='Call the aida event coreference API acquire output')
parser.add_argument('-i', '--event_cs', help='Event CS file path', required=True)
parser.add_argument('-o', '--output_path', help='Event Corference CS output file path', required=True)
args = vars(parser.parse_args())

input_event_cs_file_path = args['event_cs']
output_event_coreference_output_file_path = args['output_path']

temp_dict = dict()
with open(input_event_cs_file_path) as f:
	temp_dict['event_cs'] = f.readlines()

json_string = json.dumps(temp_dict)
r = requests.post('http://127.0.0.1:6100/aida_event_coreference_rus', json=json_string)
if r.status_code == 200:
    print("Successfully extracted events")
    f = io.open(output_event_coreference_output_file_path, 'w')
    f.write(r.text)
    f.close()
else:
    print(r.status_code)
