class CharIdxDict():
    def __init__(self):
        self.char2idx_dict = dict()
        self.char2idx_dict['P*A*D*D*I*N*G'] = 0
        self.char2idx_dict['U*N*K*N*O*W*N'] = 1
        self.char_count = 2

    def insert_char(self, char_list):
        '''
        :param raw_data_list: a two layer list of dict of surface word, labels and other tags.
        :param dict_key: key for the sequence labeling result
        :return:
        '''
        for one_char in char_list:
            if one_char not in self.char2idx_dict:
                self.char2idx_dict[one_char] = self.char_count
                self.char_count += 1

    def reversed_dict(self):
        return dict(zip(self.char2idx_dict.values(), self.char2idx_dict.keys()))

    def char2idx(self, char):
        if char not in self.char2idx_dict:
            return 1
        else:
            return self.char2idx_dict[char]

    def idx2char(self, idx):
        reversed_dict = self.reversed_dict()
        if idx not in reversed_dict:
            return 'U*N*K*N*O*W*N'
        else:
            return reversed_dict[idx]