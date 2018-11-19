import numpy as np

from utils.common.io import read_list_from_file, read_dict_from_json_file
from utils.common.processing import category_detector
from utils.text.word_idx_dict import WordIdxDict
from utils.text.struct_idx_dict import StructIdxDict
from utils.text.char_idx_dict import CharIdxDict


class TextDataFeeder():
    def __init__(self,
                 raw_data_list,
                 max_length=128,
                 max_word_length=64,
                 token_idx_dict=None,
                 pos_idx_dict=None,
                 dep_idx_dict=None,
                 char_idx_dict=None,
                 word2vec_model=None,
                 word2vec_dim=200,
                 config_file_path="config/xmie.json",
                 oov_token_prob=0,
                 oov_sentence_prob=0):
        self.raw_data_list = raw_data_list
        self.max_length = max_length
        self.max_word_length = max_word_length
        if token_idx_dict is None:
            self.token_idx_dict = self.__generate_token_dict()
        else:
            self.token_idx_dict = token_idx_dict
        if pos_idx_dict is None:
            self.pos_idx_dict = self.__generate_pos_dict()
        else:
            self.pos_idx_dict = pos_idx_dict
        if dep_idx_dict is None:
            self.dep_idx_dict = self.__generate_dep_dict()
        else:
            self.dep_idx_dict = dep_idx_dict
        if char_idx_dict is None:
            self.char_idx_dict = self.__generate_char_dict()
        else:
            self.char_idx_dict = char_idx_dict
        self.config_file_path = config_file_path
        self.config = read_dict_from_json_file(self.config_file_path)
        self.oov_token_prob = oov_token_prob
        self.oov_sentence_prob = oov_sentence_prob

        # raw_token_input
        self.raw_token_input = self.__raw_token_input()

        # token_id_input
        self.token_id_input = self.__token_id_input()

        # pos_tagger_id_input
        self.pos_id_input = self.__pos_id_input()

        # dep_input
        self.dep_id_input = self.__dep_id_input()

        # char_id_input
        self.char_id_input = self.__char_id_input()

        # word_length_input
        self.word_length_input = self.__word_length_input()

        # label_input
        self.label_input = self.__label_input()

        # label_index_input
        self.label_index_input = self.__label_index_input()

        # entity_label_index_input
        self.entity_label_index_input = self.__entity_label_index_input()

        # argument_label_input
        self.argument_label_input = self.__argument_label_input()

        # embedding_input
        if word2vec_model is None:
            self.embedding_input = None
        else:
            self.embedding_input = self.__embedding_input(word2vec_model, word2vec_dim)

        # sequence_length_input
        self.sequence_length_input = self.__sequence_length_input()

        self.data_index = np.arange(0, len(self.raw_data_list))
        self._instance_count = 0
        self.epoch = 0

        self.raw_token_input_feed = None
        self.token_id_input_feed = None
        self.pos_id_input_feed = None
        self.char_id_input_feed = None
        self.dep_id_input_feed = None
        self.word_length_input_feed = None
        self.label_input_feed = None
        self.label_index_input_feed = None
        self.entity_label_index_input_feed = None
        self.argument_label_input_feed = None
        self.embedding_input_feed = None
        self.sequence_length_input_feed = None
        self.__prepare_feed()

    def __generate_token_dict(self):
        word_idx_dict = WordIdxDict()
        word_idx_dict.insert_words(self.raw_data_list, 'word')
        return word_idx_dict

    def __generate_pos_dict(self):
        word_idx_dict = WordIdxDict()
        word_idx_dict.insert_words(self.raw_data_list, 'pos')
        return word_idx_dict

    def __generate_char_dict(self):
        char_idx_dict = CharIdxDict()
        char_list = list()
        for one_sentence in self.raw_data_list:
            one_sentence_sequence = one_sentence["sequence"]
            for one_word in one_sentence_sequence:
                one_original_text = one_word['original_text']
                for one_char in one_original_text:
                    char_list.append(one_char)
        char_list = list(set(char_list))
        char_idx_dict.insert_char(char_list)
        return char_idx_dict

    def __raw_token_input(self):
        raw_token_array = np.empty([len(self.raw_data_list), self.max_length], dtype=np.string_)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                try:
                    raw_token_array[sent_id, token_id] = one_token['word']
                except UnicodeError:
                    raw_token_array[sent_id, token_id] = one_token['word'].encode('utf-8')
        return raw_token_array

    def __token_id_input(self):
        token_id_input = np.zeros([len(self.raw_data_list), self.max_length], dtype=np.int32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                token_surface = one_token['word'].lower()
                if token_surface not in self.token_idx_dict.word2idx_dict:
                    token_id_input[sent_id, token_id] = 1
                else:
                    token_id_input[sent_id, token_id] = self.token_idx_dict.word2idx_dict[token_surface]
        return token_id_input

    def __pos_id_input(self):
        pos_id_input = np.zeros([len(self.raw_data_list), self.max_length], dtype=np.int32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                pos_tag = one_token['pos'].lower()
                if pos_tag not in self.pos_idx_dict.word2idx_dict:
                    pos_id_input[sent_id, token_id] = 1
                else:
                    pos_id_input[sent_id, token_id] = self.pos_idx_dict.word2idx_dict[pos_tag]
        return pos_id_input

    def __dep_id_input(self):
        dep_id_input = list()
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            temp_dict = dict()
            temp_dict['graph'] = one_sentence['depparse']['graph']
            temp_dict['matrix'] = np.zeros_like(one_sentence['depparse']['matrix'], dtype=np.int32)
            matrix_shape = one_sentence['depparse']['matrix'].shape
            for x in range(matrix_shape[0]):
                for y in range(matrix_shape[1]):
                    temp_dict['matrix'][x, y] = self.dep_idx_dict.struct2idx(one_sentence['depparse']['matrix'][x, y])
            dep_id_input.append(temp_dict)
        return dep_id_input

    def __char_id_input(self):
        char_idx_input = np.zeros([len(self.raw_data_list), self.max_length, self.max_word_length], dtype=np.int32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                one_orignal_text = one_token['original_text']
                for char_id, one_char in enumerate(one_orignal_text):
                    if char_id >= self.max_word_length:
                        continue
                    if one_char not in self.char_idx_dict.char2idx_dict:
                        char_idx_input[sent_id, token_id, char_id] = 1
                    else:
                        char_idx_input[sent_id, token_id, char_id] = self.char_idx_dict.char2idx_dict[one_char]
        return char_idx_input

    def __word_length_input(self):
        word_length_input = np.zeros([len(self.raw_data_list), self.max_length], dtype=np.int32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                one_original_text = one_token['original_text']
                word_length_input[sent_id, token_id] = len(one_original_text)
        return word_length_input

    def __embedding_input(self, word2vec_model, dim):
        embedding_input = np.zeros([len(self.raw_data_list), self.max_length, dim], dtype=np.float32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                token_surface = one_token['word'].lower()
                if token_surface in word2vec_model.wv.vocab:
                    embedding_input[sent_id, token_id, :] = word2vec_model[token_surface]
        return embedding_input

    def __label_input(self):
        category_list = read_list_from_file(self.config['tagger']['category_list_path'])
        label_input = np.zeros([len(self.raw_data_list), self.max_length, len(category_list)], dtype=np.int32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                token_label = one_token['label']
                if token_label in category_list:
                    label_input[sent_id, token_id, category_list.index(token_label)] = 1
        return label_input

    def __label_index_input(self):
        label_index_input = np.argmax(self.label_input, axis=2)
        return label_index_input

    def __entity_label_index_input(self):
        category_list = read_list_from_file(self.config['tagger']['entity_label_path'])
        entity_label_input = np.zeros([len(self.raw_data_list), self.max_length], dtype=np.int32) - 1

        for sent_id, one_sentence in enumerate(self.raw_data_list):
            for token_id, one_token in enumerate(one_sentence['sequence']):
                token_label = one_token['label'].replace('B-', '')
                if token_label in category_list:
                    entity_label_input[sent_id, token_id] = category_list.index(token_label)
        return entity_label_input

    def __search_phrase_tail(self, token_idx, sentence_sequence, length_offset=0):
        try:
            token_label = sentence_sequence[token_idx+1]['label']
        except IndexError:
            return length_offset
        if token_label[0] == "I":
            length_offset = self.__search_phrase_tail(token_idx+1, sentence_sequence, length_offset=length_offset+1)
        return length_offset

    def __argument_label_input(self):
        argument_label_input = list()
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            one_sentence_argument_list = list()
            one_sentence_not_none_list = list()
            one_sentence_trigger_list = list()
            one_sentence_entity_list = list()
            for word_id, one_word in enumerate(one_sentence['sequence']):
                if 'arguments' not in one_word:
                    continue
                for one_argument_info_dict in one_word['arguments']:
                    # a list of [trigger_idx, trigger_length_offset, argument_idx, argument_length_offset, event_type, argument_role]
                    argument_info_list = list()
                    trigger_idx = word_id
                    argument_info_list.append(trigger_idx) #trigger_idx
                    argument_offset = one_argument_info_dict['offset']
                    argument_idx = word_id-argument_offset
                    argument_length_offset = self.__search_phrase_tail(argument_idx, one_sentence['sequence'])
                    argument_info_list.append(argument_idx) #argument_idx
                    argument_info_list.append(argument_length_offset)
                    event_type = category_detector(one_word['label'])
                    argument_info_list.append(event_type) #event_type
                    one_sentence_not_none_list.append(argument_info_list.copy())
                    argument_info_list.append(one_argument_info_dict['role']) #role
                    one_sentence_argument_list.append(argument_info_list)
            # adding None relation
            for word_id, one_word in enumerate(one_sentence['sequence']):
                if "B-" in one_word['label']:
                    if '.' in one_word['label']:
                        one_sentence_trigger_list.append([word_id, category_detector(one_word['label'])])
                if self.entity_label_index_input[sent_id][word_id] >= 0:
                    one_sentence_entity_list.append(word_id)
            for one_trigger in one_sentence_trigger_list:
                for one_entity in one_sentence_entity_list:
                    argument_length_offset = self.__search_phrase_tail(one_entity, one_sentence['sequence'])
                    argument_temp_list = [one_trigger[0], one_entity, argument_length_offset, one_trigger[1]]
                    if argument_temp_list not in one_sentence_not_none_list:
                        # if the argument_temp is not in the "not_none" list, it means it is none
                        argument_temp_list.append('Other')
                        one_sentence_argument_list.append(argument_temp_list)
            argument_label_input.append(one_sentence_argument_list)
        return argument_label_input

    def __argument_list_shuffle(self):
        temp_list = list()
        for one_number in self.data_index.tolist():
            temp_list.append(self.argument_label_input_feed[one_number])
        self.argument_label_input_feed = temp_list

    def __sequence_length_input(self):
        sequence_length_input = np.zeros(len(self.raw_data_list), dtype=np.int32)
        for sent_id, one_sentence in enumerate(self.raw_data_list):
            sequence_length_input[sent_id] = len(one_sentence['sequence'])
        return sequence_length_input

    def __sequence_length(self, one_sentence):
        return np.sum(np.sign(one_sentence), dtype=np.int32)

    def __prepare_feed(self):
        # prepare raw_token_input_feed
        self.raw_token_input_feed = self.raw_token_input.copy()
        self.raw_token_input_feed = self.raw_token_input_feed[self.data_index]

        # prepare token id input
        self.token_id_input_feed = self.token_id_input.copy()
        self.token_id_input_feed = self.token_id_input_feed[self.data_index]
        for one_sentence_id in range(self.token_id_input_feed.shape[0]):
            if np.random.rand(1) >= self.oov_sentence_prob:
                continue
            for one_token_id in range(int(self.__sequence_length(self.token_id_input_feed[one_sentence_id]))):
                if np.random.rand(1) < self.oov_token_prob:
                    self.token_id_input_feed[one_sentence_id, one_token_id] = 1

        # prepare pos id input
        self.pos_id_input_feed = self.pos_id_input.copy()
        self.pos_id_input_feed = self.pos_id_input_feed[self.data_index]

        # prepare dep input
        self.dep_id_input_feed_temp = self.dep_id_input.copy()
        self.dep_id_input_feed = list()
        for one_data_index in self.data_index.tolist():
            self.dep_id_input_feed.append(self.dep_id_input_feed_temp[one_data_index])

        # prepare char id input
        self.char_id_input_feed = self.char_id_input.copy()
        self.char_id_input_feed = self.char_id_input_feed[self.data_index]
        for one_sentence_id in range(self.char_id_input_feed.shape[0]):
            for one_token_id in range(int(self.__sequence_length(self.token_id_input_feed[one_sentence_id]))):
                if np.random.rand(1) >= self.oov_sentence_prob:
                    continue
                for one_char_id in range(int(self.__sequence_length(self.char_id_input_feed[one_sentence_id][one_token_id]))):
                    if np.random.rand(1) < self.oov_token_prob:
                        self.char_id_input_feed[one_sentence_id, one_token_id, one_char_id] = 1

        # prepare word length input
        self.word_length_input_feed = self.word_length_input.copy()
        self.word_length_input_feed = self.word_length_input_feed[self.data_index]

        # prepare label input
        self.label_input_feed = self.label_input.copy()
        self.label_input_feed = self.label_input_feed[self.data_index]

        # prepare label index input
        self.label_index_input_feed = self.label_index_input.copy()
        self.label_index_input_feed = self.label_index_input_feed[self.data_index]

        # prepare entity label index input
        self.entity_label_index_input_feed = self.entity_label_index_input.copy()
        self.entity_label_index_input_feed = self.entity_label_index_input_feed[self.data_index]

        # prepare argument label input
        self.argument_label_input_feed = self.argument_label_input.copy()
        self.__argument_list_shuffle()

        # prepare embedding input
        if self.embedding_input is not None:
            self.embedding_input_feed = self.embedding_input.copy()
            self.embedding_input_feed = self.embedding_input_feed[self.data_index]

        # prepare sequence length in put
        self.sequence_length_input_feed = self.sequence_length_input.copy()
        self.sequence_length_input_feed = self.sequence_length_input_feed[self.data_index]

        # final step: shuffle the data_index
        np.random.shuffle(self.data_index)

    def next_batch(self, batch_size=32):
        if self._instance_count+batch_size < len(self.raw_data_list):
            raw_token_input = self.raw_token_input_feed[self._instance_count:self._instance_count+batch_size]
            token_id_input = self.token_id_input_feed[self._instance_count:self._instance_count+batch_size]
            pos_id_input = self.pos_id_input_feed[self._instance_count:self._instance_count+batch_size]
            dep_id_input = self.dep_id_input_feed[self._instance_count:self._instance_count + batch_size]
            char_id_input = self.char_id_input_feed[self._instance_count:self._instance_count+batch_size]
            word_length_input = self.word_length_input_feed[self._instance_count:self._instance_count+batch_size]
            label_input = self.label_input_feed[self._instance_count:self._instance_count+batch_size]
            label_index_input = self.label_index_input_feed[self._instance_count:self._instance_count+batch_size]
            entity_label_index_input = self.entity_label_index_input_feed[self._instance_count:self._instance_count+batch_size]
            argument_label_input = self.argument_label_input_feed[self._instance_count:self._instance_count+batch_size]
            if self.embedding_input_feed is None:
                embedding_input = None
            else:
                embedding_input = self.embedding_input_feed[self._instance_count:self._instance_count+batch_size]
            sequence_length_input = self.sequence_length_input_feed[self._instance_count:self._instance_count+batch_size]
            self._instance_count += batch_size
        else:
            raw_token_input = self.raw_token_input_feed[self._instance_count:len(self.raw_data_list)]
            token_id_input = self.token_id_input_feed[self._instance_count:len(self.raw_data_list)]
            pos_id_input = self.pos_id_input_feed[self._instance_count:len(self.raw_data_list)]
            dep_id_input = self.dep_id_input_feed[self._instance_count:len(self.raw_data_list)]
            char_id_input = self.char_id_input_feed[self._instance_count:len(self.raw_data_list)]
            word_length_input = self.word_length_input_feed[self._instance_count:len(self.raw_data_list)]
            label_input = self.label_input_feed[self._instance_count:len(self.raw_data_list)]
            entity_label_index_input = self.entity_label_index_input_feed[self._instance_count:len(self.raw_data_list)]
            label_index_input = self.label_index_input_feed[self._instance_count:len(self.raw_data_list)]
            argument_label_input = self.argument_label_input_feed[self._instance_count:len(self.raw_data_list)]
            if self.embedding_input_feed is None:
                embedding_input = None
            else:
                embedding_input = self.embedding_input_feed[self._instance_count:len(self.raw_data_list)]
            sequence_length_input = self.sequence_length_input_feed[self._instance_count:len(self.raw_data_list)]
            self._instance_count = 0
            self.epoch += 1
            self.__prepare_feed()
        return {"raw_token_input": raw_token_input,
                "token_id": token_id_input,
                "pos_id": pos_id_input,
                'dep_id': dep_id_input,
                "char_id": char_id_input,
                "word_length": word_length_input,
                "label": label_input,
                "label_index": label_index_input,
                "entity_label_index": entity_label_index_input,
                "argument_label": argument_label_input,
                "embedding": embedding_input,
                "sequence_length": sequence_length_input}