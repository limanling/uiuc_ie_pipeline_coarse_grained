# This module is for evaluation
import json
import copy
import numpy as np
import pickle
from utils.common.processing import label_preprocessor, label_normalizer, recover_label, category_detector, \
    purge_none_argument, label_index_to_label_name, find_dep_path
from utils.common.io import read_dict_from_json_file, read_list_from_file


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)  # only difference


def evaluation_pipeline(learning_core, data_feeder, new_info_box):
    sequence_evaluation_list = list()
    argument_evaluation_list = list()
    entity_type_list = ['Entity.PER',
                        'Entity.ORG',
                        'Entity.LOC',
                        'Entity.GPE',
                        'Entity.FAC',
                        'Entity.VEH',
                        'Entity.WEA']
    batch_size = 128
    global_index_offset = 0

    while data_feeder.epoch < 1:
        print("Tested: %d" % global_index_offset)
        input_batch = data_feeder.next_batch(batch_size=batch_size)
        sentence_list = list()
        argument_sentence_list = list()
        # forward_dict = {learning_core.token_id_input: input_batch["token_id"],
        #                 learning_core.pos_id_input: input_batch["pos_id"],
        #                 learning_core.char_id_input: input_batch["char_id"],
        #                 learning_core.word_length_input: input_batch["word_length"],
        #                 learning_core.pretrained_embedding_input: input_batch["embedding"],
        #                 learning_core.sequence_length_input: input_batch["sequence_length"]}
        predict_results, predict_scores, context_representation = learning_core.predict_sequence(input_batch)
        for idx, one_result in enumerate(predict_results.tolist()):
            one_sentence_list = list()
            sequence_length = input_batch["sequence_length"][idx]
            usable_sequence_score = predict_scores[idx, :sequence_length, :]
            confidence_score = softmax(usable_sequence_score)
            one_prediction_label_list = recover_label(one_result, config_path="aida_event/config/xmie.json")[:sequence_length]
            one_groundtruth_list = input_batch["label_index"][idx]
            one_groundtruth_label_list = recover_label(one_groundtruth_list, config_path="aida_event/config/xmie.json")[
                                         :sequence_length]
            for token_idx in range(sequence_length):
                token_dict = dict()
                # TODO: change the token_surface and make it from raw data.
                token_dict['token_raw'] = data_feeder.raw_data_list[idx + global_index_offset]['sequence'][token_idx][
                    'original_text']
                token_dict['token_surface'] = data_feeder.token_idx_dict.idx2word(
                    input_batch["token_id"][idx][token_idx])
                token_dict['token_prediction'] = one_prediction_label_list[token_idx]
                token_dict['token_groundtruth'] = one_groundtruth_label_list[token_idx]
                token_dict['confidence_score'] = (confidence_score[token_idx, one_result[token_idx]] + np.max(
                    confidence_score[token_idx, :])) / 2
                token_dict['edl_result'] = new_info_box[idx + global_index_offset][1][token_idx][2]
                if "Entity" in token_dict['token_prediction']:
                    token_dict['token_prediction'] = 'O'
                if token_dict['edl_result'] != 'O':
                    BI_tag = token_dict['edl_result'].split("-")[0]
                    entity_tag = token_dict['edl_result'].split("-")[1]
                    token_dict['token_prediction'] = "%s-Entity.%s" % (BI_tag, entity_tag)
                one_sentence_list.append(token_dict)

            sequence_evaluation_list.append(one_sentence_list)
            one_sentence = copy.deepcopy(one_sentence_list)
            sentence_list.append(one_sentence)

        # TODO: obtain the arguments
        argument_queue_dict = dict()
        for idx, one_sentence in enumerate(sentence_list):
            one_sentence_argument_dict = dict()
            one_sentence_argument_dict["argument_groundtruth"] = input_batch["argument_label"][idx]
            one_sentence_argument_dict["argument_prediction"] = list()
            argument_sentence_list.append(one_sentence_argument_dict)

            label_preprocessor(one_sentence, "token_prediction")
            label_preprocessor(one_sentence, "token_groundtruth")

            entity_candidate_list = list()
            trigger_candidate_list = list()
            for word_idx, one_word in enumerate(one_sentence):
                if one_word['token_prediction'] is 'O':
                    continue
                if "I-" in one_word['token_prediction']:
                    continue
                if "Entity." in one_word['token_prediction']:
                    entity_candidate_list.append(word_idx)
                    # print(one_word)
                else:
                    trigger_candidate_list.append(word_idx)

            for one_trigger_idx in trigger_candidate_list:
                word_idx = one_trigger_idx
                event_type = category_detector(one_sentence[word_idx]["token_prediction"])
                for one_entity_idx in entity_candidate_list:
                    argument_info_list = list()
                    entity_idx = one_entity_idx
                    argument_offset_length = search_phrase_tail(entity_idx, one_sentence)
                    argument_info_list.append(word_idx)
                    argument_info_list.append(entity_idx)
                    argument_info_list.append(argument_offset_length)
                    argument_info_list.append(event_type)
                    # print(argument_info_list)
                    if event_type not in argument_queue_dict:
                        argument_queue_dict[event_type] = list()
                    argument_queue_dict[event_type].append((idx, argument_info_list))

        for one_event_type in argument_queue_dict:
            argument_role_list = learning_core.argument_role_dict[one_event_type]
            argument_info_list = argument_queue_dict[one_event_type]

            trigger_embedding_list = list()
            argument_embedding_list = list()
            argument_entity_type_input_list = list()

            left_context_embedding_input = list()
            left_context_length_input = list()

            middle_context_embedding_input = list()
            middle_context_length_input = list()

            right_context_embedding_input = list()
            right_context_lenght_input = list()

            dep_id_input_list = list()
            dep_length_list = list()

            for one_argument_tuple in argument_queue_dict[one_event_type]:
                one_batch_idx = one_argument_tuple[0]
                one_argument_info = one_argument_tuple[1]
                one_trigger_index = one_argument_info[0]
                trigger_embedding_list.append(context_representation[one_batch_idx, one_trigger_index, :])
                one_argument_index = one_argument_info[1] + one_argument_info[2]
                argument_embedding_list.append(context_representation[one_batch_idx, one_argument_index, :])

                one_argument_entity_type_vector = np.zeros([7], dtype=np.float32)
                token_prediction_type = category_detector(
                    sentence_list[one_batch_idx][one_argument_info[1]]['token_prediction'])
                one_entity_type_index = entity_type_list.index(token_prediction_type)
                if one_entity_type_index >= 0:
                    one_argument_entity_type_vector[one_entity_type_index] = 1
                argument_entity_type_input_list.append(one_argument_entity_type_vector)

                if one_trigger_index < one_argument_index:
                    left_index = one_trigger_index
                    right_index = one_argument_index
                else:
                    right_index = one_trigger_index
                    left_index = one_argument_index
                one_left_embedding = np.zeros([data_feeder.max_length, 2 * learning_core.token_lstm_memory],
                                              dtype=np.float32)
                one_left_length = left_index + 1
                one_left_embedding[0:one_left_length, :] = context_representation[one_batch_idx, 0:left_index + 1, :]
                left_context_embedding_input.append(one_left_embedding)
                left_context_length_input.append(one_left_length)

                one_middle_embedding = np.zeros([data_feeder.max_length, 2 * learning_core.token_lstm_memory],
                                                dtype=np.float32)
                one_middle_length = right_index - left_index + 1
                one_middle_embedding[0:one_middle_length, :] = context_representation[one_batch_idx,
                                                               left_index:right_index + 1, :]
                middle_context_embedding_input.append(one_middle_embedding)
                middle_context_length_input.append(one_middle_length)

                one_right_embedding = np.zeros([data_feeder.max_length, 2 * learning_core.token_lstm_memory],
                                               dtype=np.float32)
                one_right_length = input_batch["sequence_length"][one_batch_idx] - right_index + 1
                one_right_embedding[0:one_right_length, :] = context_representation[one_batch_idx,
                                                             right_index:input_batch["sequence_length"][
                                                                             one_batch_idx] + 1,
                                                             :]
                right_context_embedding_input.append(one_right_embedding)
                right_context_lenght_input.append(one_right_length)
                dep_list = list()
                try:
                    dep_list = find_dep_path(one_trigger_index, one_argument_index,
                                             input_batch['dep_id'][one_batch_idx])
                    if len(dep_list) == 0:
                        dep_list.append(1)
                except:
                    dep_list.append(1)
                one_dep_id_input = np.zeros([data_feeder.max_length], dtype=np.int32)
                one_dep_id_input[0:len(dep_list)] = np.array(dep_list, dtype=np.int32)
                dep_id_input_list.append(one_dep_id_input)
                dep_length_list.append(len(dep_list))

            argument_forward_dict = {
                learning_core.trigger_embedding: np.array(trigger_embedding_list),
                learning_core.argument_embedding: np.array(argument_embedding_list),
                learning_core.argument_entity_type: np.array(argument_entity_type_input_list),
                learning_core.left_context_embedding: np.array(left_context_embedding_input),
                learning_core.left_context_length: np.array(left_context_length_input),
                learning_core.middle_context_embedding: np.array(middle_context_embedding_input),
                learning_core.middle_context_length: np.array(middle_context_length_input),
                learning_core.right_context_embedding: np.array(right_context_embedding_input),
                learning_core.right_context_length: np.array(right_context_lenght_input),
                learning_core.dep_id_input: np.array(dep_id_input_list),
                learning_core.dep_length_input: np.array(dep_length_list)
            }
            role_result, role_scores = learning_core.predict_role(argument_forward_dict, one_event_type)
            for one_result_idx, one_result in enumerate(role_result.tolist()):
                sentence_id = argument_info_list[one_result_idx][0]
                argument_info = argument_info_list[one_result_idx][1]
                one_role_result = argument_role_list[one_result]
                # confidence score
                argument_confidence_score = role_scores[one_result_idx, one_result]
                one_argument_result = argument_info + [one_role_result, argument_confidence_score]
                argument_sentence_list[sentence_id]["argument_prediction"].append(one_argument_result)

        for one_sentence in argument_sentence_list:
            argument_evaluation_list.append(one_sentence)

        global_index_offset += batch_size

    # assessment
    assert len(argument_evaluation_list) == len(sequence_evaluation_list)
    return sequence_evaluation_list, argument_evaluation_list


# TODO: in the future, combine them with that one in text data feeder
def search_phrase_tail(token_idx, sentence_sequence, length_offset=0):
    try:
        token_label = sentence_sequence[token_idx + 1]['token_prediction']
    except IndexError:
        return length_offset
    if token_label[0] == "I":
        length_offset = search_phrase_tail(token_idx + 1, sentence_sequence, length_offset=length_offset + 1)
    return length_offset
