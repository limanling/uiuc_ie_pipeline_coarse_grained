import os
from collections import defaultdict
import shutil


full_cs = '/data/m1/lim22/aida2018/m9_new_ontology/ru/ru_full_xdoc.cs'
output_cs_separate_path = '/data/m1/lim22/aida2018/m9_new_ontology/ru/cs/'
if os.path.exists(output_cs_separate_path):
    shutil.rmtree(output_cs_separate_path)
os.makedirs(output_cs_separate_path)

# doc_info=defaultdict(list)
kb_doc_mapping = defaultdict(set)
lines = open(full_cs).readlines()
for line in lines:
    line = line.rstrip('\n')
    tabs = line.split('\t')
    if len(tabs) > 4:
        kb_id = tabs[0]
        offset = tabs[3]
        doc = offset[:offset.find(':')]
        # doc_info[doc].append(kb_id)
        kb_doc_mapping[kb_id].add(doc)

doc_lines=defaultdict(list)
for line in lines:
    line = line.rstrip('\n')
    tabs = line.split('\t')
    if len(tabs) == 3:
        for doc in kb_doc_mapping[tabs[0]]:
            doc_lines[doc].append(line)
    elif len(tabs) > 3:
        offset = tabs[3]
        doc_str = offset[:offset.find(':')]
        doc_lines[doc_str].append(line)

for doc in doc_lines:
    writer = open(os.path.join(output_cs_separate_path, '%s.cs' % doc), 'w')
    writer.write('RPI_BLENDER\n\n')
    for line in doc_lines[doc]:
        writer.write('%s\n' % line)
    writer.flush()
    writer.close()
