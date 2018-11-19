class WordIdxDict():
    def __init__(self):
        self.word2idx_dict = dict()
        self.word2idx_dict['P*A*D*D*I*N*G'] = 0
        self.word2idx_dict['U*N*K*N*O*W*N'] = 1
        # self.word2idx_dict['S*T*A*R*T*S*E*N*T*E*N*C*E'] = 2
        # self.word2idx_dict['E*N*D*S*E*N*T*E*N*C*E'] = 3
        self.word_count = 2

    def insert_words(self, raw_data_list, dict_key):
        '''
        :param raw_data_list: a two layer list of dict of surface word, labels and other tags.
        :param dict_key: key for the sequence labeling result
        :return:
        '''
        for one_sentence in raw_data_list:
            for one_token in one_sentence['sequence']:
                token_surface = one_token[dict_key].lower()
                if token_surface not in self.word2idx_dict:
                    self.word2idx_dict[token_surface] = self.word_count
                    self.word_count += 1

    def reversed_dict(self):
        return dict(zip(self.word2idx_dict.values(), self.word2idx_dict.keys()))

    def word2idx(self, word):
        if word.lower() not in self.word2idx_dict:
            return 1
        else:
            return self.word2idx_dict[word.lower()]

    def idx2word(self, idx):
        reversed_dict = self.reversed_dict()
        if idx not in reversed_dict:
            return 'U*N*K*N*O*W*N'
        else:
            return reversed_dict[idx]

    def oov_token_prob(self, raw_data_list, dict_key):
        token_count = 0
        oov_count = 0
        for one_sentence in raw_data_list:
            for one_token in one_sentence['sequence']:
                token_surface = one_token[dict_key]
                if token_surface not in self.word2idx_dict:
                    oov_count += 1
                token_count += 1
        return oov_count/token_count

    def oov_sentence_prob(self, raw_data_list, dict_key):
        oov_count = 0
        sentence_count = len(raw_data_list)
        count_flag = 1
        for one_sentence in raw_data_list:
            if count_flag == 0:
                count_flag = 1
                continue
            for one_token in one_sentence['sequence']:
                token_surface = one_token[dict_key]
                if token_surface not in self.word2idx_dict:
                    oov_count += 1
                    count_flag = 0
                    break
        return oov_count/sentence_count
