import argparse

parser = argparse.ArgumentParser(description='Final output to ColdStart++ including all components')
parser.add_argument('-e', '--edl', help='EDL output file', required=True)
parser.add_argument('-r', '--relation', help='Relation output file', required=True)
parser.add_argument('-v', '--event', help='Event output file', required=True)
parser.add_argument('-o', '--output_file', help='final output file', required=True)
args = vars(parser.parse_args())

edl_file_path = args['edl']
relation_file_path = args['relation']
event_file_path = args['event']
output_file_path = args['output_file']

file_list = [edl_file_path, relation_file_path, event_file_path]

f_final = open(output_file_path, 'w', encoding='utf-8')
for one_path in file_list:
    for one_line in open(one_path, encoding='utf-8'):
        one_line = one_line.strip()
        f_final.write('%s\n' % one_line)

f_final.close()