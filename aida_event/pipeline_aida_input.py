from utils.common.ltf import LTF
from utils.text.text_data_feeder_aida import TextDataFeeder
from utils.common.io import *
from utils.text.stanford_nltk_wrapper import StanfordNLTKWrapper

import os
import pickle
import argparse
import shutil

parser = argparse.ArgumentParser(description='Prepare the input for aida event extractor')
parser.add_argument('-t', '--temp', help='Temporary folder to hold the dependency parser output', required=True)
parser.add_argument('-f', '--ltf_folder', help='LTF folder', required=True)
parser.add_argument('-l', '--list', help='LTF file list', required=True)
parser.add_argument('-o', '--output_folder', help='Output folder for preprocessed text data feeders', required=True)
args = vars(parser.parse_args())

# repository_folder = "data/repository"
# document_list_file_path = 'data/rico_hurricane/rico_en_lst'
# ltf_folder_path = 'data/rico_hurricane/rico_en'

repository_folder = args['temp']
if os.path.exists(repository_folder) is False:
    os.mkdir(repository_folder)
document_list_file_path = args['list']
ltf_folder_path = args['ltf_folder']
output_folder_path = args['output_folder']
if os.path.exists(output_folder_path) is False:
    os.mkdir(output_folder_path)
else:
    shutil.rmtree(output_folder_path)
    os.mkdir(output_folder_path)

dev_tdf = pickle.load(open("aida_event/data/argument_dev_tdf.pkl", "rb"))
snw = StanfordNLTKWrapper()

# Read Word2Vec model
print("Loading pretrained word embedding")
w2v_embedding_path = read_dict_from_json_file("aida_event/config/xmie.json")['common_tools']['word_embedding_path']
w2v_model = w2v_model_from_file(w2v_embedding_path)

document_count = len(open(document_list_file_path).read().split("\n"))

count_flag = 1

for one_line in open(document_list_file_path):
    max_length = 0
    one_line = one_line.strip()
    one_file_id = one_line.replace(".ltf.xml", "")
    print(one_file_id)
    print('%d out of %d files' % (count_flag, document_count))
    one_repository_path = os.path.join(repository_folder, '%s.pkl' % one_file_id)
    if os.path.exists(one_repository_path) is False:
        print("We don't have a file in repository!")
        one_file_path = os.path.join(ltf_folder_path, one_line)
        one_ltf = LTF(snw, one_file_path, brat_annotation_folder='brat/data/ere_argument')
        pickle.dump(one_ltf, open(one_repository_path, 'wb'))
    else:
        print("We have a file in repository!")
        one_ltf = pickle.load(open(one_repository_path, 'rb'))
    count_flag += 1

    test_raw_data_list = list()
    info_box = list()

    for one_instance in one_ltf.annotation_table:
        if len(one_instance['sequence']) > max_length:
            max_length = len(one_instance['sequence'])
            print("Max length updated! %d" % max_length)
        test_raw_data_list.append(one_instance)
    for one_instance in one_ltf.original_table:
        info_box.append((one_ltf.file_id, one_instance))

    test_tdf = TextDataFeeder(test_raw_data_list,
                              max_length=max_length+1,
                              token_idx_dict=dev_tdf.token_idx_dict,
                              pos_idx_dict=dev_tdf.pos_idx_dict,
                              dep_idx_dict=dev_tdf.dep_idx_dict,
                              word2vec_model=w2v_model,
                              char_idx_dict=dev_tdf.char_idx_dict,
                              config_file_path="aida_event/config/xmie.json")
    pickle.dump(test_tdf, open(os.path.join(output_folder_path, "%s.pkl" % one_file_id), "wb"))
    pickle.dump(info_box, open(os.path.join(output_folder_path, "%s_info.pkl" % one_file_id), "wb"))