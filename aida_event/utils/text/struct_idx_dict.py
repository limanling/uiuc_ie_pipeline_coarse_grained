# This file is to store structural result idx, e.g, dependency parser result.

class StructIdxDict:
    def __init__(self):
        self.struct2idx_dict = dict()
        self.struct2idx_dict[None] = 0
        self.struct2idx_dict['Unknown'] = 1
        self.struct_count = 2

    def insert_struct(self, raw_data_list):
        for one_sentence in raw_data_list:
            one_matrix = one_sentence['depparse']['matrix']
            for one_row in one_matrix:
                for one_entry in one_row:
                    if one_entry is None:
                        continue
                    if one_entry not in self.struct2idx_dict:
                        self.struct2idx_dict[one_entry] = self.struct_count
                        self.struct_count += 1

    def reversed_dict(self):
        return dict(zip(self.struct2idx_dict.values(), self.struct2idx_dict.keys()))

    def struct2idx(self, struct):
        if struct not in self.struct2idx_dict:
            return 1
        else:
            return self.struct2idx_dict[struct]

    def idx2struct(self, idx):
        reversed_dict = self.reversed_dict()
        if idx not in reversed_dict:
            return 'Unknown'
        else:
            return reversed_dict[idx]
