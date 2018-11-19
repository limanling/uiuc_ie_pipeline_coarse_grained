import os


class BRATAnnotation:
    def __init__(self, file_id, brat_annotation_folder):
        self.file_id = file_id
        self.file_path = os.path.join(brat_annotation_folder, "%s.rsd.ann" % self.file_id)
        self.annotation_dict = self.__read_annotation()

    def __read_annotation(self):
        annotation_dict = dict()
        annotation_dict["sequence_label"] = dict()
        annotation_dict["structure_label"] = dict()

        if os.path.exists(self.file_path) is False:
            print("No annotation file (expected: %s) available for this file" % self.file_path)
            return annotation_dict

        print("Yes, we have annotation for this file")
        for one_line in open(self.file_path):
            one_line = one_line.strip()
            line_info = one_line.split("\t")
            if 'T' in line_info[0]:
                # label start_char end_char
                label_info = line_info[1]
                label_info_list = label_info.split()
                token_type = label_info_list[0]
                start_char = int(label_info_list[1])
                end_char = int(label_info_list[2].split(';')[0])
                annotation_dict["sequence_label"][line_info[0]] = dict()
                annotation_dict["sequence_label"][line_info[0]]["token_type"] = token_type
                annotation_dict["sequence_label"][line_info[0]]["start_char"] = start_char
                annotation_dict["sequence_label"][line_info[0]]["end_char"] = end_char
                annotation_dict["sequence_label"][line_info[0]]["original_text"] = line_info[2]
            if 'E' in line_info[0]:
                label_info = line_info[1]
                label_info_list = label_info.split()
                event_type = label_info_list[0].split(":")[0]
                event_trigger_id = label_info_list[0].split(":")[1]
                argument_list = list()
                for one_argument in label_info_list[1:]:
                    argument_list.append(one_argument.split(":"))
                annotation_dict["structure_label"][line_info[0]] = dict()
                annotation_dict["structure_label"][line_info[0]]["event_type"] = event_type
                annotation_dict["structure_label"][line_info[0]]["event_trigger_id"] = event_trigger_id
                annotation_dict["structure_label"][line_info[0]]["argument_list"] = argument_list
        return annotation_dict