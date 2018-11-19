import networkx as nx
import spacy
from spacy.tokenizer import Tokenizer
import argparse


def concat_item(l_list):
    out_string = ""
    for item in l_list:
        out_string += (item + " ")
    return out_string.strip()


def shortest_dependency_length(whole_sen):
    model = spacy.load('en_core_web_sm')
    custom_tokenizer = Tokenizer(model.vocab, {}, None, None, None)
    model.tokenizer = custom_tokenizer

    edges = []
    entity_offset = []
    index = 0
    whole_sen = line.strip().split("\t")[0]
    sen = whole_sen.split(maxsplit=5)
    ori_sen = sen[5].strip()
    sentence = ori_sen.split(" ")
    entity_offset.append([int(sen[2]), int(sen[4])])
    parse_result = model(ori_sen)
    sub_graph = []
    sub_entity_concat = []
    token_concat = []
    graph = None
    for token in parse_result:
        token_concat.append('{0}-{1}'.format(token.lower_, token.i))
        for child in token.children:
            sub_graph.append(('{0}-{1}'.format(token.lower_, token.i),
                                      '{0}-{1}'.format(child.lower_, child.i)))
        if token.i in entity_offset[index]:
                    sub_entity_concat.append('{0}-{1}'.format(token.lower_, token.i))
                    assert token.lower_ == sentence[token.i].lower(), (sentence[token.i].lower(), token.lower_)
    edges.append(sub_graph)
    graph = nx.Graph(sub_graph)
    short_len = nx.shortest_path(graph, source=sub_entity_concat[0],
                                                      target=sub_entity_concat[1])
    return short_len


pattern_config = argparse.ArgumentParser(description='relation extraction')
pattern_config.add_argument("--eval_path", type=str,
                          help="eval path, 0928/en/")
pattern_params, _ = pattern_config.parse_known_args()

post_results = pattern_params.eval_path + "results_post.txt"
# pattern_file = "/data/m1/shig4/AIDA/post_process/ace_patterns.txt"
test_corpus = pattern_params.eval_path + "AIDA_plain_text.txt"
pattern_file = "aida_relation/data/sponsor_patterns"
other_label = "32"
sponsor_label = "35"
sen_length = 10
sponsor_results = pattern_params.eval_path + "results_post_sponsor.txt"
feature_set = []
stop_words = ["in order to"]
sim_feature_set = []
with open(pattern_file) as fmodel:
    for line in fmodel:
        feature_set.append(" "+line.strip())
        sim_feature_set.append(line.strip().lower())
type_constraint = ["ORG", "GPE", "LOC"]
####################################
# counting entity type constraints
####################################
label = []
score = []
sen_list = []
index_list = []
with open(post_results) as fmodel:
    for line in fmodel:
        temp = line.strip().split("\t")
        label.append(temp[0].strip())
        score.append(temp[1].strip())
num = 0
label_index = 0

with open(test_corpus) as fmodel:
    for line in fmodel:
        temp = line.strip().split("\t")
        temp_whole = temp[0].strip().split(" ", 5)
        mention1_offset = int(temp_whole[2].strip())
        mention2_offset = int(temp_whole[3].strip())
        relation = temp_whole[0].strip()
        e1_type, e2_type = temp[1].strip().split(" ")
        en_type = [e1_type.strip(), e2_type.strip()]
        whole_sentence = temp_whole[5].strip().split(" ")
        pattern = e1_type + " " + concat_item(whole_sentence[mention1_offset + 1: mention2_offset]) + " " + e2_type
        if e1_type in type_constraint and e2_type in type_constraint and label[label_index] == "32" and (
                mention2_offset - mention1_offset) < sen_length:
            flag = False
            whole_span = " " + concat_item(whole_sentence[mention1_offset + 1: mention2_offset])
            for item in feature_set:
                if item in whole_span:
                    # for item in concat_item(whole_sentence[mention1_offset + 1: mention2_offset]):
                    #     if item in feature_set:
                    flag = True
                    break
            if flag and "in order to" not in whole_span:
                # if shortest_dependency_length(line) < 5:
                sen_list.append(line)
                index_list.append(label_index)
                num += 1
        label_index += 1
print(num)
filter_num = 0
model = spacy.load('en_core_web_sm')
custom_tokenizer = Tokenizer(model.vocab, {}, None, None, None)
model.tokenizer = custom_tokenizer
for j, line in enumerate(sen_list):
    edges = []
    entity_offset = []
    index = 0
    whole_sen = line.strip().split("\t")[0]
    sen = whole_sen.split(maxsplit=5)
    ori_sen = sen[5].strip()
    sentence = ori_sen.split(" ")
    entity_offset.append([int(sen[2]), int(sen[4])])
    parse_result = model(ori_sen)
    sub_graph = []
    sub_entity_concat = []
    token_concat = []
    graph = None
    for token in parse_result:
        token_concat.append('{0}-{1}'.format(token.lower_, token.i))
        # print('{0}-{1}'.format(token.lower_, token.i))
        for child in token.children:
            sub_graph.append(('{0}-{1}'.format(token.lower_, token.i),
                                      '{0}-{1}'.format(child.lower_, child.i)))
        if token.i in entity_offset[index]:
                    sub_entity_concat.append('{0}-{1}'.format(token.lower_, token.i))
                    assert token.lower_ == sentence[token.i].lower(), (sentence[token.i].lower(), token.lower_)
    edges.append(sub_graph)
    graph = nx.Graph(sub_graph)
    try:
        short_path = nx.shortest_path(graph, source=sub_entity_concat[0], target=sub_entity_concat[1])
        for word_concat in token_concat:
            if word_concat.split("-")[0].strip() in sim_feature_set:
                # print(word_concat.split("-")[0].strip())
                filter_num += 1
                label[index_list[j]] = sponsor_label
                # print(index_list[j])
                break
    except:
        continue
# print(filter_num)

    # if short_len:
    #     label[index_list[j]] = sponsor_label
    #     # print(index_list[j])
    #     filter_num += 1
# print(filter_num)

with open(sponsor_results, "w", encoding="utf-8") as fmodel:
    for i, item in enumerate(label):
        fmodel.write(item + "\t" + score[i] + "\n")