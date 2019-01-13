import argparse
import codecs

parser = argparse.ArgumentParser(description='Final output to ColdStart++ including all components')
parser.add_argument('-e', '--edl', help='EDL output file', required=True)
parser.add_argument('-f', '--filler', help='Filler output file', required=True)
parser.add_argument('-r', '--relation', help='Relation output file', required=True)
parser.add_argument('-n', '--newrelation', help='New relation output file', required=True)
parser.add_argument('-v', '--event', help='Event output file', required=True)
parser.add_argument('-o', '--output_file', help='final output file', required=True)
args = vars(parser.parse_args())

edl_file_path = args['edl']
filler_file_path = args['filler']
relation_file_path = args['relation']
new_relation_file_path = args['newrelation']
event_file_path = args['event']
output_file_path = args['output_file']

uri_head = 'https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#'
mapping_file_path = 'aida_event/config/cs_to_aida_ontology_mapping.csv'
ontology_mapping_dict = dict()

for one_line in codecs.open(mapping_file_path, 'r', 'utf-8'):
    one_line = one_line.strip()
    ontology_mapping_dict[one_line.split(',')[0]] = one_line.split(',')[1]

# file_list = [edl_file_path, relation_file_path, event_file_path]

f_final = codecs.open(output_file_path, 'w', 'utf-8')

# EDL
for one_line in codecs.open(edl_file_path, 'r', 'utf-8'):
    one_line = one_line.strip()
    one_line_list = one_line.split('\t')
    if len(one_line_list) == 3 and one_line_list[1] == 'type':
        one_line_list[2] = ontology_mapping_dict[one_line_list[2]]
    new_line = '\t'.join(one_line_list)
    f_final.write('%s\n' % new_line)

# Filler

for one_line in codecs.open(filler_file_path, 'r', 'utf-8'):
    one_line = one_line.strip()
    one_line_list = one_line.split('\t')
    if len(one_line_list) == 3:
        if one_line_list[1] == 'type':
            one_line_list[2] = ontology_mapping_dict[one_line_list[2]]
            one_line = '\t'.join(one_line_list)
    f_final.write('%s\n' % one_line)

# Relation
for one_line in codecs.open(relation_file_path, 'r', 'utf-8'):
    one_line = one_line.strip()
    f_final.write('%s\n' % one_line)

for one_line in codecs.open(new_relation_file_path, 'r', 'utf-8'):
    one_line = one_line.strip()
    f_final.write('%s\n' % one_line)


# Event
for one_line in codecs.open(event_file_path, 'r', 'utf-8'):
    one_line = one_line.strip()
    one_line_list = one_line.split('\t')
    if len(one_line_list) == 3 and one_line_list[1] == 'type':
        one_line_list[2] = '%s%s' % (uri_head, one_line_list[2])
    elif len(one_line_list) == 5 and 'mention' not in one_line_list[1]:
        one_line_list[1] = '%s%s' % (uri_head, one_line_list[1])
    new_line = '\t'.join(one_line_list)
    f_final.write('%s\n' % new_line)

f_final.close()