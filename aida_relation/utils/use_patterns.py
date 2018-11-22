import os
import argparse

pattern_config = argparse.ArgumentParser(description='relation extraction')
pattern_config.add_argument("--eval_path", type=str,
                          help="eval path, 0928/en/")
pattern_params, _ = pattern_config.parse_known_args()

train_corpus = "aida_relation/data/ere_filtered_train.txt"
test_corpus = os.path.join(pattern_params.eval_path, "AIDA_plain_text.txt")
system_results = os.path.join(pattern_params.eval_path, "AIDA_results.txt")
pattern_file = "aida_relation/data/ere_pattern.txt"
other_label = "32"
new_results_file = os.path.join(pattern_params.eval_path, "results_post.txt")

####################################
# counting entity type constraints
####################################

rel2type = {}
with open(train_corpus) as fmodel:
    for line in fmodel:
        whole = line.strip().split("\t")
        en_type = whole[1].strip().split(" ")
        en_type[0] = en_type[0].strip()
        en_type[1] = en_type[1].strip()
        rel = whole[0].strip().split(" ", 1)[0].strip()
        if rel not in rel2type:
            rel2type[rel] = [rel2type]
        else:
            if en_type not in rel2type[rel]:
                rel2type[rel].append(en_type)

# print(rel2type)
def concat_item(l_list):
    out_string = ""
    for item in l_list:
        out_string += (item + " ")
    return out_string.strip()


relation_patterns = {}
ace_rel_type_dic = {u'PART-WHOLE_Artifact(Arg-1,Arg-2)': 28, u'ORG-AFF_Investor-Shareholder(Arg-1,Arg-2)': 12,
                    u'ORG-AFF_Sports-Affiliation(Arg-1,Arg-2)': 21,
                    u'ORG-AFF_Membership(Arg-1,Arg-2)': 18, u'ORG-AFF_Employment(Arg-2,Arg-1)': 8,
                    u'ART_User-Owner-Inventor-Manufacturer(Arg-2,Arg-1)': 14,
                    u'ORG-AFF_Investor-Shareholder(Arg-2,Arg-1)': 9, u'PER-SOC_Business(Arg-1,Arg-1)': 23,
                    u'GEN-AFF_Org-Location(Arg-2,Arg-1)': 5,
                    u'PART-WHOLE_Subsidiary(Arg-2,Arg-1)': 4, u'ORG-AFF_Founder(Arg-2,Arg-1)': 27,
                    u'PART-WHOLE_Artifact(Arg-2,Arg-1)': 31, u'ORG-AFF_Membership(Arg-2,Arg-1)': 24,
                    u'ART_User-Owner-Inventor-Manufacturer(Arg-1,Arg-2)': 13, u'PHYS_Near(Arg-1,Arg-1)': 16,
                    u'GEN-AFF_Citizen-Resident-Religion-Ethnicity(Arg-1,Arg-2)': 17,
                    u'PART-WHOLE_Subsidiary(Arg-1,Arg-2)': 11, u'PER-SOC_Lasting-Personal(Arg-1,Arg-1)': 20,
                    u'PART-WHOLE_Geographical(Arg-1,Arg-2)': 0,
                    u'GEN-AFF_Org-Location(Arg-1,Arg-2)': 6, u'ORG-AFF_Founder(Arg-1,Arg-2)': 25,
                    u'ORG-AFF_Student-Alum(Arg-1,Arg-2)': 22,
                    u'GEN-AFF_Citizen-Resident-Religion-Ethnicity(Arg-2,Arg-1)': 7,
                    u'ORG-AFF_Ownership(Arg-2,Arg-1)': 30,
                    u'ORG-AFF_Ownership(Arg-1,Arg-2)': 29,
                    u'ORG-AFF_Employment(Arg-1,Arg-2)': 10, u'PER-SOC_Family(Arg-1,Arg-1)': 15,
                    u'ORG-AFF_Student-Alum(Arg-2,Arg-1)': 19, u'NO-RELATION(Arg-1,Arg-1)': 1,
                    u'ORG-AFF_Sports-Affiliation(Arg-2,Arg-1)': 26, u'PHYS_Located(Arg-1,Arg-1)': 2,
                    u'PART-WHOLE_Geographical(Arg-2,Arg-1)': 3}
ere_rel_type_dic = {'physical_locatednear(Arg-1,Arg-2)': 0,
                    'physical_locatednear(Arg-2,Arg-1)': 1,
                    'physical_resident(Arg-1,Arg-2)': 2,
                    'physical_resident(Arg-2,Arg-1)': 3,
                    'physical_orgheadquarter(Arg-1,Arg-2)': 4,
                    'physical_orgheadquarter(Arg-2,Arg-1)': 5,
                    'physical_orglocationorigin(Arg-1,Arg-2)': 6,
                    'physical_orglocationorigin(Arg-2,Arg-1)': 7,
                    'partwhole_subsidiary(Arg-1,Arg-2)': 8,
                    'partwhole_subsidiary(Arg-2,Arg-1)': 9,
                    'partwhole_membership(Arg-1,Arg-2)': 10,
                    'partwhole_membership(Arg-2,Arg-1)': 11,
                    'personalsocial_business(Arg-1,Arg-2)': 12,
                    'personalsocial_business(Arg-2,Arg-1)': 12,
                    'personalsocial_family(Arg-1,Arg-2)': 13,
                    'personalsocial_family(Arg-2,Arg-1)': 13,
                    'personalsocial_unspecified(Arg-1,Arg-2)': 14,
                    'personalsocial_unspecified(Arg-2,Arg-1)': 14,
                    'personalsocial_role(Arg-1,Arg-2)': 15,
                    'personalsocial_role(Arg-2,Arg-1)': 15,
                    'orgaffiliation_employmentmembership(Arg-1,Arg-2)': 16,
                    'orgaffiliation_employmentmembership(Arg-2,Arg-1)': 17,
                    'orgaffiliation_leadership(Arg-1,Arg-2)': 18,
                    'orgaffiliation_leadership(Arg-2,Arg-1)': 19,
                    'orgaffiliation_investorshareholder(Arg-1,Arg-2)': 20,
                    'orgaffiliation_investorshareholder(Arg-2,Arg-1)': 21,
                    'orgaffiliation_studentalum(Arg-1,Arg-2)': 22,
                    'orgaffiliation_studentalum(Arg-2,Arg-1)': 23,
                    'orgaffiliation_ownership(Arg-1,Arg-2)': 24,
                    'orgaffiliation_ownership(Arg-2,Arg-1)': 25,
                    'orgaffiliation_founder(Arg-1,Arg-2)': 26,
                    'orgaffiliation_founder(Arg-2,Arg-1)': 27,
                    'generalaffiliation_more(Arg-1,Arg-2)': 28,
                    'generalaffiliation_more(Arg-2,Arg-1)': 29,
                    'generalaffiliation_opra(Arg-1,Arg-2)': 30,
                    'generalaffiliation_opra(Arg-2,Arg-1)': 31,
                    'NO-RELATION(Arg-1,Arg-1)': 32,
                    'generalaffiliation_apora(Arg-1,Arg-2)': 33,
                    'generalaffiliation_apora(Arg-2,Arg-1)': 34,
                    'sponsorship(Arg-1,Arg-2)': 35,
                    'sponsorship(Arg-2,Arg-1)': 36,
                    }
label = []
score = []
with open(system_results) as fmodel:
    for line in fmodel:
        temp = line.strip().split("\t")
        label.append(temp[0].strip())
        score.append(temp[1].strip())

with open(pattern_file) as fmodel:
    for line in fmodel:
        whole = line.strip().split("\t")
        if whole[0].strip() not in relation_patterns:
            relation_patterns[whole[0].strip()] = [whole[1].strip()]
        else:
            relation_patterns[whole[0].strip()].append(whole[1].strip())
line_index = 0
fixed_type_num = 0
rel_num = 0
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
        try:
            extend_pattern = whole_sentence[mention1_offset - 1] + " " + pattern
        except:
            extend_pattern = None
        # filter results by extracted patterns and extended patterns
        for key in relation_patterns:
            if pattern in relation_patterns[key]:
                label[line_index] = str(ere_rel_type_dic[key])
            if extend_pattern in relation_patterns[key]:
                label[line_index] = str(ere_rel_type_dic[key])
        # filter results by type constraints
        try:
            if en_type not in rel2type[label[line_index]] and label[line_index] != other_label:
                label[line_index] = other_label
                fixed_type_num += 1
        except:
            continue
        if label[line_index] != other_label:
            rel_num += 1
        line_index += 1
        ##############
        # Sponsor relation
        ##############

with open(new_results_file, "w", encoding="utf-8") as fmodel:
    for i, item in enumerate(label):
        fmodel.write(item + "\t" + score[i] + "\n")
print("fixed num is %d" % fixed_type_num)
print("relation num is %d" % rel_num)
