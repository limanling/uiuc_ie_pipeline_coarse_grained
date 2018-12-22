# This version aims to extract triggers

from utils.common.io import read_dict_from_json_file, read_list_from_file, dict_of_event_argument
from utils.common.processing import find_dep_path
from utils.mlframework.discriminator import Discriminator

import tensorflow as tf
import tensorflow.contrib.layers as layers
import numpy as np


class LearningCore:
    def __init__(self,
                 tensorflow_session=None,
                 gpu_device=0,
                 limit_batch_size=128,
                 token_vocab_size=8000,
                 pos_vocab_size=50,
                 char_vocab_size=50,
                 dep_vocab_size=50,
                 token_embedding_dim=100,
                 pos_embedding_dim=20,
                 dep_embeeding_dim=50,
                 char_embedding_dim=20,
                 pretrained_embedding_dim=200,
                 hidden_layer_dim=128,
                 token_lstm_memory=128,
                 char_lstm_memory=16,
                 keep_prob_value=1.0,
                 config_path="config/xmie.json"):

        if tensorflow_session is None:
            if gpu_device >= 0:
                print("Now we are working with GPU")
                session_config = tf.ConfigProto(device_count={'GPU': 1})
                session_config.gpu_options.visible_device_list = str(gpu_device)
                session_config.gpu_options.allow_growth = True
                self.sess = tf.Session(config=session_config)
            else:
                print("Now we are working with CPU")
                session_config = tf.ConfigProto(device_count={'GPU': 0})
                self.sess = tf.Session(config=session_config)
        else:
            self.sess = tensorflow_session

        # Basic parameters
        self.__config = read_dict_from_json_file(config_path)
        self.limit_batch_size = limit_batch_size
        self.token_vocab_size = token_vocab_size
        self.pos_vocab_size = pos_vocab_size
        self.char_vocab_size = char_vocab_size
        self.dep_vocab_size = dep_vocab_size
        self.token_embedding_dim = token_embedding_dim
        self.pos_embedding_dim = pos_embedding_dim
        self.dep_embedding_dim = dep_embeeding_dim
        self.char_embedding_dim = char_embedding_dim
        self.pretrained_embedding_dim = pretrained_embedding_dim
        self.hidden_layer_dim = hidden_layer_dim
        self.token_lstm_memory = token_lstm_memory
        self.char_lstm_memory = char_lstm_memory

        self.label_num = len(read_list_from_file(self.__config['tagger']['category_list_path']))
        assert self.label_num == 95

        self.keep_prob_value = keep_prob_value

        # preparation for the type
        self.argument_role_dict = dict_of_event_argument(
            read_list_from_file(self.__config['tagger']['argument_dict_path']))
        self.event_type_list = list()
        for one_key in self.argument_role_dict:
            self.event_type_list.append(one_key)
        self.event_type_list.sort()
        self.gan = dict()

        # Start of the neural network graph
        # for sequence labeling
        self.sgd_lr = tf.placeholder(dtype=tf.float32, name='sgd_lr')

        # token id to token_id_embedding
        self.token_id_input = tf.placeholder(shape=(None, None), dtype=tf.int32, name='token_id_input')
        token_id_embedding_dict = tf.Variable(tf.random_normal([self.token_vocab_size, self.token_embedding_dim],
                                                               0, 0.001), dtype=tf.float32,
                                              name='token_id_embedding_dict')
        token_id_embedding = tf.nn.embedding_lookup(token_id_embedding_dict, self.token_id_input,
                                                    name='token_id_embedding')

        # pos id to pos_id_embedding
        self.pos_id_input = tf.placeholder(shape=(None, None), dtype=tf.int32, name='pos_id_input')
        pos_id_embedding_dict = tf.Variable(tf.random_normal([self.pos_vocab_size, self.pos_embedding_dim], 0,
                                                             0.001), dtype=tf.float32, name='pos_id_embedding_dict')
        pos_id_embedding = tf.nn.embedding_lookup(pos_id_embedding_dict, self.pos_id_input, name='pos_id_embedding')

        # pretrained embedding
        self.pretrained_embedding_input = tf.placeholder(shape=(None, None, self.pretrained_embedding_dim),
                                                         dtype=tf.float32,
                                                         name='pretrained_embedding_input')


        # character id to character_embedding
        self.char_id_input = tf.placeholder(shape=(None, None, None), dtype=tf.int32, name='char_id_input')
        self.word_length_input = tf.placeholder(shape=(None, None), dtype=tf.int32, name='word_length_input')
        reshaped_char_id_input = tf.reshape(self.char_id_input, [-1, tf.shape(self.char_id_input)[-1]])
        char_id_embedding_dict = tf.Variable(tf.random_normal([self.char_vocab_size, self.char_embedding_dim], 0,
                                                              0.001), dtype=tf.float32,
                                             name='char_id_embedding_dict')
        char_embeddings = tf.nn.embedding_lookup(char_id_embedding_dict, reshaped_char_id_input)
        word_lengths = tf.reshape(self.word_length_input, shape=[-1])

        # sentence length input
        char_cell_fw = tf.nn.rnn_cell.LSTMCell(self.char_lstm_memory)
        char_cell_bw = tf.nn.rnn_cell.LSTMCell(self.char_lstm_memory)

        _, ((_, char_output_fw), (_, char_output_bw)) = tf.nn.bidirectional_dynamic_rnn(char_cell_fw,
                                                                                        char_cell_bw,
                                                                                        char_embeddings,
                                                                                        sequence_length=word_lengths,
                                                                                        dtype=tf.float32,
                                                                                        scope='character_embedding')
        char_output = tf.concat([char_output_fw, char_output_bw], axis=-1)

        char_id_embedding = tf.reshape(char_output, [tf.shape(self.char_id_input)[0],
                                                     tf.shape(self.char_id_input)[1],
                                                     2 * self.char_lstm_memory])

        input_embedded = tf.concat([token_id_embedding, pos_id_embedding, self.pretrained_embedding_input,
                                    char_id_embedding], axis=2, name='input_embedded')

        # sentence length input
        self.sequence_length_input = tf.placeholder(dtype=tf.int32, name='sequence_length_input')

        sequence_cell_fw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        sequence_cell_bw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)

        (sequence_output_fw, sequence_output_bw), _ = tf.nn.bidirectional_dynamic_rnn(sequence_cell_fw,
                                                                    sequence_cell_bw,
                                                                    input_embedded,
                                                                    sequence_length=self.sequence_length_input,
                                                                    dtype=tf.float32,
                                                                    scope='sequence_labeling')
        self.context_rep = tf.concat([sequence_output_fw, sequence_output_bw], axis=-1, name='bi_lstm_output')

        self.sequence_scores = layers.fully_connected(self.context_rep, self.label_num)

        # Codes for training: sequence labeling
        self.sequence_label_index_input = tf.placeholder(tf.int32, shape=[None, None],
                                                         name="sequence_label_index_input")
        self.log_likelihood, transition_params = tf.contrib.crf.crf_log_likelihood(self.sequence_scores,
                                                                                   self.sequence_label_index_input,
                                                                                   self.sequence_length_input)
        self.sequence_labeling_loss = tf.reduce_mean(-self.log_likelihood)

        sequence_optimizer = tf.train.MomentumOptimizer(learning_rate=self.sgd_lr, momentum=0.95)
        # sequence_optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
        self.sequence_train = sequence_optimizer.minimize(self.sequence_labeling_loss)

        # Codes for testing: sequence labeling
        self.viterbi_sequence, self.viterbi_score = tf.contrib.crf.crf_decode(self.sequence_scores,
                                                                              transition_params,
                                                                              self.sequence_length_input)

        # Graph for argument role labeling
        # Obtain the trigger and argument information
        self.trigger_embedding = tf.placeholder(shape=(None, self.token_lstm_memory*2), dtype=tf.float32,
                                                name='trigger_embedding')
        self.argument_embedding = tf.placeholder(shape=(None, self.token_lstm_memory*2), dtype=tf.float32,
                                                 name='argument_embedding')
        # argument_entity_type information
        self.argument_entity_type = tf.placeholder(shape=(None, 7), dtype=tf.float32, name='argument_entity_type')

        # context_embeddings
        # left
        self.left_context_embedding = tf.placeholder(shape=(None, None, self.token_lstm_memory*2), dtype=tf.float32,
                                                     name='left_context_embedding')
        self.left_context_length = tf.placeholder(dtype=tf.int32, name='left_context_length')
        left_cell_fw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        left_cell_bw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        _, ((_, left_output_fw), (_, left_output_bw)) = tf.nn.bidirectional_dynamic_rnn(left_cell_fw,
                                                                                        left_cell_bw,
                                                                                        self.left_context_embedding,
                                                                                        sequence_length=self.left_context_length,
                                                                                        dtype=tf.float32,
                                                                                        scope='left_embedding')
        left_embedding = tf.concat([left_output_fw, left_output_bw], axis=-1)

        # middle
        self.middle_context_embedding = tf.placeholder(shape=(None, None, self.token_lstm_memory * 2), dtype=tf.float32,
                                                       name='middle_context_embedding')
        self.middle_context_length = tf.placeholder(dtype=tf.int32, name='middle_context_length')
        middle_cell_fw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        middle_cell_bw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        _, ((_, middle_output_fw), (_, middle_output_bw)) = tf.nn.bidirectional_dynamic_rnn(middle_cell_fw,
                                                                                            middle_cell_bw,
                                                                                            self.middle_context_embedding,
                                                                                            sequence_length=self.middle_context_length,
                                                                                            dtype=tf.float32,
                                                                                            scope='middle_embedding')
        middle_embedding = tf.concat([middle_output_fw, middle_output_bw], axis=-1)

        # right
        self.right_context_embedding = tf.placeholder(shape=(None, None, self.token_lstm_memory * 2), dtype=tf.float32,
                                                      name='right_context_embedding')
        self.right_context_length = tf.placeholder(dtype=tf.int32, name='right_context_length')
        right_cell_fw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        right_cell_bw = tf.nn.rnn_cell.LSTMCell(self.token_lstm_memory)
        _, ((_, right_output_fw), (_, right_output_bw)) = tf.nn.bidirectional_dynamic_rnn(right_cell_fw,
                                                                                          right_cell_bw,
                                                                                          self.right_context_embedding,
                                                                                          sequence_length=self.right_context_length,
                                                                                          dtype=tf.float32,
                                                                                          scope='right_embedding')
        right_embedding = tf.concat([right_output_fw, right_output_bw], axis=-1)

        # dep id to dep_id_embedding (for argument role labeling)
        self.dep_id_input = tf.placeholder(shape=(None, None), dtype=tf.int32, name='dep_id_input')
        dep_id_embedding_dict = tf.Variable(tf.random_normal([self.dep_vocab_size, self.dep_embedding_dim], 0,
                                                             0.001), dtype=tf.float32, name='dep_id_embedding_dict')
        dep_id_embedding = tf.nn.embedding_lookup(dep_id_embedding_dict, self.dep_id_input, name='dep_id_embedding')
        self.dep_length_input = tf.placeholder(dtype=tf.int32, name='dep_length_input')
        dep_cell_fw = tf.nn.rnn_cell.LSTMCell(self.char_lstm_memory)
        dep_cell_bw = tf.nn.rnn_cell.LSTMCell(self.char_lstm_memory)
        _, ((_, dep_output_fw), (_, dep_output_bw)) = tf.nn.bidirectional_dynamic_rnn(dep_cell_fw,
                                                                                      dep_cell_bw,
                                                                                      dep_id_embedding,
                                                                                      sequence_length=self.dep_length_input,
                                                                                      dtype=tf.float32,
                                                                                      scope='dep_embedding')
        dep_embedding = tf.concat([dep_output_fw, dep_output_bw], axis=-1)

        self.event_embedding = tf.concat([self.trigger_embedding,
                                          self.argument_embedding,
                                          self.argument_entity_type,
                                          left_embedding,
                                          middle_embedding,
                                          right_embedding,
                                          dep_embedding],
                                         axis=-1)
        # It's a 1319-dim vector
        event_embedding_fc = layers.fully_connected(self.event_embedding, self.token_lstm_memory * 2)

        self.argument_table_dict = dict()
        self.argument_chosen_action_dict = dict()
        argument_table_reshape_dict = dict()
        argument_agent_action_for_gather_dict = dict()
        argument_table_selected_dict = dict()
        argument_weight_dict = dict()
        self.argument_loss_dict = dict()
        argument_trainer_dict = dict()
        self.argument_update_model_dict = dict()

        self.argument_agent_action = tf.placeholder(dtype=tf.int32, name='agent_argument')
        self.argument_reward = tf.placeholder(dtype=tf.float32, name='agent_argument_reward')
        for one_event_type in self.event_type_list:
            print("Generating network for %s" % one_event_type)
            argument_role_list = self.argument_role_dict[one_event_type]
            self.argument_table_dict[one_event_type] = layers.fully_connected(event_embedding_fc,
                                                                         len(argument_role_list),
                                                                         activation_fn=tf.nn.softmax)
            self.argument_chosen_action_dict[one_event_type] = tf.argmax(self.argument_table_dict[one_event_type], axis=1)
            self.gan[one_event_type] = Discriminator(state_dim=1319,
                                                     action_count=self.label_num,
                                                     tf_session=self.sess,
                                                     scope_name=one_event_type)
            argument_table_reshape_dict[one_event_type] = tf.reshape(self.argument_table_dict[one_event_type], [-1])
            argument_agent_action_for_gather_dict[one_event_type] = tf.range(
                tf.shape(self.argument_table_dict[one_event_type])[0]) * tf.shape(self.argument_table_dict[one_event_type])[
                                                                        1] + self.argument_agent_action
            argument_table_selected_dict[one_event_type] = tf.gather(argument_table_reshape_dict[one_event_type],
                                                                     argument_agent_action_for_gather_dict[
                                                                         one_event_type])
            argument_weight_dict[one_event_type] = tf.log(tf.clip_by_value(argument_table_selected_dict[one_event_type],
                                                                           1e-5, 1)) * self.argument_reward
            self.argument_loss_dict[one_event_type] = tf.reduce_mean(-argument_weight_dict[one_event_type])
            argument_trainer_dict[one_event_type] = tf.train.MomentumOptimizer(learning_rate=self.sgd_lr, momentum=0.95)
            # argument_trainer_dict[one_event_type] = tf.train.AdamOptimizer(learning_rate=0.001)
            self.argument_update_model_dict[one_event_type] = argument_trainer_dict[one_event_type].minimize(
                self.argument_loss_dict[one_event_type])

        # Initialize the graph
        self.sess.run(tf.global_variables_initializer())


        # Saver
        self.saver = tf.train.Saver(max_to_keep=0)

        # Finalizer
        self.sess.graph.finalize()



    def __loss_function(self):
        difference = tf.square(self.q_updated - self.q_current)
        difference = tf.reduce_sum(difference, 2)
        mask = tf.sign(self.token_id_input)
        mask = tf.cast(mask, dtype=tf.float32)
        difference = difference * mask
        difference = tf.reduce_sum(difference, 1)
        difference = difference / tf.reduce_sum(mask, 1)
        return tf.reduce_mean(difference)

    def __reward_function(self, action, observation, gan_network):
        gan_output = self.gan[gan_network].get_rewards(agent_s=observation, agent_a=action)
        return 20 * (gan_output - 0.5)

    def __start_end(self, split_size, input_batch_size):
        result_list = list()
        start_count = 0
        while True:
            if start_count + split_size < input_batch_size:
                result_list.append([start_count, start_count+split_size])
                start_count += split_size
            else:
                result_list.append([start_count, input_batch_size])
                return result_list


    def save(self, ckpt_path):
        self.saver.save(self.sess,
                        ckpt_path)

    def load(self, ckpt_path):
        self.saver.restore(self.sess,
                           ckpt_path)

    def fit_trigger(self, input_dict, sgd_lr):
        backward_dict = {self.sgd_lr: sgd_lr,
                         self.token_id_input: input_dict["token_id"],
                         self.pos_id_input: input_dict["pos_id"],
                         self.char_id_input: input_dict["char_id"],
                         self.word_length_input: input_dict["word_length"],
                         self.sequence_length_input: input_dict["sequence_length"],
                         self.pretrained_embedding_input: input_dict["embedding"],
                         self.sequence_label_index_input: input_dict['label_index']}
        self.sess.run(self.sequence_train, feed_dict=backward_dict)

    def fit_argument(self, input_dict, sgd_lr, epsilon_greedy=0.1):
        context_dict = {self.token_id_input: input_dict['token_id'],
                        self.pos_id_input: input_dict['pos_id'],
                        self.char_id_input: input_dict["char_id"],
                        self.word_length_input: input_dict["word_length"],
                        self.sequence_length_input: input_dict["sequence_length"],
                        self.pretrained_embedding_input: input_dict["embedding"]}
        context_representation = self.sess.run(self.context_rep, feed_dict=context_dict)

        argument_queue_dict = dict()

        for one_event_type in self.event_type_list:
            argument_queue_dict[one_event_type] = list()
        for batch_idx, one_sentence in enumerate(input_dict["argument_label"]):
            for one_argument_info in one_sentence:
                current_event_type = one_argument_info[3]
                argument_queue_dict[current_event_type].append((batch_idx, one_argument_info))


        for one_event_type in argument_queue_dict:
            if len(argument_queue_dict[one_event_type]) == 0:
                continue
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
                one_entity_index = input_dict['entity_label_index'][one_batch_idx, one_argument_info[1]]
                if one_entity_index >= 0:
                    one_argument_entity_type_vector[one_entity_index] = 1
                argument_entity_type_input_list.append(one_argument_entity_type_vector)

                if one_trigger_index < one_argument_index:
                    left_index = one_trigger_index
                    right_index = one_argument_index
                else:
                    right_index= one_trigger_index
                    left_index = one_argument_index
                one_left_embedding = np.zeros([320, 2*self.token_lstm_memory], dtype=np.float32)
                one_left_length = left_index + 1
                one_left_embedding[0:one_left_length, :] = context_representation[one_batch_idx, 0:left_index + 1, :]
                left_context_embedding_input.append(one_left_embedding)
                left_context_length_input.append(one_left_length)

                one_middle_embedding = np.zeros([320, 2 * self.token_lstm_memory], dtype=np.float32)
                one_middle_length = right_index - left_index + 1
                one_middle_embedding[0:one_middle_length, :] = context_representation[one_batch_idx,
                                                               left_index:right_index+1, :]
                middle_context_embedding_input.append(one_middle_embedding)
                middle_context_length_input.append(one_middle_length)

                one_right_embedding = np.zeros([320, 2 * self.token_lstm_memory], dtype=np.float32)
                one_right_length = input_dict["sequence_length"][one_batch_idx] - right_index + 1
                one_right_embedding[0:one_right_length, :] = context_representation[one_batch_idx,
                                                             right_index:input_dict["sequence_length"][one_batch_idx]+1,
                                                             :]
                right_context_embedding_input.append(one_right_embedding)
                right_context_lenght_input.append(one_right_length)

                dep_list = list()
                try:
                    dep_list = find_dep_path(one_trigger_index,  one_argument_index, input_dict['dep_id'][one_batch_idx])
                    if len(dep_list) == 0:
                        dep_list.append(1)
                except:
                    dep_list.append(1)
                one_dep_id_input = np.zeros([320], dtype=np.int32)
                one_dep_id_input[0:len(dep_list)] = np.array(dep_list, dtype=np.int32)
                dep_id_input_list.append(one_dep_id_input)
                dep_length_list.append(len(dep_list))

            if len(trigger_embedding_list) == 0:
                continue
            assert len(trigger_embedding_list) == len(argument_queue_dict[one_event_type])

            split_list = self.__start_end(self.limit_batch_size, len(argument_queue_dict[one_event_type]))
            for one_split in split_list:
                split_start = one_split[0]
                split_end = one_split[1]
                argument_forward_dict = {self.trigger_embedding: np.array(trigger_embedding_list[split_start:split_end]),
                                         self.argument_embedding: np.array(argument_embedding_list[split_start:split_end]),
                                         self.argument_entity_type: np.array(argument_entity_type_input_list[split_start:split_end]),
                                         self.left_context_embedding: np.array(left_context_embedding_input[split_start:split_end]),
                                         self.left_context_length: np.array(left_context_length_input[split_start:split_end]),
                                         self.middle_context_embedding: np.array(middle_context_embedding_input[split_start:split_end]),
                                         self.middle_context_length: np.array(middle_context_length_input[split_start:split_end]),
                                         self.right_context_embedding: np.array(right_context_embedding_input[split_start:split_end]),
                                         self.right_context_length: np.array(right_context_lenght_input[split_start:split_end]),
                                         self.dep_id_input: np.array(dep_id_input_list[split_start:split_end]),
                                         self.dep_length_input: np.array(dep_length_list[split_start:split_end])
                                         }
                event_embedding,\
                argument_chosen_action = self.sess.run([self.event_embedding,
                                                        self.argument_chosen_action_dict[one_event_type]],
                                                       feed_dict=argument_forward_dict)

                agent_action_list = list()
                expert_action_list = list()
                argument_reward_list = list()
                expert_reward_list = list()

                for one_idx, one_argument_tuple in enumerate(argument_queue_dict[one_event_type][split_start:split_end]):
                    if np.random.uniform() < epsilon_greedy:
                        current_argument_action = np.random.choice(len(self.argument_role_dict[one_event_type]))
                    else:
                        current_argument_action = argument_chosen_action[one_idx]
                    agent_action_list.append(current_argument_action)
                    argument_ground_truth = self.argument_role_dict[one_event_type].index(one_argument_tuple[1][4])
                    assert argument_ground_truth >= 0
                    expert_action_list.append(argument_ground_truth)

                self.gan[one_event_type].train(expert_s=event_embedding,
                                               expert_a=np.array(expert_action_list),
                                               agent_s=event_embedding,
                                               agent_a=np.array(agent_action_list))
                temp_agent_reward = self.__reward_function(np.array(agent_action_list),
                                                           np.array(event_embedding),
                                                           one_event_type)
                temp_expert_reward = self.__reward_function(np.array(expert_action_list),
                                                            np.array(event_embedding),
                                                            one_event_type)

                for one_idx, one_argument_action in enumerate(agent_action_list):
                    one_expert_action = expert_action_list[one_idx]
                    expert_reward_list.append(np.maximum(temp_expert_reward[one_idx], 1))
                    if one_argument_action == one_expert_action:
                        argument_reward_list.append(np.maximum(temp_agent_reward[one_idx], 1))
                    else:
                        argument_reward_list.append(np.minimum(temp_agent_reward[one_idx], -1))

                agent_backward_dict = {self.sgd_lr: sgd_lr,
                                       self.trigger_embedding: np.array(trigger_embedding_list[split_start:split_end]),
                                       self.argument_embedding: np.array(
                                           argument_embedding_list[split_start:split_end]),
                                       self.argument_entity_type: np.array(
                                           argument_entity_type_input_list[split_start:split_end]),
                                       self.left_context_embedding: np.array(
                                           left_context_embedding_input[split_start:split_end]),
                                       self.left_context_length: np.array(
                                           left_context_length_input[split_start:split_end]),
                                       self.middle_context_embedding: np.array(
                                           middle_context_embedding_input[split_start:split_end]),
                                       self.middle_context_length: np.array(
                                           middle_context_length_input[split_start:split_end]),
                                       self.right_context_embedding: np.array(
                                           right_context_embedding_input[split_start:split_end]),
                                       self.right_context_length: np.array(
                                           right_context_lenght_input[split_start:split_end]),
                                       self.dep_id_input: np.array(dep_id_input_list[split_start:split_end]),
                                       self.dep_length_input: np.array(dep_length_list[split_start:split_end]),
                                       self.argument_reward: np.array(argument_reward_list),
                                       self.argument_agent_action: np.array(agent_action_list)}
                self.sess.run(self.argument_update_model_dict[one_event_type], agent_backward_dict)
                expert_backward_dict = {self.sgd_lr: sgd_lr,
                                        self.trigger_embedding: np.array(trigger_embedding_list[split_start:split_end]),
                                        self.argument_embedding: np.array(
                                            argument_embedding_list[split_start:split_end]),
                                        self.argument_entity_type: np.array(
                                            argument_entity_type_input_list[split_start:split_end]),
                                        self.left_context_embedding: np.array(
                                            left_context_embedding_input[split_start:split_end]),
                                        self.left_context_length: np.array(
                                            left_context_length_input[split_start:split_end]),
                                        self.middle_context_embedding: np.array(
                                            middle_context_embedding_input[split_start:split_end]),
                                        self.middle_context_length: np.array(
                                            middle_context_length_input[split_start:split_end]),
                                        self.right_context_embedding: np.array(
                                            right_context_embedding_input[split_start:split_end]),
                                        self.right_context_length: np.array(
                                            right_context_lenght_input[split_start:split_end]),
                                        self.dep_id_input: np.array(dep_id_input_list[split_start:split_end]),
                                        self.dep_length_input: np.array(dep_length_list[split_start:split_end]),
                                        self.argument_reward: np.array(expert_reward_list),
                                        self.argument_agent_action: np.array(expert_action_list)}
                self.sess.run(self.argument_update_model_dict[one_event_type], expert_backward_dict)

    def predict_sequence(self, input_dict):
        forward_dict = {self.token_id_input: input_dict["token_id"],
                        self.pos_id_input: input_dict["pos_id"],
                        self.char_id_input: input_dict["char_id"],
                        self.word_length_input: input_dict["word_length"],
                        self.pretrained_embedding_input: input_dict["embedding"],
                        self.sequence_length_input: input_dict["sequence_length"]}
        viterbi_sequence, sequence_scores, context_representation = self.sess.run([self.viterbi_sequence,
                                                                                  self.sequence_scores,
                                                                                  self.context_rep],
                                                                 feed_dict=forward_dict)
        return viterbi_sequence, sequence_scores, context_representation

    def predict_role(self, input_dict, event_type):
        predicted_result, predicted_scores = self.sess.run([self.argument_chosen_action_dict[event_type],
                                                           self.argument_table_dict[event_type]],
                                                           feed_dict=input_dict)
        return predicted_result, predicted_scores
